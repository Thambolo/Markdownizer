# Architecture

This file contains the detailed architecture notes and ASCII diagram.

## Overview

The project consists of two cooperating components:

- Browser extension (MV3) — captures user-visible DOM, expands content, runs Readability.js and POSTs a readability candidate to the local agent.
- Local Agent Service (FastAPI + ConnectOnion) — independently fetches the URL, extracts with trafilatura, optionally runs a Playwright probe for blockers, compares the extension's capture vs the agent extraction, converts chosen content to Markdown, and returns diagnostics.

For the original, full ASCII architecture diagram and step-by-step flow, see the original README content archived here.


## Full architecture diagram and flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser Extension                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. User clicks extension → Inject Readability.js           │ │
│  │ 2. Auto-expand content (scroll, "show more", details)      │ │
│  │ 3. Extract clean HTML with Readability                     │ │
│  │ 4. Collect metadata (stats, iframes)                       │ │
│  │ 5. POST to /ingest → Local Agent                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
								│
								▼
┌─────────────────────────────────────────────────────────────────┐
│                       Local Agent Service                        │
│                        (Python + FastAPI)                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 6. Receive extension payload (A = Readability HTML)        │ │
│  │ 7. Fetch URL independently with httpx                      │ │
│  │ 8. ⚡ FAST PATH: If redirect detected →                     │ │
│  │    • Use extension's content (skip comparison)             │ │
│  │    • Return success with diagnostics                       │ │
│  │ 9. Extract code blocks from raw HTML (preserve formatting) │ │
│  │ 10. Extract with trafilatura (B)                           │ │
│  │ 11. [Optional] Playwright probe if content < 500 chars     │ │
│  │ 12. If blockers detected → Use extension's content         │ │
│  │ 13. Compare A vs B using scoring algorithm                 │ │
│  │ 14. Choose winner (tie = prefer A)                         │ │
│  │ 15. Convert to Markdown with markdownify                   │ │
│  │ 16. Reinsert code blocks as proper Markdown                │ │
│  │ 17. Normalize links, clean whitespace                      │ │
│  │ 18. Return Markdown + diagnostics                          │ │
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

### Notes
- The extension runs in the user's browser and benefits from authenticated sessions and JS-rendered DOM.
- The agent runs independent network fetches and therefore provides a baseline extraction that can be compared.

