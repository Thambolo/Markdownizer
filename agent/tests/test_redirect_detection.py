"""Tests for redirect detection logic."""

import httpx
import pytest


def normalize_url(u: httpx.URL) -> tuple[str, str]:
    """Normalize URL for comparison (extracted from fetcher.py)."""
    domain = u.host.lower().removeprefix('www.') if u.host else ''
    path = u.path.rstrip('/') if u.path != '/' else '/'
    return (domain, path)


class TestURLNormalization:
    """Test URL normalization for redirect detection."""

    def test_identical_urls_not_considered_redirect(self):
        """Exact same URLs should not be considered a redirect."""
        url1 = httpx.URL("https://example.com/article")
        url2 = httpx.URL("https://example.com/article")
        assert normalize_url(url1) == normalize_url(url2)

    def test_http_to_https_not_considered_redirect(self):
        """Scheme changes (http → https) should be normalized."""
        url1 = httpx.URL("http://example.com/article")
        url2 = httpx.URL("https://example.com/article")
        assert normalize_url(url1) == normalize_url(url2)

    def test_www_normalization(self):
        """www subdomain should be normalized away."""
        url1 = httpx.URL("https://www.example.com/article")
        url2 = httpx.URL("https://example.com/article")
        assert normalize_url(url1) == normalize_url(url2)

    def test_trailing_slash_normalization(self):
        """Trailing slashes should be normalized."""
        url1 = httpx.URL("https://example.com/article")
        url2 = httpx.URL("https://example.com/article/")
        assert normalize_url(url1) == normalize_url(url2)

    def test_combined_benign_differences(self):
        """Multiple benign differences should all normalize."""
        url1 = httpx.URL("http://www.example.com/article")
        url2 = httpx.URL("https://example.com/article/")
        assert normalize_url(url1) == normalize_url(url2)

    def test_path_change_detected(self):
        """Different paths should be detected as redirects."""
        url1 = httpx.URL("https://example.com/article")
        url2 = httpx.URL("https://example.com/login")
        assert normalize_url(url1) != normalize_url(url2)

    def test_domain_change_detected(self):
        """Different domains should be detected as redirects."""
        url1 = httpx.URL("https://example.com/article")
        url2 = httpx.URL("https://other.com/article")
        assert normalize_url(url1) != normalize_url(url2)

    def test_subdomain_change_detected(self):
        """Different subdomains (not www) should be detected."""
        url1 = httpx.URL("https://blog.example.com/article")
        url2 = httpx.URL("https://auth.example.com/login")
        assert normalize_url(url1) != normalize_url(url2)

    def test_query_params_ignored_in_normalization(self):
        """Query parameters are not part of our normalization."""
        # Note: Our normalization only checks domain + path
        # Query params are ignored, which is intentional
        url1 = httpx.URL("https://example.com/article?utm_source=twitter")
        url2 = httpx.URL("https://example.com/article")
        # Both normalize to same (domain, path)
        assert normalize_url(url1) == normalize_url(url2)

    def test_root_path_handling(self):
        """Root path should be handled correctly."""
        url1 = httpx.URL("https://example.com/")
        url2 = httpx.URL("https://example.com")
        # Root path normalization
        norm1 = normalize_url(url1)
        norm2 = normalize_url(url2)
        # Both should normalize to '/' for path
        assert norm1[1] == '/' and norm2[1] == '/'


class TestRedirectScenarios:
    """Test real-world redirect scenarios."""

    def test_login_redirect_detected(self):
        """Login redirects should be detected."""
        original = httpx.URL("https://medium.com/@user/protected-post")
        redirected = httpx.URL("https://medium.com/login")
        assert normalize_url(original) != normalize_url(redirected)

    def test_paywall_redirect_detected(self):
        """Paywall redirects should be detected."""
        original = httpx.URL("https://nytimes.com/article")
        redirected = httpx.URL("https://nytimes.com/subscribe")
        assert normalize_url(original) != normalize_url(redirected)

    def test_signup_redirect_detected(self):
        """Signup redirects should be detected."""
        original = httpx.URL("https://site.com/content")
        redirected = httpx.URL("https://site.com/signup")
        assert normalize_url(original) != normalize_url(redirected)

    def test_geo_block_redirect_detected(self):
        """Geo-blocking redirects should be detected."""
        original = httpx.URL("https://site.com/video")
        redirected = httpx.URL("https://site.com/not-available-in-your-region")
        assert normalize_url(original) != normalize_url(redirected)

    def test_international_login_detected(self):
        """International login paths should be detected."""
        original = httpx.URL("https://site.com/articulo")
        redirected = httpx.URL("https://site.com/iniciar-sesion")
        assert normalize_url(original) != normalize_url(redirected)

    def test_subdomain_auth_redirect_detected(self):
        """Subdomain changes for auth should be detected."""
        original = httpx.URL("https://blog.example.com/post")
        redirected = httpx.URL("https://auth.example.com/login")
        assert normalize_url(original) != normalize_url(redirected)

    def test_canonical_url_with_www_not_redirect(self):
        """Canonical URL transformations should not be considered redirects."""
        original = httpx.URL("http://www.example.com/article/")
        canonical = httpx.URL("https://example.com/article")
        assert normalize_url(original) == normalize_url(canonical)
