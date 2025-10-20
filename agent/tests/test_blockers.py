"""Tests for PlaywrightProbeTool (with mocking)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools.playwright_probe import PlaywrightProbeTool


@pytest.fixture
def probe():
    """Create a PlaywrightProbeTool instance."""
    return PlaywrightProbeTool()


def test_detect_blockers_login_required(probe):
    """Test detection of login-required pages."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=401)
        mock_page.content.return_value = '<form><input type="password"></form>'
        mock_page.inner_text.return_value = "Please sign in to continue"
        mock_page.query_selector_all.side_effect = [
            [Mock()],  # login forms
            [Mock()],  # password inputs
            [],  # overlays
            [],  # modals
            []   # iframes
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/private")
        
        assert flags["login_required"] is True


def test_detect_blockers_paywall(probe):
    """Test detection of paywalls."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_overlay = Mock()
        mock_overlay.inner_text.return_value = "Subscribe now for premium access"
        
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=200)
        mock_page.content.return_value = '<div class="paywall-overlay">Subscribe</div>'
        mock_page.inner_text.return_value = "Subscribe now for premium access"
        mock_page.query_selector_all.side_effect = [
            [],  # login forms
            [],  # password inputs
            [mock_overlay],  # overlays with paywall text
            [],  # modals
            []   # iframes
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/premium")
        
        assert flags["paywall"] is True


def test_detect_blockers_captcha(probe):
    """Test detection of CAPTCHA challenges."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=200)
        mock_page.content.return_value = '<div class="g-recaptcha"></div>'
        mock_page.inner_text.return_value = "Complete the captcha"
        mock_page.query_selector_all.side_effect = [
            [],  # login forms
            [],  # password inputs
            [],  # overlays
            [],  # modals
            []   # iframes
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/captcha")
        
        assert flags["captcha"] is True


def test_detect_blockers_thin_content(probe):
    """Test detection of content-too-thin pages."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=200)
        mock_page.content.return_value = '<body>Minimal</body>'
        mock_page.inner_text.return_value = "Hi"  # Very short content
        mock_page.query_selector_all.side_effect = [
            [],  # login forms
            [],  # password inputs
            [],  # overlays
            [],  # modals
            []   # iframes (no iframes, just thin content)
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/empty")
        
        assert flags["content_too_thin"] is True


def test_detect_blockers_cross_origin_iframe(probe):
    """Test detection of iframe-heavy pages with thin content."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_iframe = Mock()
        
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=200)
        mock_page.content.return_value = '<body><iframe src="https://other.com"></iframe></body>'
        mock_page.inner_text.return_value = "Loading"  # Thin content
        mock_page.query_selector_all.side_effect = [
            [],  # login forms
            [],  # password inputs
            [],  # overlays
            [],  # modals
            [mock_iframe, mock_iframe]  # Multiple iframes
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/iframe-heavy")
        
        assert flags["cross_origin_iframe"] is True


def test_detect_blockers_clean_page(probe):
    """Test that clean accessible pages have no flags."""
    with patch('src.tools.playwright_probe.sync_playwright') as mock_playwright:
        # Setup mocks
        mock_page = Mock()
        mock_page.goto.return_value = Mock(status=200)
        mock_page.content.return_value = '<article>' + '<p>Good content</p>' * 50 + '</article>'
        mock_page.inner_text.return_value = "Good accessible content. " * 100
        mock_page.query_selector_all.side_effect = [
            [],  # login forms
            [],  # password inputs
            [],  # overlays
            [],  # modals
            []   # iframes
        ]
        
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        probe._playwright = mock_pw
        probe._browser = mock_browser
        
        # Test
        flags = probe.detect_blockers("https://example.com/good-article")
        
        assert flags["login_required"] is False
        assert flags["paywall"] is False
        assert flags["captcha"] is False
        assert flags["content_too_thin"] is False


def test_close_cleanup(probe):
    """Test that close() properly cleans up resources."""
    probe._browser = Mock()
    probe._playwright = Mock()
    
    result = probe.close()
    
    assert "closed" in result.lower()
    assert probe._browser is None
    assert probe._playwright is None
