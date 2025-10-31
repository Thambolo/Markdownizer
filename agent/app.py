"""ConnectOnion agent setup for Markdownizer."""

from __future__ import annotations

import sys
from pathlib import Path

from connectonion import Agent

from config import settings
from src.tools.fetcher import FetcherTool
from src.tools.extractor import ExtractorTool
from src.tools.comparator import ComparatorTool
from src.tools.playwright_probe import PlaywrightProbeTool
from src.tools.normalizer import NormalizerTool


# Initialize tool instances globally (ConnectOnion best practice)
fetcher = FetcherTool()
extractor = ExtractorTool()
comparator = ComparatorTool()
playwright_probe = PlaywrightProbeTool()
normalizer = NormalizerTool()


def create_agent() -> Agent:
    """
    Create the Markdownizer agent with intelligent model fallback.
    
    Strategy:
    1. Try ConnectOnion's free tier first (co/gpt-4o-mini) - 100k free tokens
    2. If that fails, fall back to user's OpenAI API key
    3. If both fail, raise clear error
    
    Returns:
        Agent: Initialized ConnectOnion agent
    
    Raises:
        RuntimeError: If both ConnectOnion and OpenAI initialization fail
    """
    # Use global tool instances
    tools = [
        fetcher,              # Auto-discovers: fetch_url, close
        extractor,            # Auto-discovers: extract_with_trafilatura, convert_to_markdown, clean_markdown, fix_fragmented_code_blocks
        comparator,           # Auto-discovers: compute_signals, semantic_overlap, score_candidate, compare_and_decide
        playwright_probe,     # Auto-discovers: detect_blockers, close
        normalizer,           # Auto-discovers: strip_tracking, normalize_links, redact_tokens
    ]
    
    agent_instance = None
    error_messages = []
    
    # Try ConnectOnion free tier first
    if settings.use_connectonion_free:
        try:
            print(f"🔄 Trying ConnectOnion free tier ({settings.connectonion_model})...")
            agent_instance = Agent(
                name="markdownizer",
                system_prompt=Path("src/prompts/agent.md"),
                tools=tools,
                model=settings.connectonion_model,  # co/gpt-4o-mini
                max_iterations=20,
            )
            print(f"✅ Using ConnectOnion free tier: {settings.connectonion_model}")
            return agent_instance
        except Exception as e:
            error_msg = f"ConnectOnion free tier failed: {str(e)}"
            error_messages.append(error_msg)
            print(f"⚠️  {error_msg}")
    
    # Fallback to user's OpenAI API key
    if settings.openai_api_key:
        try:
            print(f"🔄 Falling back to OpenAI ({settings.openai_model})...")
            agent_instance = Agent(
                name="markdownizer",
                system_prompt=Path("src/prompts/agent.md"),
                tools=tools,
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_iterations=20,
            )
            print(f"✅ Using OpenAI: {settings.openai_model}")
            return agent_instance
        except Exception as e:
            error_msg = f"OpenAI fallback failed: {str(e)}"
            error_messages.append(error_msg)
            print(f"❌ {error_msg}")
    else:
        error_messages.append("No OpenAI API key provided")
    
    # Both failed
    raise RuntimeError(
        "Failed to initialize agent with any available model:\n" +
        "\n".join(f"  - {msg}" for msg in error_messages) +
        "\n\nPlease either:\n" +
        "  1. Ensure ConnectOnion package is installed correctly, or\n" +
        "  2. Set OPENAI_API_KEY in your .env file"
    )


# Create the agent (with fallback logic)
agent = create_agent()


def cleanup_resources():
    """Clean up agent resources."""
    try:
        if fetcher and hasattr(fetcher, 'close'):
            fetcher.close()
        if playwright_probe and hasattr(playwright_probe, 'close'):
            playwright_probe.close()
        return "Resources cleaned up"
    except Exception as e:
        return f"Cleanup warning: {str(e)}"


# Cleanup on exit
import atexit
atexit.register(cleanup_resources)


if __name__ == "__main__":
    # Test the agent
    print("🤖 Markdownizer Agent initialized")
    print(f"   Model: {settings.openai_model}")
    print(f"   Tools: {len(agent.tools)} registered")
    print(f"   Max iterations: {agent.max_iterations}")
    print("\nAvailable tools:")
    for tool_name in agent.list_tools():
        print(f"   - {tool_name}")
