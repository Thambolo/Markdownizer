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


def test_extract_language_from_classes_stackoverflow(extractor):
    """Test language extraction from StackOverflow classes."""
    from bs4 import BeautifulSoup
    
    # StackOverflow uses s-lang-js pattern
    html = '<code class="s-lang-js">const x = 1;</code>'
    soup = BeautifulSoup(html, 'html.parser')
    code = soup.find('code')
    
    lang = extractor._extract_language_from_classes(code)
    assert lang == 'javascript'


def test_extract_language_from_classes_common_patterns(extractor):
    """Test language extraction from common class patterns."""
    from bs4 import BeautifulSoup
    
    test_cases = [
        ('<code class="lang-python">code</code>', 'python'),
        ('<code class="language-javascript">code</code>', 'javascript'),
        ('<code class="hljs-typescript">code</code>', 'typescript'),
        ('<code class="prism-bash">code</code>', 'bash'),
        ('<pre class="lang-go">code</pre>', 'go'),
    ]
    
    for html, expected_lang in test_cases:
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find(['code', 'pre'])
        lang = extractor._extract_language_from_classes(elem)
        assert lang == expected_lang, f"Failed for {html}"


def test_normalize_language_name(extractor):
    """Test language name normalization."""
    assert extractor._normalize_language_name('js') == 'javascript'
    assert extractor._normalize_language_name('py') == 'python'
    assert extractor._normalize_language_name('ts') == 'typescript'
    assert extractor._normalize_language_name('sh') == 'bash'
    assert extractor._normalize_language_name('yml') == 'yaml'
    assert extractor._normalize_language_name('c++') == 'cpp'
    assert extractor._normalize_language_name('c#') == 'csharp'
    assert extractor._normalize_language_name('golang') == 'go'
    assert extractor._normalize_language_name('rs') == 'rust'
    assert extractor._normalize_language_name('rb') == 'ruby'


def test_detect_language_from_code_python(extractor):
    """Test Python language detection from code content."""
    python_code = """
    import os
    from pathlib import Path
    
    def hello():
        print("Hello")
    """
    
    lang = extractor._detect_language_from_code(python_code)
    assert lang == 'python'


def test_detect_language_from_code_javascript(extractor):
    """Test JavaScript language detection from code content."""
    js_code = """
    const x = 10;
    function test() {
        console.log("test");
    }
    """
    
    lang = extractor._detect_language_from_code(js_code)
    assert lang == 'javascript'


def test_detect_language_from_code_bash(extractor):
    """Test Bash language detection from code content."""
    bash_code = """
    $ npm install
    $ git commit -m "test"
    export PATH=/usr/bin
    """
    
    lang = extractor._detect_language_from_code(bash_code)
    assert lang == 'bash'


def test_detect_language_from_code_html(extractor):
    """Test HTML language detection from code content."""
    html_code = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body><div>Content</div></body>
    </html>
    """
    
    lang = extractor._detect_language_from_code(html_code)
    assert lang == 'html'


def test_detect_language_from_code_go(extractor):
    """Test Go language detection from code content."""
    go_code = """
    package main
    
    func main() {
        fmt.Println("Hello")
    }
    """
    
    lang = extractor._detect_language_from_code(go_code)
    assert lang == 'go'


def test_detect_language_from_code_rust(extractor):
    """Test Rust language detection from code content."""
    rust_code = """
    fn main() {
        let mut x = 5;
        println!("{}", x);
    }
    """
    
    lang = extractor._detect_language_from_code(rust_code)
    assert lang == 'rust'


def test_fix_fragmented_code_blocks_with_line_numbers(extractor):
    """Test fixing fragmented inline code with line numbers."""
    markdown = """
Some text before

`1from connectonion import Agent
2
3# Comment
4agent = Agent("test")`

Some text after
"""
    
    fixed = extractor.fix_fragmented_code_blocks(markdown)
    
    # Should convert to fenced code block
    assert '```python' in fixed or '```' in fixed
    assert 'from connectonion import Agent' in fixed
    assert '# Comment' in fixed
    assert 'agent = Agent("test")' in fixed
    # Line numbers should be stripped
    assert '1from' not in fixed
    assert '2\n' not in fixed or '```python\n\n' in fixed  # Allow blank line in code


def test_fix_fragmented_code_blocks_single_line(extractor):
    """Test fixing single-line code blocks with line numbers."""
    markdown = '`1const x = 10;`'
    
    fixed = extractor.fix_fragmented_code_blocks(markdown)
    
    # Should convert to fenced block
    assert '```' in fixed
    assert 'const x = 10;' in fixed
    assert '1const' not in fixed


def test_fix_fragmented_code_blocks_javascript(extractor):
    """Test JavaScript code block detection and language tagging."""
    markdown = """
`1function test() {
2  console.log("hello");
3}`
"""
    
    fixed = extractor.fix_fragmented_code_blocks(markdown)
    
    assert '```javascript' in fixed
    assert 'function test()' in fixed
    assert 'console.log("hello")' in fixed


def test_convert_to_markdown_preserves_language_from_classes(extractor):
    """Test that language info from HTML classes is preserved in Markdown."""
    html = """
    <pre><code class="lang-python">
def hello():
    print("world")
    </code></pre>
    """
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    # Should have fenced code block with language
    assert '```python' in markdown
    assert 'def hello():' in markdown
    assert 'print("world")' in markdown


def test_convert_to_markdown_stackoverflow_code_blocks(extractor):
    """Test conversion of StackOverflow-style code blocks."""
    html = """
    <pre><code class="s-lang-js">
const x = 10;
function test() {
    return x;
}
    </code></pre>
    """
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    assert '```javascript' in markdown
    assert 'const x = 10;' in markdown
    assert 'function test()' in markdown


def test_convert_to_markdown_multiple_code_blocks(extractor):
    """Test conversion with multiple code blocks with different languages."""
    html = """
    <div>
        <pre><code class="lang-python">print("hello")</code></pre>
        <p>Some text</p>
        <pre><code class="lang-javascript">console.log("world");</code></pre>
    </div>
    """
    
    markdown = extractor.convert_to_markdown(html, "Test", "https://example.com", False)
    
    assert '```python' in markdown
    assert 'print("hello")' in markdown
    assert '```javascript' in markdown
    assert 'console.log("world")' in markdown


def test_fix_fragmented_code_blocks_no_line_numbers(extractor):
    """Test that code without line numbers is left unchanged."""
    markdown = """
Some normal text with `inline code` that should stay.

```python
# Already a proper code block
def test():
    pass
```
"""
    
    fixed = extractor.fix_fragmented_code_blocks(markdown)
    
    # Should not break existing code
    assert '`inline code`' in fixed
    assert '```python' in fixed
    assert 'def test():' in fixed
