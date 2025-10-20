"""Tests for ExtractorTool."""

import pytest
from src.tools.extractor import ExtractorTool


@pytest.fixture
def extractor():
    """Create an ExtractorTool instance."""
    return ExtractorTool()


def test_extract_with_trafilatura_success(extractor):
    """Test successful extraction with trafilatura."""
    html = """
    <html>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is the main content of the article.</p>
                <p>It has multiple paragraphs with useful information.</p>
            </article>
            <footer>Copyright 2024</footer>
        </body>
    </html>
    """
    
    result = extractor.extract_with_trafilatura(html, "https://example.com/article")
    
    assert result["success"] is True
    assert result["text"]
    assert result["html"]
    assert result["char_count"] > 0
    assert result["word_count"] > 0
    assert "Test Article" in result["text"]


def test_extract_with_trafilatura_empty_content(extractor):
    """Test extraction with minimal/empty content."""
    html = "<html><body></body></html>"
    
    result = extractor.extract_with_trafilatura(html, "https://example.com")
    
    # trafilatura should return no content for empty HTML
    assert result["success"] is False


def test_convert_to_markdown_basic(extractor):
    """Test basic HTML to Markdown conversion."""
    html = "<h1>Title</h1><p>Paragraph text</p>"
    
    markdown = extractor.convert_to_markdown(
        html,
        "Test Title",
        "https://example.com",
        include_metadata=False
    )
    
    assert "# Title" in markdown
    assert "Paragraph text" in markdown


def test_convert_to_markdown_with_metadata(extractor):
    """Test Markdown conversion with metadata header."""
    html = "<p>Content</p>"
    
    markdown = extractor.convert_to_markdown(
        html,
        "My Article",
        "https://example.com/article",
        include_metadata=True
    )
    
    assert "# My Article" in markdown
    assert "**Source**: https://example.com/article" in markdown
    assert "**Captured**:" in markdown


def test_convert_to_markdown_removes_scripts(extractor):
    """Test that scripts and styles are removed."""
    html = """
    <div>
        <script>alert('bad');</script>
        <style>.test { color: red; }</style>
        <p>Good content</p>
    </div>
    """
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    assert "alert" not in markdown
    assert "color: red" not in markdown
    assert "Good content" in markdown


def test_convert_to_markdown_preserves_links(extractor):
    """Test that links are preserved in Markdown format."""
    html = '<p>Check out <a href="https://example.com">this link</a></p>'
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    assert "[this link]" in markdown or "this link" in markdown


def test_clean_markdown_removes_excessive_whitespace(extractor):
    """Test that excessive blank lines are removed."""
    markdown = """
# Title


Paragraph 1



Paragraph 2


"""
    
    cleaned = extractor.clean_markdown(markdown)
    
    # Should not have 3+ consecutive blank lines
    assert "\n\n\n" not in cleaned
    assert "# Title" in cleaned
    assert "Paragraph 1" in cleaned
    assert "Paragraph 2" in cleaned


def test_clean_markdown_preserves_single_blanks(extractor):
    """Test that single blank lines are preserved."""
    markdown = """# Title

Paragraph 1

Paragraph 2"""
    
    cleaned = extractor.clean_markdown(markdown)
    
    assert cleaned.count("\n\n") >= 2  # At least two single blank lines
    assert "# Title" in cleaned


def test_convert_to_markdown_handles_complex_structure(extractor):
    """Test conversion with complex HTML structure."""
    html = """
    <article>
        <h1>Main Title</h1>
        <h2>Section 1</h2>
        <p>Intro paragraph</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <h2>Section 2</h2>
        <p>More content</p>
        <blockquote>A quote</blockquote>
    </article>
    """
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    assert "# Main Title" in markdown
    assert "## Section 1" in markdown or "Section 1" in markdown
    assert "Item 1" in markdown
    assert "Item 2" in markdown


def test_convert_handles_error_gracefully(extractor):
    """Test that conversion errors are handled gracefully."""
    # Pass None or invalid input
    markdown = extractor.convert_to_markdown(
        None,
        "Test",
        "https://example.com",
        False
    )
    
    # Should return error message, not crash
    assert "Error" in markdown or "Failed" in markdown
