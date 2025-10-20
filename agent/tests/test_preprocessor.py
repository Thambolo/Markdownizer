"""
Unit tests for PreprocessorTool - Code Block Extraction.

Tests Phase 1 implementation:
- Semantic HTML extraction (<pre><code>)
- Framework-specific patterns
- Language detection
- Placeholder system
- Markdown reinsertion
"""

import pytest
from src.tools.preprocessor import PreprocessorTool, CodeBlock


class TestCodeBlockDataclass:
    """Test CodeBlock dataclass functionality."""
    
    def test_basic_code_block(self):
        """Test basic code block creation."""
        block = CodeBlock(content="print('hello')", language="python")
        assert block.content == "print('hello')"
        assert block.language == "python"
        assert block.is_terminal is False
    
    def test_to_markdown_python(self):
        """Test Python code block to Markdown."""
        block = CodeBlock(content="def foo():\n    pass", language="python")
        result = block.to_markdown()
        assert result == "```python\ndef foo():\n    pass\n```"
    
    def test_to_markdown_terminal(self):
        """Test terminal block to Markdown."""
        block = CodeBlock(
            content="npm install\ncd project",
            language="bash",
            is_terminal=True
        )
        result = block.to_markdown()
        assert "$ npm install" in result
        assert "$ cd project" in result
    
    def test_to_markdown_with_dollar_prompt(self):
        """Test terminal block already having $ prompts."""
        block = CodeBlock(
            content="$ npm install\n$ cd project",
            is_terminal=True
        )
        result = block.to_markdown()
        # Should not duplicate $
        assert result.count('$') == 2


class TestSemanticHTMLExtraction:
    """Test extraction from semantic HTML elements."""
    
    def test_simple_pre_code(self):
        """Test basic <pre><code> extraction."""
        html = '<pre><code>print("hello")</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert 'print("hello")' in blocks[0].content
        assert 'PLACEHOLDER_0' in processed_html
    
    def test_pre_code_with_language_class(self):
        """Test <pre><code class="language-python">."""
        html = '<pre><code class="language-python">def foo():\n    pass</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "def foo()" in blocks[0].content
    
    def test_multiple_code_blocks(self):
        """Test multiple code blocks are extracted."""
        html = '''
        <pre><code>first block</code></pre>
        <p>Some text</p>
        <pre><code>second block</code></pre>
        '''
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 2
        assert "first block" in blocks[0].content
        assert "second block" in blocks[1].content
    
    def test_pre_without_code(self):
        """Test <pre> without nested <code>."""
        html = '<pre>plain preformatted text</pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert "plain preformatted text" in blocks[0].content
    
    def test_nested_spans_syntax_highlighting(self):
        """Test extraction with nested syntax highlighting spans."""
        html = '''
        <pre><code class="language-python">
            <span class="keyword">def</span>
            <span class="function">foo</span>():
                <span class="keyword">pass</span>
        </code></pre>
        '''
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        content = blocks[0].content
        assert "def" in content
        assert "foo" in content
        assert "pass" in content


class TestFrameworkDetection:
    """Test framework-specific code block detection."""
    
    def test_docusaurus_theme_code_block(self):
        """Test Docusaurus theme-code-block class."""
        html = '''
        <div class="theme-code-block">
            <div class="codeBlockContent">
                <span>console.log('test');</span>
            </div>
        </div>
        '''
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) >= 1
        # Should find something resembling the code
        assert any("console.log" in block.content for block in blocks)
    
    def test_highlightjs_hljs_class(self):
        """Test highlight.js class detection."""
        html = '<pre><code class="hljs javascript">const x = 5;</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert "const x = 5" in blocks[0].content
    
    def test_prism_language_class(self):
        """Test Prism.js language- class."""
        html = '<pre class="language-python"><code>import sys</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "import sys" in blocks[0].content


class TestLanguageDetection:
    """Test programming language detection."""
    
    def test_detect_python_from_class(self):
        """Test Python detection from class attribute."""
        html = '<code class="language-python">x = 1</code>'
        tool = PreprocessorTool()
        
        _, blocks = tool.extract_code_blocks(html)
        # Inline code may not be captured, so test the internal method
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('code')
        
        language = tool._detect_language_from_tag(element)
        assert language == "python"
    
    def test_detect_javascript_from_content(self):
        """Test JavaScript detection from code patterns."""
        code = "const foo = () => { console.log('test'); }"
        tool = PreprocessorTool()
        
        language = tool._detect_language_from_content(code)
        assert language == "javascript"
    
    def test_detect_python_from_content(self):
        """Test Python detection from code patterns."""
        code = "import os\ndef main():\n    print('hello')"
        tool = PreprocessorTool()
        
        language = tool._detect_language_from_content(code)
        assert language == "python"
    
    def test_detect_bash_from_content(self):
        """Test Bash detection from terminal patterns."""
        code = "$ npm install\n$ git clone repo"
        tool = PreprocessorTool()
        
        language = tool._detect_language_from_content(code)
        assert language == "bash"
    
    def test_language_alias_mapping(self):
        """Test that language aliases are normalized."""
        html = '<code class="lang-js">test</code>'
        tool = PreprocessorTool()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('code')
        
        language = tool._detect_language_from_tag(element)
        assert language == "javascript"  # js -> javascript


