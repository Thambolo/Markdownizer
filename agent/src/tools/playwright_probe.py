"""Playwright-based blocker detection tool."""

from __future__ import annotations

from typing import Optional

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError

from config import settings


class PlaywrightProbeTool:
    """Tool for detecting access blockers using headless Playwright."""

    def __init__(self):
        """Initialize the probe."""
        self._playwright = None
        self._browser: Optional[Browser] = None

    def _get_browser(self) -> Browser:
        """Get or create headless browser."""
        if self._browser is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=settings.playwright_headless,
                args=["--disable-gpu", "--no-sandbox"],
            )
        return self._browser

    def detect_blockers(self, url: str) -> dict[str, bool | str]:
        """
        Probe a URL for access blockers (headless only, no auth).

        This is NOT for scraping - only for detecting blockers.
        30-second hard timeout.

        Args:
            url: The URL to probe

        Returns:
            Dictionary with blocker flags and metadata
        """
        flags = {
            "login_required": False,
            "paywall": False,
            "captcha": False,
            "cross_origin_iframe": False,
            "content_too_thin": False,
            "csp_blocked": False,
            "error": None,
        }

        browser = None
        page = None

        try:
            browser = self._get_browser()
            page = browser.new_page()

            # Set timeout from config (convert seconds to milliseconds)
            page.set_default_timeout(settings.playwright_timeout * 1000)

            # Navigate to page
            response = page.goto(url, wait_until="networkidle")

            if not response:
                flags["error"] = "No response received"
                return flags

            # Check HTTP status
            status = response.status
            if status == 401 or status == 403:
                flags["login_required"] = True

            # Get page content
            content = page.content()
            text = page.inner_text("body")

            # Detect login/signup patterns
            login_patterns = [
                "sign in",
                "log in",
                "login",
                "password",
                "authenticate",
                "session expired",
            ]
            if any(pattern in content.lower() for pattern in login_patterns):
                # Check if it's a prominent login form
                login_forms = page.query_selector_all('form[action*="login"]')
                password_inputs = page.query_selector_all('input[type="password"]')
                if login_forms or password_inputs:
                    flags["login_required"] = True

            # Detect paywall patterns
            paywall_patterns = [
                "subscribe",
                "subscription",
                "premium",
                "member",
                "free trial",
                "unlock",
                "paywall",
            ]
            overlays = page.query_selector_all('[class*="overlay"]')
            modals = page.query_selector_all('[class*="modal"]')
            if overlays or modals:
                overlay_text = " ".join(
                    [el.inner_text() for el in (overlays + modals) if el]
                )
                if any(pattern in overlay_text.lower() for pattern in paywall_patterns):
                    flags["paywall"] = True

            # Detect captcha
            captcha_patterns = ["captcha", "recaptcha", "hcaptcha", "cf-challenge"]
            if any(pattern in content.lower() for pattern in captcha_patterns):
                flags["captcha"] = True

            # Check for cross-origin iframes with significant content
            iframes = page.query_selector_all("iframe")
            if len(text.strip()) < 200 and len(iframes) > 0:
                # Page is thin and has iframes - might be iframe-heavy content
                flags["cross_origin_iframe"] = True

            # Content too thin check
            if len(text.strip()) < 100 and not flags["login_required"]:
                flags["content_too_thin"] = True

        except TimeoutError:
            flags["error"] = "Page load timeout"
        except Exception as e:
            flags["error"] = f"Probe error: {str(e)}"
        finally:
            if page:
                page.close()

        return flags

    def close(self) -> str:
        """Close browser and cleanup."""
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            return "Playwright browser closed"
        finally:
            self._browser = None
            self._playwright = None
