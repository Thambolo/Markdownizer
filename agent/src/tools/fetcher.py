"""HTTP fetcher tool using httpx."""

from __future__ import annotations

import httpx
from typing import Optional

from config import settings


class FetcherTool:
    """Tool for fetching web pages with httpx."""

    def __init__(self):
        """Initialize the fetcher with a reusable client."""
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=settings.http_timeout,
                follow_redirects=True,
                headers={"User-Agent": settings.http_user_agent},
            )
        return self._client

    def fetch_url(self, url: str) -> dict[str, str | int | bool]:
        """
        Fetch a URL and return HTML content with metadata.

        Args:
            url: The URL to fetch

        Returns:
            Dictionary with html, status_code, content_type, final_url, and redirect info
        """
        client = self._get_client()

        try:
            response = client.get(url)
            
            # Check if we were redirected to a different page
            original_url = httpx.URL(url)
            final_url = response.url
            
            # Normalize for comparison (ignore benign differences)
            def normalize_url(u: httpx.URL) -> tuple[str, str]:
                """Return (normalized_domain, normalized_path) for comparison."""
                # Remove www. prefix
                domain = u.host.lower().removeprefix('www.') if u.host else ''
                # Normalize trailing slash
                path = u.path.rstrip('/') if u.path != '/' else '/'
                return (domain, path)
            
            orig_normalized = normalize_url(original_url)
            final_normalized = normalize_url(final_url)
            
            # Redirect is significant if domain OR path changed
            was_redirected = orig_normalized != final_normalized
            
            return {
                "html": response.text,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "final_url": str(response.url),
                "original_url": url,
                "was_redirected": was_redirected,
                "success": True,
                "error": None,
            }
        except httpx.TimeoutException:
            return {
                "html": "",
                "status_code": 0,
                "content_type": "",
                "final_url": url,
                "success": False,
                "error": "Request timeout",
            }
        except httpx.HTTPError as e:
            return {
                "html": "",
                "status_code": 0,
                "content_type": "",
                "final_url": url,
                "success": False,
                "error": f"HTTP error: {str(e)}",
            }
        except Exception as e:
            return {
                "html": "",
                "status_code": 0,
                "content_type": "",
                "final_url": url,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    def close(self) -> str:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
        return "HTTP client closed"
