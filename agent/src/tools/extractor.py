"""Content extraction and Markdown conversion tool."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md


class ExtractorTool:
    """Tool for extracting content and converting to Markdown."""

    def __init__(self):
        """Initialize the extractor."""
        self._cache: dict[str, str] = {}

    def extract_with_trafilatura(
        self, html: str, url: str
    ) -> dict[str, str | int | None]:
        """
        Extract clean text from HTML using trafilatura.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Use trafilatura to extract main content
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                output_format="txt",
            )

            # Also get HTML version for Markdown conversion
            html_content = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                output_format="html",
            )

            if text and html_content:
                return {
                    "text": text,
                    "html": html_content,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "success": True,
                    "error": None,
                }
            else:
                return {
                    "text": "",
                    "html": "",
                    "char_count": 0,
                    "word_count": 0,
                    "success": False,
                    "error": "Trafilatura returned no content",
                }

        except Exception as e:
            return {
                "text": "",
                "html": "",
                "char_count": 0,
                "word_count": 0,
                "success": False,
                "error": f"Extraction error: {str(e)}",
            }

    def convert_to_markdown(
        self, html: str, title: str, url: str, include_metadata: bool = True
    ) -> str:
        """
        Convert HTML to Markdown using markdownify.

        Args:
            html: Clean HTML content
            title: Page title
            url: Source URL
            include_metadata: Whether to include metadata header

        Returns:
            Markdown formatted string
        """
        try:
            # Clean HTML first
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for tag in soup(
                ["script", "style", "nav", "footer", "header", "aside", "iframe"]
            ):
                tag.decompose()

            # Convert to Markdown
            # Note: markdownify will convert <pre><code> to ``` fenced blocks
            # but won't preserve language classes (that's OK - we just want the code content)
            markdown = md(
                str(soup),
                heading_style="ATX",
                bullets="-",
                strong_em_symbol="*",
                code_block_style="fenced",
            )

            # Add metadata header if requested
            if include_metadata:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                header = f"""# {title}

**Source**: {url}  
**Captured**: {timestamp}

---

"""
                markdown = header + markdown.strip()

            return markdown

        except Exception as e:
            # Fallback: return plain text in code block
            return f"""# {title}

**Source**: {url}  
**Error**: Failed to convert to Markdown: {str(e)}

```
{html[:1000]}...
```
"""

    def clean_markdown(self, markdown: str) -> str:
        """
        Clean up excessive whitespace in Markdown.

        Args:
            markdown: Raw markdown string

        Returns:
            Cleaned markdown string
        """
        lines = markdown.split("\n")
        cleaned = []
        prev_blank = False

        for line in lines:
            is_blank = not line.strip()

            # Skip consecutive blank lines
            if is_blank and prev_blank:
                continue

            cleaned.append(line)
            prev_blank = is_blank

        return "\n".join(cleaned)
