"""URL and link normalization tool."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse


class NormalizerTool:
    """Tool for normalizing URLs and links in Markdown."""

    def __init__(self):
        """Initialize the normalizer."""
        # Tracking parameters to remove
        self._tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "msclkid",
            "ref",
            "source",
        }

    def strip_tracking(self, url: str) -> str:
        """
        Remove tracking parameters from URL.

        Args:
            url: URL with potential tracking params

        Returns:
            Cleaned URL
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Remove tracking parameters
            cleaned_params = {
                k: v for k, v in query_params.items() if k not in self._tracking_params
            }

            # Rebuild query string
            new_query = urlencode(cleaned_params, doseq=True)

            # Rebuild URL
            cleaned = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )

            return cleaned

        except Exception:
            # If parsing fails, return original
            return url

    def normalize_links(self, markdown: str, base_url: str) -> str:
        """
        Normalize all links in Markdown to absolute URLs.

        Args:
            markdown: Markdown content with links
            base_url: Base URL for resolving relative links

        Returns:
            Markdown with normalized links
        """
        # Pattern to match Markdown links: [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        def normalize_link(match):
            text = match.group(1)
            url = match.group(2)

            # Skip anchors and mailto links
            if url.startswith("#") or url.startswith("mailto:"):
                return match.group(0)

            # Make absolute
            try:
                absolute_url = urljoin(base_url, url)
                # Strip tracking
                cleaned_url = self.strip_tracking(absolute_url)
                return f"[{text}]({cleaned_url})"
            except Exception:
                # If normalization fails, keep original
                return match.group(0)

        return re.sub(link_pattern, normalize_link, markdown)

    def redact_tokens(self, url: str) -> str:
        """
        Redact sensitive tokens from URLs for logging.

        Args:
            url: URL that might contain tokens

        Returns:
            URL with tokens redacted
        """
        # Patterns that might indicate tokens
        token_patterns = [
            (r"(token=)[^&]+", r"\1[REDACTED]"),
            (r"(api_key=)[^&]+", r"\1[REDACTED]"),
            (r"(key=)[^&]+", r"\1[REDACTED]"),
            (r"(secret=)[^&]+", r"\1[REDACTED]"),
            (r"(auth=)[^&]+", r"\1[REDACTED]"),
        ]

        redacted = url
        for pattern, replacement in token_patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)

        return redacted
