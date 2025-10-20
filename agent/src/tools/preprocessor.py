"""
Code block preprocessing tool for Markdownizer.

Extracts code blocks from HTML before content cleanup to preserve them,
then reinjects them after Markdown conversion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup, Tag, NavigableString, Comment


@dataclass
class CodeBlock:
    """Represents an extracted code block with metadata."""
    
    content: str
    language: str = "text"
    is_terminal: bool = False
    line_numbers: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
    placeholder: str = ""
    
    def to_markdown(self) -> str:
        """Convert to Markdown code block format."""
        fence = "```"
        lang = self.language if self.language != "text" else ""
        
        # Clean content - remove line numbers if present
        content = self._strip_line_numbers(self.content) if self.line_numbers else self.content
        
        # Terminal blocks use $ prompt style
        if self.is_terminal:
            lines = content.strip().split('\n')
            formatted = '\n'.join(f"$ {line.lstrip('$').strip()}" for line in lines if line.strip())
            return f"{fence}bash\n{formatted}\n{fence}"
        
        return f"{fence}{lang}\n{content.strip()}\n{fence}"
    
    @staticmethod
    def _strip_line_numbers(content: str) -> str:
        """
        Remove line numbers from code content.
        Handles patterns like:
        - "1from connectonion import Agent"
        - "2"
        - "3# Comment"
        """
        import re
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Match line number at start: digit(s) followed by code or empty
            # Pattern: ^(\d+)(.*)$
            match = re.match(r'^(\d+)(.*)$', line)
            if match:
                # Keep everything after the number
                cleaned_lines.append(match.group(2))
            else:
                # No line number, keep as-is
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)


class PreprocessorTool:
    """
    Extracts code blocks from HTML before cleanup, preserves them through
    processing, and reinjects as proper Markdown code blocks.
    
    Strategies (Phase 1):
    1. Semantic HTML: <pre>, <code>, <samp>, <kbd>
    2. Framework detection: Common documentation frameworks
    3. Placeholder system: Safe passthrough
    """
    
    # Common documentation framework selectors
    FRAMEWORK_PATTERNS = {
        # Docusaurus
        'docusaurus': [
            '.theme-code-block',
            '[class*="codeBlock"]',
            '.prism-code',
        ],
        # Mintlify
        'mintlify': [
            '[class*="CodeBlock"]',
            '[class*="CodeGroup"]',
        ],
        # GitBook
        'gitbook': [
            '.code-block',
            '[data-gb-custom-block]',
        ],
        # Nextra
        'nextra': [
            '[class*="nextra-code"]',
            '.nx-code-block',
        ],
        # VuePress
        'vuepress': [
            '.vuepress-code-block',
            'div[class*="language-"]',
        ],
        # Generic highlight.js
        'highlightjs': [
            '.hljs',
            '[class*="hljs-"]',
        ],
        # Generic Prism
        'prism': [
            '[class*="prism"]',
            '[class*="language-"]',
        ],
    }
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': [
            r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import',
            r'\bdef\s+\w+\s*\(',
            r'\bclass\s+\w+',
            r'print\s*\(',
        ],
        'javascript': [
            r'\bconst\s+\w+',
            r'\blet\s+\w+',
            r'\bvar\s+\w+',
            r'\bfunction\s+\w+\s*\(',
            r'=>',
            r'console\.log',
        ],
        'typescript': [
            r'\binterface\s+\w+',
            r'\btype\s+\w+\s*=',
            r':\s*(string|number|boolean)',
        ],
        'bash': [
            r'^\$\s',
            r'^#\s',
            r'\bsudo\s',
            r'\bapt-get\s',
            r'\bgit\s',
            r'\bnpm\s',
            r'\bpip\s',
        ],
        'json': [
            r'^\s*[\{\[]',
            r':\s*[\{\[\"\'\d]',
        ],
        'yaml': [
            r'^\w+:\s*$',
            r'^\s+-\s+\w+',
        ],
    }
    
    def __init__(self):
        """Initialize the preprocessor tool."""
        # Public placeholder format used by tests and reinsertion
        # e.g. PLACEHOLDER_0, PLACEHOLDER_1
        self._placeholder_prefix = "PLACEHOLDER_"
        self._placeholder_suffix = ""
        self._block_counter = 0
    
    def extract_code_blocks(self, html: str) -> tuple[str, list[CodeBlock]]:
        """
        Extract code blocks from HTML and replace with placeholders.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Tuple of (HTML with placeholders, list of extracted code blocks)
        """
        soup = BeautifulSoup(html, 'html.parser')
        blocks: list[CodeBlock] = []
        
        # Strategy 1: Semantic HTML (<pre><code>)
        blocks.extend(self._extract_semantic_html(soup))
        
        # Strategy 2: Framework-specific patterns
        blocks.extend(self._extract_framework_blocks(soup))
        
        # Generate placeholders for all blocks (human-friendly token)
        for i, block in enumerate(blocks):
            block.placeholder = f"{self._placeholder_prefix}{i}{self._placeholder_suffix}"

        return str(soup), blocks
    
    def _extract_semantic_html(self, soup: BeautifulSoup) -> list[CodeBlock]:
        """
        Extract code blocks from semantic HTML elements.
        
        Targets: <pre><code>, <code>, <samp>, <kbd>
        """
        blocks: list[CodeBlock] = []
        
        # Find all <pre> tags (most common for code blocks)
        for pre_tag in soup.find_all('pre'):
            # Get the code element inside (if exists)
            code_tag = pre_tag.find('code')
            
            if code_tag:
                content = self._extract_text_content(code_tag)
                language = self._detect_language_from_tag(code_tag)
                is_terminal = self._is_terminal_block(pre_tag, code_tag)
                has_line_numbers = self._has_line_numbers(content)
                
                if content.strip():
                    block = CodeBlock(
                        content=content,
                        language=language,
                        is_terminal=is_terminal,
                        line_numbers=has_line_numbers,
                        metadata={'source': 'semantic_html', 'tag': 'pre>code'}
                    )
                    blocks.append(block)
                    
                    # Replace with simple placeholder token so downstream
                    # markdown conversion preserves a distinct marker that
                    # we can reinstate later. Tests expect `PLACEHOLDER_{i}`
                    placeholder_token = soup.new_string(f"{self._placeholder_prefix}{len(blocks)-1}{self._placeholder_suffix}")
                    pre_tag.replace_with(placeholder_token)
            else:
                # <pre> without <code> (less common but valid)
                content = self._extract_text_content(pre_tag)
                if content.strip():
                    block = CodeBlock(
                        content=content,
                        language='text',
                        metadata={'source': 'semantic_html', 'tag': 'pre'}
                    )
                    blocks.append(block)
                    
                    placeholder_token = soup.new_string(f"{self._placeholder_prefix}{len(blocks)-1}{self._placeholder_suffix}")
                    pre_tag.replace_with(placeholder_token)
        
        # Standalone <code> tags (inline code, but sometimes used for blocks)
        for code_tag in soup.find_all('code'):
            # Skip if already processed as part of <pre>
            if code_tag.find_parent('pre'):
                continue
            
            content = self._extract_text_content(code_tag)
            # Only treat as block if multiline or long
            if '\n' in content or len(content) > 60:
                language = self._detect_language_from_tag(code_tag)
                has_line_numbers = self._has_line_numbers(content)
                block = CodeBlock(
                    content=content,
                    language=language,
                    line_numbers=has_line_numbers,
                    metadata={'source': 'semantic_html', 'tag': 'code'}
                )
                blocks.append(block)
                
                placeholder_token = soup.new_string(f"{self._placeholder_prefix}{len(blocks)-1}{self._placeholder_suffix}")
                code_tag.replace_with(placeholder_token)
        
        return blocks
    
    def _extract_framework_blocks(self, soup: BeautifulSoup) -> list[CodeBlock]:
        """
        Extract code blocks using framework-specific selectors.
        """
        blocks: list[CodeBlock] = []
        
        for framework, selectors in self.FRAMEWORK_PATTERNS.items():
            for selector in selectors:
                try:
                    for element in soup.select(selector):
                        # Avoid duplicates (already processed by semantic HTML)
                        if element.find('pre') or any('PLACEHOLDER_' in str(c) for c in element.children if isinstance(c, NavigableString)):
                            continue
                        
                        content = self._extract_text_content(element)
                        if content.strip() and len(content) > 10:  # Minimum length threshold
                            language = self._detect_language_from_tag(element)
                            is_terminal = self._is_terminal_block(element)
                            has_line_numbers = self._has_line_numbers(content)
                            
                            block = CodeBlock(
                                content=content,
                                language=language,
                                is_terminal=is_terminal,
                                line_numbers=has_line_numbers,
                                metadata={'source': 'framework', 'framework': framework, 'selector': selector}
                            )
                            blocks.append(block)
                            
                            placeholder_token = soup.new_string(f"{self._placeholder_prefix}{len(blocks)-1}{self._placeholder_suffix}")
                            element.replace_with(placeholder_token)
                except Exception:
                    # Selector might not be valid for this HTML
                    continue
        
        return blocks
    
    def _extract_text_content(self, element: Tag) -> str:
        """
        Extract clean text content from an element, preserving structure.
        
        Handles nested spans from syntax highlighters.
        """
        # Get all text, preserving newlines
        text_parts = []
        
        for content in element.descendants:
            if isinstance(content, NavigableString):
                text = str(content)
                # Preserve meaningful whitespace
                if text and not text.isspace():
                    text_parts.append(text)
                elif '\n' in text:
                    text_parts.append('\n')
        
        # Join and clean up excessive whitespace
        full_text = ''.join(text_parts)
        
        # Remove common artifacts
        full_text = full_text.replace('\u200b', '')  # Zero-width space
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)  # Excessive newlines
        
        return full_text
    
    def _detect_language_from_tag(self, element: Tag) -> str:
        """
        Detect programming language from element attributes and content.
        """
        # Check class attribute (most common: class="language-python")
        classes = element.get('class', [])
        for cls in classes:
            if isinstance(cls, str):
                # language-python, lang-python, python, hljs-python, prism-python
                match = re.search(r'(?:language-|lang-|hljs-|prism-)?(\w+)', cls)
                if match:
                    lang = match.group(1).lower()
                    # Map common aliases
                    if lang in ('js', 'javascript', 'jsx'):
                        return 'javascript'
                    elif lang in ('ts', 'typescript', 'tsx'):
                        return 'typescript'
                    elif lang in ('py', 'python3'):
                        return 'python'
                    elif lang in ('sh', 'bash', 'shell', 'zsh'):
                        return 'bash'
                    elif lang in ('yml'):
                        return 'yaml'
                    elif lang not in ('hljs', 'prism', 'code', 'block'):
                        return lang
        
        # Check data-language attribute
        data_lang = element.get('data-language') or element.get('data-lang')
        if data_lang:
            return str(data_lang).lower()
        
        # Analyze content patterns
        content = self._extract_text_content(element)
        return self._detect_language_from_content(content)
    
    def _detect_language_from_content(self, content: str) -> str:
        """
        Detect programming language from code content using patterns.
        """
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return lang
        
        return 'text'
    
    def _is_terminal_block(self, *elements: Tag) -> bool:
        """
        Determine if this is a terminal/command block.
        """
        for element in elements:
            # Check classes
            classes = element.get('class', [])
            for cls in classes:
                if isinstance(cls, str) and any(term in cls.lower() for term in ['terminal', 'command', 'console', 'shell']):
                    return True
            
            # Check content
            content = self._extract_text_content(element)
            lines = content.strip().split('\n')
            # If majority of lines start with $ or #, it's terminal
            prompt_lines = sum(1 for line in lines if line.strip().startswith(('$', '#')))
            if prompt_lines > len(lines) * 0.5:
                return True
        
        return False
    
    def inject_code_into_html(self, trafilatura_html: str, blocks: list[CodeBlock]) -> str:
        """
        Inject extracted code blocks back into trafilatura's cleaned HTML.
        
        Since trafilatura removes code blocks during extraction, we need to
        intelligently re-inject them. This uses BeautifulSoup to find suitable
        injection points based on surrounding text context.
        
        Args:
            trafilatura_html: HTML from trafilatura (already cleaned)
            blocks: Code blocks extracted from original HTML
            
        Returns:
            HTML with code blocks injected back in appropriate locations
        """
        if not blocks or not trafilatura_html:
            return trafilatura_html
            
        soup = BeautifulSoup(trafilatura_html, 'html.parser')
        
        # Simple strategy: append all code blocks at the end in order
        # This ensures they're in the document, even if not perfectly positioned
        # TODO: Implement smarter positioning based on surrounding text
        
        body = soup.find('body') or soup
        
        for block in blocks:
            # Create a proper <pre><code> structure
            pre = soup.new_tag('pre')
            code = soup.new_tag('code')
            
            # Set language class if available
            if block.language and block.language != 'text':
                code['class'] = f'language-{block.language}'
            
            # Strip line numbers before injecting into HTML
            content = CodeBlock._strip_line_numbers(block.content) if block.line_numbers else block.content
            code.string = content
            pre.append(code)
            body.append(pre)
        
        return str(soup)
    
    def _has_line_numbers(self, content: str) -> bool:
        """
        Detect if code content has line numbers at the start of each line.
        
        Checks if most lines start with a digit followed by code.
        Examples: "1from", "2", "3#", "10def"
        
        Args:
            content: Code content to check
            
        Returns:
            True if content appears to have line numbers
        """
        import re
        
        lines = [line for line in content.split('\n') if line.strip()]
        if not lines:
            return False
        
        # Check how many lines start with a digit
        lines_with_numbers = 0
        for line in lines:
            # Match: starts with digit(s), optionally followed by code
            if re.match(r'^\d+', line):
                lines_with_numbers += 1
        
        # If 70%+ of non-empty lines start with a number, assume line numbers
        return lines_with_numbers >= len(lines) * 0.7
    
    def reinsert_code_blocks(self, markdown: str, blocks: list[CodeBlock]) -> str:
        """
        Replace placeholders with proper Markdown code blocks.
        
        Args:
            markdown: Markdown content with placeholders
            blocks: List of extracted code blocks
            
        Returns:
            Markdown with code blocks reinserted
        """
        result = markdown

        for i, block in enumerate(blocks):
            placeholder = f"{self._placeholder_prefix}{i}{self._placeholder_suffix}"
            markdown_block = block.to_markdown()

            # Replace all occurrences of the placeholder with the fenced code block
            if placeholder in result:
                result = result.replace(placeholder, markdown_block)

        return result
