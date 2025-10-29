# Code Block Preservation & Preprocessing

This file documents the code block extraction, line-number stripping and language hint preservation.

## Extraction strategy
1. Semantic HTML tags (`<pre>`, `<code>`, `<samp>`, `<kbd>`)
2. Standalone code-like blocks detection
3. Framework-specific containers (Prism.js, Highlight.js, Docusaurus, etc.)

## Line number detection & stripping
- Detect leading digit patterns and if >=70% of lines start with digits, strip the numeric prefixes.
- Regex used: `^(\d+)(.*)$` — the number is removed while preserving indentation and code.

## Language hints
- Extract language from class attributes: `language-python`, `lang-javascript`, `hljs-typescript`, `prism-`, etc.

## Reinsertion
Code blocks are replaced with placeholders prior to Markdown conversion and reinserted as fenced blocks with detected language.

--
*Moved from README: code block preservation details.*

## Full details

### Line Number Stripping Examples

Before (with line numbers):

```
1from typing import List
2
3def process(items: List[str]) -> str:
4    return ", ".join(items)
```

After (clean code):

```
from typing import List

def process(items: List[str]) -> str:
	return ", ".join(items)
```

### Detection algorithm
- Analyze each line for leading digit patterns (`^\d+`). If >=70% of lines start with digits, consider the block to have line numbers and strip them.

