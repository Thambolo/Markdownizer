"""Content extraction and Markdown conversion tool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md


class ExtractorTool:
    """Tool for extracting content and converting to Markdown."""

    def __init__(self):
        """Initialize the extractor."""
        self._cache: dict[str, str] = {}

    def extract_with_trafilatura(
        self, html: str, url: str
    ) -> dict[str, str | int | None]:
        """
        Extract clean text from HTML using trafilatura.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Use trafilatura to extract main content
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                output_format="txt",
            )

            # Also get HTML version for Markdown conversion
            html_content = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                output_format="html",
            )

            if text and html_content:
                return {
                    "text": text,
                    "html": html_content,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "success": True,
                    "error": None,
                }
            else:
                return {
                    "text": "",
                    "html": "",
                    "char_count": 0,
                    "word_count": 0,
                    "success": False,
                    "error": "Trafilatura returned no content",
                }

        except Exception as e:
            return {
                "text": "",
                "html": "",
                "char_count": 0,
                "word_count": 0,
                "success": False,
                "error": f"Extraction error: {str(e)}",
            }

    def convert_to_markdown(
        self, html: str, title: str, url: str, include_metadata: bool = True
    ) -> str:
        """
        Convert HTML to Markdown using markdownify.

        Args:
            html: Clean HTML content
            title: Page title
            url: Source URL
            include_metadata: Whether to include metadata header

        Returns:
            Markdown formatted string
        """
        try:
            # Defensive: handle None or non-string input
            if not html:
                raise ValueError("No HTML content provided")

            # Clean HTML first
            soup = BeautifulSoup(html, "html.parser")
            
            # STEP 1: Extract language info from code blocks and add markers
            # This preserves class information before markdownify loses it
            code_lang_map = {}
            code_counter = 0
            
            for pre_tag in soup.find_all('pre'):
                code_tag = pre_tag.find('code')
                if code_tag:
                    # Detect language from class attributes
                    lang = self._extract_language_from_classes(code_tag)
                    if not lang and pre_tag:
                        lang = self._extract_language_from_classes(pre_tag)
                    
                    # Add a unique marker that will survive markdownify
                    marker = f"LANGMARKER_{code_counter}"
                    code_lang_map[marker] = lang
                    
                    # Insert marker as a comment in the code
                    if code_tag.string:
                        code_tag.string = f"{marker}\n{code_tag.string}"
                    else:
                        # If code has child elements, prepend marker
                        marker_tag = soup.new_string(f"{marker}\n")
                        code_tag.insert(0, marker_tag)
                    
                    code_counter += 1

            # Remove unwanted elements
            for tag in soup(
                ["script", "style", "nav", "footer", "header", "aside", "iframe"]
            ):
                tag.decompose()

            # Convert to Markdown
            markdown = md(
                str(soup),
                heading_style="ATX",
                bullets="-",
                strong_em_symbol="*",
                code_block_style="fenced",
            )
            
            # STEP 2: Replace markers with language identifiers
            # Pattern: ```\nLANGMARKER_0\ncode
            # Replace with: ```python\ncode
            import re
            for marker, lang in code_lang_map.items():
                # Match: ```\nMARKER or ```language\nMARKER
                pattern = rf'```(\w*)\s*\n{re.escape(marker)}\s*\n'
                if lang:
                    replacement = f'```{lang}\n'
                else:
                    replacement = '```\n'
                markdown = re.sub(pattern, replacement, markdown)
            
            # Add metadata header if requested
            if include_metadata:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                header = f"""# {title}

**Source**: {url}  
**Captured**: {timestamp}

---

"""
                markdown = header + markdown.strip()

            return markdown

        except Exception as e:
            # Fallback: return plain text in code block
            safe_preview = "" if not isinstance(html, str) else (html[:1000] + "...")
            return f"""# {title}

**Source**: {url}  
**Error**: Failed to convert to Markdown: {str(e)}

```
{safe_preview}
```
"""

    def fix_fragmented_code_blocks(self, markdown: str) -> str:
        """
        Fix fragmented inline code that should be fenced code blocks.
        
        Detects patterns like:
        `1from connectonion import Agent
        2
        3# Comment
        4code_here()`
        
        And converts to:
        ```python
        from connectonion import Agent
        
        # Comment
        code_here()
        ```
        
        Args:
            markdown: Markdown with potentially fragmented code
            
        Returns:
            Markdown with proper fenced code blocks
        """
        import re
        
        # Pattern: backtick, line number, optional content with newlines, ending backtick
        # Matches both:
        # - Single line: `1code`
        # - Multi-line: `1code\n2more\n3stuff`
        pattern = r'`(\d+[^\n`]*(?:\n\d+[^\n`]*)*)`'
        
        def replace_code_block(match):
            content = match.group(1)
            
            # Split by newlines and strip line numbers
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Remove leading line number (e.g., "1from" -> "from")
                cleaned = re.sub(r'^\d+', '', line)
                cleaned_lines.append(cleaned)
            
            # Convert any code block with line numbers (even single line)
            if len(cleaned_lines) >= 1:
                # Detect language
                code_content = '\n'.join(cleaned_lines)
                lang = self._detect_language_from_code(code_content)
                
                # Return fenced code block
                return f'\n```{lang}\n{code_content}\n```\n'
            else:
                # Empty, keep as-is
                return match.group(0)
        
        # Apply the replacement
        result = re.sub(pattern, replace_code_block, markdown)
        
        return result
    
    def _detect_language_from_code(self, code: str) -> str:
        """
        Detect programming language from code content.
        
        Args:
            code: Code content
            
        Returns:
            Language identifier (python, javascript, bash, etc.)
        """
        import re
        
        # HTML patterns (check first as it's most distinctive)
        if re.search(r'<!DOCTYPE html>|<html|<div|<head|<body|<script|<style', code, re.IGNORECASE):
            return 'html'
        
        # XML patterns
        if re.search(r'<\?xml|<AppDomains?>', code):
            return 'xml'
        
        # Rust patterns (check before JavaScript to avoid 'fn' confusion)
        if re.search(r'\bfn\s+\w+\s*\(', code) and (re.search(r'\blet\s+mut\s+', code) or re.search(r'use\s+std::', code) or re.search(r'println!', code)):
            return 'rust'
        
        # JavaScript/TypeScript patterns
        js_patterns = [
            r'\b(const|let|var)\s+\w+',
            r'\bfunction\s+\w+\s*\(',
            r'=>',
            r'console\.(log|error|warn)',
            r'async\s+function',
            r'await\s+',
            r'\.then\(',
            r'Office\.(context|onReady)',
            r'asyncResult',
            r'getElementById|querySelector',
        ]
        if any(re.search(pattern, code) for pattern in js_patterns):
            return 'javascript'
        
        # TypeScript specific patterns
        if re.search(r':\s*(string|number|boolean|void|any)\b', code) or re.search(r'\binterface\s+\w+', code):
            return 'typescript'
        
        # Python patterns
        python_patterns = [
            r'\b(import|from)\s+\w+',
            r'\bdef\s+\w+\s*\(',
            r'\bclass\s+\w+',
            r'\bprint\s*\(',
            r'if\s+__name__\s*==',
            r':\s*$',  # Colon at end of line (function/class definitions)
        ]
        if any(re.search(pattern, code, re.MULTILINE) for pattern in python_patterns):
            return 'python'
        
        # Bash/Shell patterns
        bash_patterns = [
            r'^\$\s',
            r'^#!\s*/bin/(bash|sh)',
            r'\b(sudo|apt-get|brew|npm|pip|git|docker|cd|ls|mkdir)\s',
            r'\bexport\s+\w+=',
        ]
        if any(re.search(pattern, code, re.MULTILINE) for pattern in bash_patterns):
            return 'bash'
        
        # JSON patterns
        if re.search(r'^\s*[\{\[]', code.strip()) and re.search(r':\s*[\{\[\"\'\d]', code):
            try:
                import json
                json.loads(code)
                return 'json'
            except:
                pass
        
        # CSS patterns
        if re.search(r'\w+\s*\{[^}]*\}', code) and re.search(r'(color|width|height|margin|padding):', code):
            return 'css'
        
        # SQL patterns
        if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN)\b', code, re.IGNORECASE):
            return 'sql'
        
        # YAML patterns
        if re.search(r'^\w+:\s*$', code, re.MULTILINE) or re.search(r'^\s+-\s+\w+', code, re.MULTILINE):
            return 'yaml'
        
        # Go patterns
        if re.search(r'\bpackage\s+\w+', code) or re.search(r'\bfunc\s+\w+\s*\(', code):
            return 'go'
        
        # Rust patterns
        if re.search(r'\bfn\s+\w+', code) or re.search(r'\blet\s+mut\s+', code) or re.search(r'use\s+std::', code):
            return 'rust'
        
        # Java patterns
        if re.search(r'\b(public|private|protected)\s+(class|interface)', code) or re.search(r'System\.out\.println', code):
            return 'java'
        
        # C/C++ patterns
        if re.search(r'#include\s*<', code) or re.search(r'\bstd::', code) or re.search(r'int\s+main\s*\(', code):
            if re.search(r'\bstd::', code) or re.search(r'#include\s*<iostream>', code):
                return 'cpp'
            return 'c'
        
        # C# patterns
        if re.search(r'\bnamespace\s+\w+', code) or re.search(r'\busing\s+System', code):
            return 'csharp'
        
        # Ruby patterns
        if re.search(r'\b(def|end|require|puts|attr_accessor)\b', code):
            return 'ruby'
        
        # PHP patterns
        if re.search(r'<\?php', code) or re.search(r'\$\w+\s*=', code):
            return 'php'
        
        # Swift patterns
        if re.search(r'\b(func|var|let)\s+\w+', code) and re.search(r'->', code):
            return 'swift'
        
        # Kotlin patterns
        if re.search(r'\b(fun|val|var)\s+\w+', code):
            return 'kotlin'
        
        # Markdown patterns
        if re.search(r'^#{1,6}\s', code, re.MULTILINE) and re.search(r'\[.*?\]\(.*?\)', code):
            return 'markdown'
        
        # Dockerfile patterns
        if re.search(r'^\s*(FROM|RUN|COPY|ADD|WORKDIR|ENV|EXPOSE)\s+', code, re.MULTILINE | re.IGNORECASE):
            return 'dockerfile'
        
        # Default to no language
        return ''

    def _extract_language_from_classes(self, element) -> str:
        """
        Extract programming language from HTML element classes.
        
        Common patterns:
        - lang-js, lang-python, lang-html
        - language-javascript, language-python
        - hljs-javascript, prism-python
        - s-lang-js (StackOverflow)
        
        Args:
            element: BeautifulSoup element (code or pre tag)
            
        Returns:
            Language identifier or empty string
        """
        import re
        
        classes = element.get('class', [])
        if not classes:
            return ''
        
        # Join all classes into one string for easier matching
        class_str = ' '.join(classes) if isinstance(classes, list) else classes
        
        # Common language class patterns
        patterns = [
            (r'\blang-(\w+)', 1),                    # lang-js, lang-python
            (r'\blanguage-(\w+)', 1),                # language-javascript
            (r'\bs-lang-(\w+)', 1),                  # s-lang-js (StackOverflow)
            (r'\bhljs-(\w+)', 1),                    # hljs-javascript
            (r'\bprism-(\w+)', 1),                   # prism-python
            (r'\bcode-(\w+)', 1),                    # code-python
            (r'\bsyntax-(\w+)', 1),                  # syntax-javascript
        ]
        
        for pattern, group in patterns:
            match = re.search(pattern, class_str)
            if match:
                lang = match.group(group).lower()
                # Normalize common aliases
                return self._normalize_language_name(lang)
        
        return ''
    
    def _normalize_language_name(self, lang: str) -> str:
        """
        Normalize language names to standard identifiers.
        
        Supports all common languages used in markdown viewers:
        GitHub, GitLab, VS Code, Obsidian, Notion, etc.
        
        Args:
            lang: Raw language name from class
            
        Returns:
            Normalized language identifier
        """
        # Map common aliases to standard names
        lang_map = {
            # JavaScript family
            'js': 'javascript',
            'jsx': 'javascript',
            'node': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            
            # Python
            'py': 'python',
            'python3': 'python',
            'python2': 'python',
            
            # Shell/Bash
            'sh': 'bash',
            'shell': 'bash',
            'zsh': 'bash',
            'fish': 'bash',
            'powershell': 'powershell',
            'ps1': 'powershell',
            
            # Web
            'yml': 'yaml',
            'md': 'markdown',
            'mdown': 'markdown',
            'htm': 'html',
            
            # C family
            'c++': 'cpp',
            'cplusplus': 'cpp',
            'c#': 'csharp',
            'cs': 'csharp',
            'objc': 'objective-c',
            
            # JVM languages
            'kt': 'kotlin',
            'groovy': 'groovy',
            'scala': 'scala',
            
            # Functional languages
            'hs': 'haskell',
            'clj': 'clojure',
            'cljs': 'clojure',
            'erl': 'erlang',
            'ex': 'elixir',
            'exs': 'elixir',
            'fs': 'fsharp',
            'fsx': 'fsharp',
            
            # Systems languages
            'rs': 'rust',
            'golang': 'go',
            
            # Scripting
            'rb': 'ruby',
            'pl': 'perl',
            'lua': 'lua',
            'r': 'r',
            
            # Mobile
            'swift': 'swift',
            'dart': 'dart',
            
            # Data/Config
            'json5': 'json',
            'jsonc': 'json',
            'toml': 'toml',
            'ini': 'ini',
            'cfg': 'ini',
            'conf': 'ini',
            
            # Database
            'pgsql': 'sql',
            'mysql': 'sql',
            'plsql': 'sql',
            'tsql': 'sql',
            
            # Markup/Document
            'tex': 'latex',
            'latex': 'latex',
            'rst': 'restructuredtext',
            'adoc': 'asciidoc',
            
            # Other popular
            'dockerfile': 'dockerfile',
            'docker': 'dockerfile',
            'makefile': 'makefile',
            'make': 'makefile',
            'graphql': 'graphql',
            'gql': 'graphql',
            'proto': 'protobuf',
            'diff': 'diff',
            'patch': 'diff',
            'regex': 'regex',
            'regexp': 'regex',
        }
        
        return lang_map.get(lang, lang)

    def clean_markdown(self, markdown: str) -> str:
        """
        Clean up excessive whitespace in Markdown.

        Args:
            markdown: Raw markdown string

        Returns:
            Cleaned markdown string
        """
        lines = markdown.split("\n")
        cleaned = []
        prev_blank = False

        for line in lines:
            is_blank = not line.strip()

            # Skip consecutive blank lines
            if is_blank and prev_blank:
                continue

            cleaned.append(line)
            prev_blank = is_blank

        return "\n".join(cleaned)
