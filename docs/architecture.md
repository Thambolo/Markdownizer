# Architecture

This file contains the detailed architecture notes and ASCII diagram.

## Overview

The project consists of two cooperating components:

- Browser extension (MV3) — captures user-visible DOM with priority extraction methods (Schema.org > Semantic HTML > Readability.js), expands content, and POSTs the best extraction to the local agent.
- Local Agent Service (FastAPI + ConnectOnion) — independently fetches the URL, extracts with trafilatura, optionally runs a Playwright probe for blockers, compares the extension's capture vs the agent extraction, converts chosen content to Markdown with code block handling, and returns diagnostics.

For the original, full ASCII architecture diagram and step-by-step flow, see the original README content archived here.


## Full architecture diagram and flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser Extension                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. User clicks extension → Inject extraction scripts       │ │
│  │ 2. Auto-expand content (scroll, "show more", details)      │ │
│  │ 3. Try Schema.org JSON-LD (85-90% reliability)             │ │
│  │ 4. Try Semantic HTML5 (75-80% reliability)                 │ │
│  │ 5. Fall back to Readability.js (100% coverage)             │ │
│  │ 6. Collect metadata (stats, iframes)                       │ │
│  │ 7. POST to /ingest → Local Agent                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
								│
								▼
┌─────────────────────────────────────────────────────────────────┐
│                       Local Agent Service                        │
│                        (Python + FastAPI)                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 8. Receive extension payload (A = best extraction)         │ │
│  │ 9. Fetch URL independently with httpx                      │ │
│  │ 10. ⚡ FAST PATH: If redirect detected →                    │ │
│  │    • Use extension's content (skip comparison)             │ │
│  │    • Return success with diagnostics                       │ │
│  │ 11. Extract with trafilatura (B)                           │ │
│  │ 12. [Optional] Playwright probe if content < 500 chars     │ │
│  │ 13. If blockers detected → Use extension's content         │ │
│  │ 14. Compare A vs B using scoring algorithm                 │ │
│  │ 15. Choose winner (tie = prefer A)                         │ │
│  │ 16. Convert to Markdown with markdownify                   │ │
│  │ 17. Fix code blocks (language detection, repair)           │ │
│  │ 18. Normalize links, clean whitespace                      │ │
│  │ 19. Return Markdown + diagnostics                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
								│
								▼
					┌───────────────────────┐
					│  Markdown Download    │
					└───────────────────────┘
```

### Redirect detection (fast path)

If the agent's independent fetch redirects to a different URL, the agent immediately prefers the browser's captured content. Redirects are a strong signal the agent can't access the same content (login wall, subscribe page, geo block).

### Extraction priority in browser

The extension uses a 3-tier extraction strategy:
1. **Schema.org JSON-LD** (85-90% reliability) - structured data, highest quality
2. **Semantic HTML5** (75-80% reliability) - semantic tags like `<article>`, `<main>`
3. **Readability.js** (100% coverage) - universal fallback for any page

### Notes
- The extension runs in the user's browser and benefits from authenticated sessions and JS-rendered DOM.
- The agent runs independent network fetches and therefore provides a baseline extraction that can be compared.
- Code blocks are handled in the final Markdown conversion step with language detection and formatting repair.

