"""FastAPI server for Markdownizer agent service."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from schemas import (
    IngestRequest,
    SuccessResponse,
    ErrorResponse,
    HealthResponse,
)
from app import agent, fetcher, extractor, comparator, playwright_probe, normalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Markdownizer Agent API",
    description="AI-powered web content to Markdown conversion service",
    version="1.0.0",
)

# Add CORS middleware for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Browser extensions need wildcard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
    )


@app.post("/ingest", response_model=Union[SuccessResponse, ErrorResponse])
async def ingest_content(request: IngestRequest):
    """
    Ingest content from browser extension and convert to Markdown.

    This endpoint orchestrates the full pipeline:
    1. Receive extension's captured HTML (Schema.org > Semantic > Readability)
    2. Fetch URL independently
    3. Extract with trafilatura
    4. Optionally probe for blockers
    5. Compare both versions (extension vs agent)
    6. Convert chosen version to Markdown with code block handling
    7. Return result or error
    """
    start_time = datetime.now(timezone.utc)
    url = str(request.url)
    
    # Redact URL for logging
    safe_url = normalizer.redact_tokens(url)
    logger.info(f"Ingest request: {safe_url}")

    try:
        # Step 1: Fetch the URL independently to get RAW HTML
        logger.info(f"Fetching URL with httpx...")
        fetch_result = fetcher.fetch_url(url)

        if not fetch_result["success"]:
            logger.warning(f"Fetch failed: {fetch_result['error']}")
            logger.info("Using extension's captured content as fallback")
            # Use extension's content as fallback
            markdown_final = extractor.convert_to_markdown(
                request.html_extension,
                request.title,
                url,
            )
            markdown_final = extractor.fix_fragmented_code_blocks(markdown_final)
            
            return SuccessResponse(
                chosen="extension",
                title=request.title,
                url=url,
                markdown=markdown_final,
                diagnostics={
                    "score_extension": 1.0,
                    "score_trafilatura": 0.0,
                    "signals": {
                        "extension": {
                            "len": len(request.text_extension),
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                        "trafilatura": {
                            "len": 0,
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                    },
                },
            )
        
        # Check if we were redirected to a different page
        # ANY redirect means agent sees different content than user's browser
        if fetch_result.get("was_redirected"):
            logger.warning(
                f"Redirect detected: {fetch_result['original_url']} → {fetch_result['final_url']}"
            )
            logger.info("Using extension's captured content (agent can't verify redirected page)")
            
            # Convert extension's HTML to Markdown
            markdown_final = extractor.convert_to_markdown(
                request.html_extension,
                request.title,
                url,
            )
            markdown_final = extractor.fix_fragmented_code_blocks(markdown_final)
            
            return SuccessResponse(
                chosen="extension",
                title=request.title,
                url=url,
                markdown=markdown_final,
                diagnostics={
                    "score_extension": 1.0,
                    "score_trafilatura": 0.0,
                    "signals": {
                        "extension": {
                            "len": len(request.text_extension),
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                        "trafilatura": {
                            "len": 0,
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                    },
                    "redirect_detected": True,
                    "original_url": fetch_result['original_url'],
                    "final_url": fetch_result['final_url'],
                },
            )

        # Step 2: Extract with trafilatura
        logger.info("Extracting content with trafilatura...")
        extraction = extractor.extract_with_trafilatura(
            fetch_result["html"],
            url,
        )

        if not extraction["success"]:
            logger.warning(f"Extraction failed: {extraction['error']}")
            logger.info("Using extension's captured content as fallback")
            # Use extension's content
            markdown_final = extractor.convert_to_markdown(
                request.html_extension,
                request.title,
                url,
            )
            markdown_final = extractor.fix_fragmented_code_blocks(markdown_final)
            
            return SuccessResponse(
                chosen="extension",
                title=request.title,
                url=url,
                markdown=markdown_final,
                diagnostics={
                    "score_extension": 1.0,
                    "score_trafilatura": 0.0,
                    "signals": {
                        "extension": {
                            "len": len(request.text_extension),
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                        "trafilatura": {
                            "len": 0,
                            "density": 0.0,
                            "overlap": 0.0,
                        },
                    },
                },
            )

        # Step 3: Check for blockers (proactive detection)
        # Note: Redirects are already handled above, so no need to check here
        blocker_flags = {}
        should_probe = (
            extraction["char_count"] < 200 or  # Thin content
            extraction["char_count"] < 500  # Suspicious short content
        )
        
        if should_probe:
            logger.info(f"Probing for blockers (extraction: {extraction['char_count']} chars)...")
            blocker_flags = playwright_probe.detect_blockers(url)
            
            # If critical blockers detected, use extension's content
            # (User already has the content in their browser, so convert it!)
            blocker_detected = (
                blocker_flags.get("login_required") or
                blocker_flags.get("paywall") or
                blocker_flags.get("captcha")
            )
            
            if blocker_detected:
                blocker_type = (
                    "login wall" if blocker_flags.get("login_required") else
                    "paywall" if blocker_flags.get("paywall") else
                    "CAPTCHA"
                )
                logger.warning(f"{blocker_type} detected, using extension's captured content")
                
                # Convert extension's HTML to Markdown
                markdown_final = extractor.convert_to_markdown(
                    request.html_extension,
                    request.title,
                    url,
                )
                markdown_final = extractor.fix_fragmented_code_blocks(markdown_final)
                
                return SuccessResponse(
                    chosen="extension",
                    title=request.title,
                    url=url,
                    markdown=markdown_final,
                    diagnostics={
                        "score_extension": 1.0,
                        "score_trafilatura": 0.0,
                        "signals": {
                            "extension": {
                                "len": len(request.text_extension),
                                "density": 0.0,
                                "overlap": 0.0,
                            },
                            "trafilatura": {
                                "len": 0,
                                "density": 0.0,
                                "overlap": 0.0,
                            },
                        },
                    },
                )

        # Step 4: Compare both versions
        logger.info("Comparing extension vs agent extraction...")
        comparison = comparator.compare_and_decide(
            extension_text=request.text_extension,
            extension_html=request.html_extension,
            trafilatura_text=extraction["text"],
            trafilatura_html=extraction["html"],
            title=request.title,
            blocker_flags=blocker_flags,
        )
        
        # Choose HTML based on comparison result
        html_with_code = extraction["html"] if comparison["chosen"] == "trafilatura" else request.html_extension
        
        # Step 5: Convert chosen content to Markdown
        markdown = extractor.convert_to_markdown(
            html_with_code,
            request.title,
            url,
        )

        # Step 6: Fix fragmented code blocks (line numbers, broken formatting)
        markdown = extractor.fix_fragmented_code_blocks(markdown)

        # Step 7: Normalize links and clean
        markdown = normalizer.normalize_links(markdown, url)
        markdown = extractor.clean_markdown(markdown)

        # Calculate duration
        chosen = comparison["chosen"]
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Conversion complete: {chosen} chosen "
            f"(extension: {comparison['score_extension']:.3f}, trafilatura: {comparison['score_trafilatura']:.3f}), "
            f"{duration:.2f}s"
        )

        # Step 8: Return success response
        return SuccessResponse(
            chosen=chosen,
            title=request.title,
            url=url,
            markdown=markdown,
            diagnostics={
                "score_extension": comparison["score_extension"],
                "score_trafilatura": comparison["score_trafilatura"],
                "signals": {
                    "extension": comparison["signals_extension"],
                    "trafilatura": comparison["signals_trafilatura"],
                },
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
    )