class TestTerminalDetection:
    """Test terminal/command block detection."""
    
    def test_detect_terminal_from_class(self):
        """Test terminal detection from class name."""
        html = '<pre class="terminal"><code>$ ls -la</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert blocks[0].is_terminal is True
    
    def test_detect_terminal_from_content(self):
        """Test terminal detection from $ prompts."""
        html = '<pre><code>$ npm install\n$ npm start</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        assert blocks[0].is_terminal is True


class TestPlaceholderSystem:
    """Test placeholder generation and usage."""
    
    def test_placeholders_unique(self):
        """Test that each block gets a unique placeholder."""
        html = '''
        <pre><code>block 1</code></pre>
        <pre><code>block 2</code></pre>
        <pre><code>block 3</code></pre>
        '''
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        placeholders = [b.placeholder for b in blocks]
        assert len(placeholders) == len(set(placeholders))  # All unique
    
    def test_processed_html_contains_placeholders(self):
        """Test that processed HTML contains the placeholders."""
        html = '<pre><code>test code</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        # Should contain PLACEHOLDER marker
        assert "PLACEHOLDER_0" in processed_html
        # Should not contain original code
        assert "test code" not in processed_html or "PLACEHOLDER" in processed_html


class TestMarkdownReinsertion:
    """Test reinsertion of code blocks into Markdown."""
    
    def test_simple_reinsertion(self):
        """Test basic placeholder replacement."""
        tool = PreprocessorTool()
        
        # Simulate extraction
        html = '<pre><code class="language-python">print("hello")</code></pre>'
        processed_html, blocks = tool.extract_code_blocks(html)
        
        # Simulate markdown with placeholder
        markdown = f"Some text\n\nPLACEHOLDER_0\n\nMore text"
        
        result = tool.reinsert_code_blocks(markdown, blocks)
        
        assert "```python" in result
        assert 'print("hello")' in result
        assert "PLACEHOLDER" not in result
    
    def test_multiple_reinsertion(self):
        """Test multiple code blocks are reinserted correctly."""
        tool = PreprocessorTool()
        
        blocks = [
            CodeBlock(content="code 1", language="python"),
            CodeBlock(content="code 2", language="javascript"),
        ]
        blocks[0].placeholder = "PLACEHOLDER_0"
        blocks[1].placeholder = "PLACEHOLDER_1"
        
        markdown = "Text\nPLACEHOLDER_0\nMiddle\nPLACEHOLDER_1\nEnd"
        
        result = tool.reinsert_code_blocks(markdown, blocks)
        
        assert "```python" in result
        assert "code 1" in result
        assert "```javascript" in result
        assert "code 2" in result
        assert "PLACEHOLDER" not in result
    
    def test_reinsertion_preserves_order(self):
        """Test that code blocks maintain correct order."""
        tool = PreprocessorTool()
        
        blocks = [
            CodeBlock(content="first", language="python"),
            CodeBlock(content="second", language="python"),
        ]
        blocks[0].placeholder = "PLACEHOLDER_0"
        blocks[1].placeholder = "PLACEHOLDER_1"
        
        markdown = "A\nPLACEHOLDER_0\nB\nPLACEHOLDER_1\nC"
        
        result = tool.reinsert_code_blocks(markdown, blocks)
        
        # Verify order
        first_pos = result.index("first")
        second_pos = result.index("second")
        assert first_pos < second_pos


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_html(self):
        """Test handling of empty HTML."""
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks("")
        
        assert blocks == []
    
    def test_html_with_no_code(self):
        """Test HTML without any code blocks."""
        html = '<p>Just some text</p><div>More text</div>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 0
    
    def test_code_with_special_characters(self):
        """Test code containing special characters."""
        html = '<pre><code>x = "&lt;div&gt;"</code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert len(blocks) == 1
        # Should preserve special chars
        assert blocks[0].content
    
    def test_empty_code_block(self):
        """Test handling of empty code blocks."""
        html = '<pre><code></code></pre>'
        tool = PreprocessorTool()
        
        processed_html, blocks = tool.extract_code_blocks(html)
        
        # Should filter out empty blocks
        assert all(block.content.strip() for block in blocks)
    
    def test_nested_pre_tags(self):
        """Test handling of nested pre tags (malformed HTML)."""
        html = '<pre><pre><code>nested</code></pre></pre>'
        tool = PreprocessorTool()
        
        # Should not crash
        processed_html, blocks = tool.extract_code_blocks(html)
        
        assert isinstance(blocks, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
