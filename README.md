[![CI](https://github.com/Thambolo/Markdownizer/actions/workflows/ci.yml/badge.svg)](https://github.com/Thambolo/Markdownizer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/Thambolo/Markdownizer.svg?style=flat-square)](https://github.com/Thambolo/Markdownizer/commits/main)

# Markdownizer

> **AI-powered web content to Markdown conversion** — A professional tool for capturing and converting web pages to clean, structured Markdown format.

Markdownizer combines a browser extension with a local AI agent to intelligently extract and convert web content. The extension captures what you see (including authenticated pages), while the agent compares multiple extraction methods to produce the highest-quality Markdown output.

---

## ✨ Features

- **🎯 Smart Extraction** - Compares browser-captured content vs independent fetch to choose the best version
- **🔐 Auth-Aware** - Captures content from pages you're logged into (using your browser session)
- **🤖 AI-Powered** - Uses ConnectOnion framework with GPT for intelligent decision-making
- **📊 Quality Scoring** - Weighted algorithm considers length, density, structure, and semantic overlap
- **🚫 Blocker Detection** - Identifies login walls, paywalls, and captchas (doesn't bypass them)
- **💻 Code Block Preservation** - Intelligently extracts and preserves code examples with automatic line number stripping
- **� Link Normalization** - Converts relative URLs to absolute and removes tracking parameters
- **💾 Offline Fallback** - Auto-downloads raw HTML when agent is unavailable
- **🛡️ Privacy-First** - All processing happens locally—no external servers

---

## 🏗️ Architecture

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

### Redirect Detection (Fast Path)

**Priority #1: Universal Redirect Detection**

If the agent's independent fetch redirects to a different URL, Markdownizer immediately uses the extension's captured content without comparison.

**Why?** Redirects mean the agent is seeing a different page than the user:
- Login walls: `/article` → `/login`
- Paywalls: `/content` → `/subscribe`
- Auth gates: `/premium` → `/signup`
- Geo-blocks: `/video` → `/not-available`

**URL Normalization (Ignores Benign Differences):**
```python
# These are NOT considered redirects:
http://example.com/article  → https://example.com/article  # Scheme upgrade
www.example.com/post        → example.com/post             # www prefix
/article/                   → /article                     # Trailing slash

# These ARE considered redirects:
/article → /login           # Path changed
blog.site.com → auth.site.com  # Subdomain changed
```

**Result:** Returns `SuccessResponse` with extension's content immediately—no wasted time on extraction or comparison.

### Decision Algorithm (When No Redirect)

```python
score = (
    0.35 * normalized_length +
    0.20 * content_density +
    0.20 * semantic_overlap +
    0.10 * structure_richness +
    0.10 * date_freshness +
    0.05 * link_quality
) - blocker_penalty

# If |score_A - score_B| < 0.05: prefer extension's Readability (user-visible)
# Otherwise: choose higher-scoring candidate
```

**Blocker Detection:** If trafilatura extracts < 500 characters, Playwright probes for login walls, paywalls, or CAPTCHAs. If detected, returns success with extension's content.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Chrome or Edge browser**
- **Git** (for cloning)

**Optional:**
- **OpenAI API key** (only needed if ConnectOnion's free tier is unavailable)
  - Markdownizer uses ConnectOnion's **FREE tier** by default (100k tokens/month)
  - OpenAI key is only used as a fallback

### 1. Install the Agent Service

```bash
# Clone the repository
git clone https://github.com/Thambolo/Markdownizer.git
cd Markdownizer

# Download Readability.js (Windows PowerShell)
.\setup.ps1

# Or manually download it:
# Navigate to https://github.com/mozilla/readability
# Save Readability.js to extension/src/vendor/readability.js
```

```bash
# Navigate to agent directory
cd agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (optional, for blocker detection)
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
notepad .env  # Windows
# Or: nano .env  # macOS/Linux
```

### 2. Start the Agent

**Option A: Quick Start Script (Windows)**
```powershell
cd agent
.\start.ps1
```

**Option B: Manual Start**
```bash
# Make sure you're in agent/ directory with venv activated
python main.py

# Or use uvicorn directly:
uvicorn main:app --host 127.0.0.1 --port 5050 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:5050
INFO:     Application startup complete.
```

Test the health endpoint:
```bash
curl http://127.0.0.1:5050/health
# Expected: {"status":"ok","version":"1.0.0","timestamp":"..."}
```

### 3. Install the Browser Extension

1. Open Chrome/Edge and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `Markdownizer/extension/src` folder
5. Pin the extension to your toolbar

### 4. Configure the Extension

1. Right-click the extension icon → **Options**
2. Verify Agent URL is `http://127.0.0.1:5050`
3. Test connection (should show "Agent connected")

### 5. Convert a Page!

1. Navigate to any article or blog post
2. Click the Markdownizer extension icon
3. Wait a few seconds
4. Markdown file downloads automatically!

---

## 📁 Project Structure

```
Markdownizer/
├── agent/                      # Python agent service
│   ├── main.py                # FastAPI app & routes
│   ├── app.py                 # ConnectOnion agent setup
│   ├── config.py              # Settings (Pydantic)
│   ├── schemas.py             # Request/response models
│   ├── start.ps1              # Quick start script (Windows)
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   ├── .env                   # Your config (git-ignored)
│   ├── venv/                  # Virtual environment (git-ignored)
│   ├── src/
│   │   ├── tools/             # Agent tools (class instances)
│   │   │   ├── __init__.py
│   │   │   ├── fetcher.py     # HTTP client (httpx)
│   │   │   ├── extractor.py   # trafilatura + markdownify
│   │   │   ├── comparator.py  # Scoring & decision logic
│   │   │   ├── playwright_probe.py  # Blocker detection
│   │   │   └── normalizer.py  # Link normalization
│   │   └── prompts/
│   │       └── agent.md       # System prompt
│   └── tests/                 # Pytest test suite
│       ├── __init__.py
│       ├── test_comparator.py
│       ├── test_extractor.py
│       └── test_blockers.py
├── extension/                 # Browser extension (MV3)
│   └── src/                   # Extension root (load this folder)
│       ├── manifest.json      # Extension config
│       ├── sw.js              # Service worker
│       ├── content.js         # Content script
│       ├── options.html       # Settings UI
│       ├── options.js         # Settings logic
│       ├── css/
│       │   └── options.css    # Styles
│       ├── icons/             # Extension icons
│       │   ├── icon16.png
│       │   ├── icon48.png
│       │   └── icon128.png
│       └── vendor/
│           └── readability.js # Mozilla Readability
├── shared/
│   └── protocol.json          # API contract
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
├── setup.ps1                  # Download Readability.js (Windows)
├── README.md
├── QUICKSTART.md              # 5-minute setup guide
├── LICENSE
└── .gitignore
```

---

## ⚙️ Configuration

### Agent Environment Variables

The agent uses environment variables for configuration. Copy [`agent/.env.example`](agent/.env.example) to `agent/.env` and configure as needed.

**Key settings:**
- **Model Configuration** - ConnectOnion free tier (default) or OpenAI fallback
- **Server** - Host, port, and reload settings
- **Playwright** - Optional blocker detection settings
- **HTTP Client** - Timeout and retry configuration
- **Scoring** - Comparison algorithm thresholds

For complete documentation of all available options, see [`agent/.env.example`](agent/.env.example).

### Extension Settings

Access via: Right-click extension → Options

- **Agent URL**: Default `http://127.0.0.1:5050`
- **Auto-download backup**: Save HTML when agent offline

---

## 🔒 Security & Ethics

### What Markdownizer Does

✅ **Captures user-visible content** from your authenticated browser session  
✅ **Detects redirects** and uses your browser's capture when URLs don't match  
✅ **Compares sources** only when the agent can access the same page  
✅ **Detects blockers** (login/paywall/captcha) and uses your captured content  
✅ **Returns success** even with blockers—you get Markdown from what you can see  
✅ **Processes locally** — no external servers, all data stays on your machine

### What Markdownizer Does NOT Do

❌ **No paywall bypassing** — Uses YOUR browser session (you must have access)  
❌ **No auth automation** — No login flows, credentials, or cookies manipulated  
❌ **No captcha solving** — Detects CAPTCHAs but doesn't attempt to solve them  
❌ **No headed browsers** — Playwright only for blocker detection (headless, 30s, no scraping)  
❌ **No credential storage** — Zero persistence of passwords or session data  
❌ **No HTML sanitization needed** — Output is Markdown (plain text, non-executable)

### Security Posture

**Secure by Design:**
- **Markdown output** is plain text and cannot execute JavaScript or code
- **Script/style/iframe tags** are removed before conversion
- **BeautifulSoup** parsing is safe (no code execution)
- **markdownify** strips event handlers (onclick, onerror, etc.)
- **No HTML rendering** in the pipeline—only parsing and conversion

**Redirect Detection** prevents content mismatches:
- Agent cannot be tricked into processing wrong content
- User's authenticated capture is trusted source
- Transparent diagnostics show when redirects occurred

### Ethical Guidelines

- **Respect access controls** — Don't use to bypass paywalls or auth
- **Personal use** — For your own reading and research
- **Check terms of service** — Some sites prohibit automated access
- **Rate limiting** — Don't abuse the service on any site

---

## 🧪 Testing

Run tests with pytest:

```bash
cd agent
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_comparator.py -v
```

### Test Files

- `test_comparator.py` - Scoring algorithm and decision logic
  - Signal computation, semantic overlap, candidate scoring
  - Compare and decide logic with tie-breaking rules
  - Structure richness and blocker penalty handling
  
- `test_extractor.py` - Content extraction and Markdown conversion
  - Trafilatura extraction with success/failure cases
  - HTML to Markdown conversion with metadata
  - Script/style removal, link preservation, whitespace cleanup
  - Complex structure handling and error recovery
  
- `test_preprocessor.py` - Code block extraction and preservation
  - CodeBlock dataclass and to_markdown conversion
  - Semantic HTML extraction (`<pre>`, `<code>` tags)
  - Framework detection (Prism.js, Highlight.js, Docusaurus)
  - Language detection and terminal block identification
  - Placeholder system and Markdown reinsertion
  - Edge cases: empty HTML, special characters, nested tags
  
- `test_blockers.py` - Blocker detection (mocked Playwright)
  - Login walls, paywalls, and CAPTCHA detection
  - Thin content and cross-origin iframe handling
  - Clean page validation and resource cleanup

---

## 🎯 How Markdownizer Handles Different Scenarios

### Public Content (No Auth Required)

**Example:** Blog posts, news articles, documentation

```
1. Extension captures page with Readability.js
2. Agent fetches same URL independently → No redirect
3. Both extractions succeed
4. Comparison scores both versions
5. Chooses best quality → Usually trafilatura (cleaner)
6. Returns Markdown with diagnostics
```

**Result:** ✅ High-quality Markdown with optimal content extraction

### Authenticated Content (Logged In)

**Example:** Medium premium articles, paywalled news, private wikis

```
1. You're logged in → Extension captures full article (2000 words)
2. Agent fetches same URL → Redirects to /login (not logged in)
3. ⚡ Redirect detected immediately
4. Agent chooses extension's capture (no comparison needed)
5. Returns Markdown with redirect diagnostics
```

**Result:** ✅ Success! You get Markdown of the content you can see

**Diagnostics:**
```json
{
  "ok": true,
  "chosen": "readability",
  "redirect_detected": true,
  "original_url": "https://medium.com/@author/premium-post",
  "final_url": "https://medium.com/login"
}
```

### Soft Paywalls (Preview + Paywall)

**Example:** NYTimes (shows preview, then "subscribe to continue")

```
1. Extension captures full preview (300 chars) + paywall overlay
2. Agent fetches → Gets same content (no redirect)
3. Trafilatura extracts 320 chars (below 500 threshold)
4. Playwright probes → Detects paywall elements
5. Agent chooses extension's capture
6. Returns Markdown with blocker info
```

**Result:** ✅ Success! You get Markdown of what you captured

### Hard Paywalls (Immediate Block)

**Example:** Wall Street Journal article

```
1. Extension captures: "Subscribe to read" (50 chars)
2. Agent fetches → Gets "Subscribe to read" (50 chars)
3. Trafilatura extracts 50 chars (< 500 threshold)
4. Playwright probes → Detects paywall
5. Agent chooses extension's capture
6. Returns Markdown (minimal content)
```

**Result:** ⚠️ Success, but content is just the paywall message (you can't bypass this)

### Geo-Blocked Content

**Example:** Video unavailable in your region

```
1. Extension captures: "Not available in your region"
2. Agent fetches → Redirects to /geo-block or /unavailable
3. ⚡ Redirect detected
4. Agent uses extension's capture
5. Returns Markdown with redirect info
```

**Result:** ✅ Success! Markdown shows the geo-block message

### Agent Offline / Network Error

**Example:** Agent service not running

```
1. Extension captures page content
2. POSTs to agent → Network error (connection refused)
3. Extension catches error
4. Falls back: Downloads raw HTML file
5. Shows "Agent offline" notification
```

**Result:** ⚠️ You get HTML backup, can manually process later

---

## 📊 Technical Details

### Code Block Preservation

Markdownizer intelligently extracts and preserves code examples from documentation sites, including **automatic line number stripping** for cleaner output.

#### Extraction Strategy

Code blocks are extracted through three parallel paths:

1. **Semantic HTML Tags** - Direct extraction from `<pre>`, `<code>`, `<samp>`, `<kbd>` elements
2. **Standalone Code Blocks** - Detection of code-like patterns in isolated elements
3. **Framework-Specific Blocks** - Special handling for:
   - Prism.js (`pre.language-*`, `code.language-*`)
   - Highlight.js (`pre.hljs`, `code.hljs`)
   - Custom code containers (`div.code-block`, `div.highlight`, etc.)

#### Line Number Detection & Stripping

Many documentation sites display line numbers alongside code (e.g., "1 from typing import List", "2 ", "3 def process():"). Markdownizer automatically detects and removes these:

**Detection Algorithm:**
- Analyzes each line for leading digit patterns (`^\d+`)
- If ≥70% of lines start with digits → line numbers detected
- Threshold prevents false positives on code containing numbers

**Stripping Process:**
- Applies regex pattern: `^(\d+)(.*)$`
- Removes digit prefix while preserving the rest
- Examples:
  - `"1from typing import List"` → `"from typing import List"`
  - `"2"` → `""`
  - `"3# Comment"` → `"# Comment"`
  - `"42    result = x + y"` → `"    result = x + y"`

**Result:**
```python
# Before (with line numbers)
1from typing import List
2
3def process(items: List[str]) -> str:
4    return ", ".join(items)

# After (clean code)
from typing import List

def process(items: List[str]) -> str:
    return ", ".join(items)
```

#### Language Detection

Markdownizer preserves language hints for proper Markdown syntax highlighting:

- Extracts from `class` attributes: `language-python`, `lang-javascript`, `hljs-typescript`
- Detects common patterns: `prism-`, `highlight-`, `code-`
- Falls back to generic code blocks when language unclear

**Example Output:**
````python
```python
def example():
    pass
```
````

#### Implementation Details

All code extraction logic is in `agent/src/tools/preprocessor.py`:

- `_extract_semantic_html()` - Direct tag extraction with line number detection
- `_extract_framework_blocks()` - Framework-specific patterns with stripping
- `_has_line_numbers()` - 70% threshold detection method
- `_strip_line_numbers()` - Regex-based removal

Code blocks are injected back into HTML before Markdown conversion to preserve structure and context.

---

## �🐛 Troubleshooting

### Agent won't start

**Problem:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem:** `Failed to initialize agent with any available model`

**Solution:**

Markdownizer tries two models automatically:
1. **ConnectOnion free tier** (co/gpt-4o-mini) - 100k tokens/month, no API key needed
2. **Your OpenAI key** (fallback)

If both fail:
```bash
# Option 1: Wait a moment and retry (ConnectOnion might be temporarily down)
python main.py

# Option 2: Add your OpenAI API key to .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

The agent will automatically use whichever model is available!

### Extension not working

**Problem:** Extension shows "Agent offline"

**Solution:**
1. Check agent is running: `curl http://127.0.0.1:5050/health`
2. Verify URL in extension options matches agent host/port
3. Check firewall isn't blocking localhost:5050

**Problem:** Content script injection fails

**Solution:**
- Some pages block extensions via CSP (Content Security Policy)
- Try opening the page in a new tab
- Extension shows "CSP Blocked" notification when this happens

**Problem:** Empty or incorrect Markdown output

**Solution:**
- Check browser console for errors (F12 → Console)
- Try the page again (some dynamic content needs time to load)
- Check agent logs for extraction failures

### Comparison issues

**Problem:** Agent always chooses trafilatura over Readability

**Solution:**
- Check semantic overlap score in diagnostics
- If pages differ significantly, they might not be the same content
- Verify you're not behind a login wall (agent can't access auth'd content)

---

## 📊 API Reference

### `POST /ingest`

Convert web content to Markdown.

**Request:**
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "html_readability": "<article>...</article>",
  "text_readability": "Plain text...",
  "meta": {
    "captured_at": "2025-10-20T12:34:56Z",
    "stats": {"char_count": 8421, "headings": 6, "lists": 5},
    "iframe_info": []
  }
}
```

**Success Response (200) - Normal Comparison:**
```json
{
  "ok": true,
  "chosen": "trafilatura",
  "title": "Article Title",
  "url": "https://example.com/article",
  "markdown": "# Article Title\n\n...",
  "diagnostics": {
    "score_readability": 0.81,
    "score_trafilatura": 0.87,
    "redirect_detected": false,
    "signals": {
      "readability": {"len": 8421, "density": 0.62, "overlap": 0.94},
      "trafilatura": {"len": 9100, "density": 0.68, "overlap": 0.96}
    }
  }
}
```

**Success Response (200) - Redirect Detected:**
```json
{
  "ok": true,
  "chosen": "readability",
  "title": "Premium Article",
  "url": "https://medium.com/@author/premium-post",
  "markdown": "# Premium Article\n\nFull article content...",
  "diagnostics": {
    "score_readability": 1.0,
    "score_trafilatura": 0.0,
    "redirect_detected": true,
    "original_url": "https://medium.com/@author/premium-post",
    "final_url": "https://medium.com/login",
    "signals": {
      "readability": {"len": 12000, "density": 0.0, "overlap": 0.0},
      "trafilatura": {"len": 0, "density": 0.0, "overlap": 0.0}
    }
  }
}
```

**Error Response (200) - Rare:**
```json
{
  "ok": false,
  "code": "internal-error",
  "message": "Unexpected error during conversion: ..."
}
```

**Note:** Most scenarios that previously returned errors (redirects, blockers, fetch failures) now return **success** with the extension's captured content.

### `GET /health`

Health check endpoint.

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-10-20T12:34:56.789Z"
}
```

---

## ❓ Frequently Asked Questions

### Does Markdownizer bypass paywalls?

**No.** Markdownizer uses YOUR browser session to capture content. If you can see a page in your browser (because you're subscribed/logged in), Markdownizer will convert it. If you can't access it, neither can Markdownizer.

**What happens with paywalls:**
- You're subscribed → Extension captures full article → You get Markdown ✅
- You're not subscribed → Extension captures paywall message → You get that message ✅
- Markdownizer never tries to bypass, authenticate, or circumvent access controls

### Why does it return success even when there's a login wall?

**Philosophy:** If your browser captured content (even if it's just "Please log in"), Markdownizer converts that to Markdown and returns success. This is correct behavior—you got the Markdown of what you could see.

**Diagnostics** tell you what happened (redirect, blocker detected, etc.) so you understand the result.

### What happens when the agent fetch redirects?

**Immediate Readability choice:** If the agent's independent fetch redirects to a different URL (e.g., `/article` → `/login`), Markdownizer immediately uses your browser's captured content without comparison.

**Why?** The agent is seeing a different page than you saw, so comparison would be meaningless. Your browser's capture is the trusted source.

### Does Markdownizer need an OpenAI API key?

**No, but it helps.** Markdownizer uses ConnectOnion's **free tier** by default (100k tokens/month). If that's unavailable, it falls back to your OpenAI API key automatically.

**Cost:** Most conversions use <1k tokens, so 100k tokens = ~100-200 articles per month on free tier.

### Is my data sent to external servers?

**No.** Everything runs locally:
- Extension captures content in your browser
- Agent runs on your machine (localhost)
- API calls only go to OpenAI/ConnectOnion for LLM reasoning (not content)
- HTML content stays on your machine

### Can I use this for commercial purposes?

**Check terms of service** for sites you're converting. Markdownizer is MIT licensed (free for any use), but:
- Some sites prohibit automated access in their ToS
- Respect copyright and access controls
- Use for personal research/reading is generally fine
- Bulk scraping or republishing may violate ToS

### Why Playwright? Isn't that for web scraping?

**Not for scraping!** Playwright is only used for **blocker detection**:
- Runs headless (no UI)
- 30-second timeout (very limited)
- Only checks for login/paywall/CAPTCHA elements
- Never automates login or bypasses auth
- Most conversions never activate Playwright

### How accurate is the comparison algorithm?

**Very accurate for public content.** The scoring algorithm considers:
- Length (35%) - Longer = more complete
- Density (20%) - Text vs. HTML ratio
- Semantic overlap (20%) - Content similarity
- Structure (10%) - Headings, lists, tables
- Freshness (10%) - Date indicators
- Link quality (5%) - Internal/external links

**For auth'd content:** Comparison is skipped (redirect detection) since agent can't access the same content.

### What about JavaScript-heavy sites (SPAs)?

**Extension handles it:** The browser extension runs after JavaScript loads, so it captures the rendered content (React, Vue, Angular, etc.).

**Agent fetch:** May not see JS-rendered content (just initial HTML). That's why comparison chooses the better version, often the extension's capture for SPAs.

### Can Markdownizer handle non-English content?

**Yes!** Works with any UTF-8 content. The LLM decision-making is language-agnostic, and Markdown supports all Unicode characters.

**Redirect detection** even works with international auth pages (`/iniciar-sesion`, `/connexion`, etc.) because it detects **any** URL change, not specific keywords.

---

## 🛠️ Development

### Run in Development Mode

```bash
# Agent with auto-reload
cd agent
uvicorn main:app --reload --port 5050

# Watch logs
tail -f logs/agent.log  # if logging to file
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type checking (optional)
mypy .
```

### Adding New Tools

Follow ConnectOnion best practices:

```python
# In src/tools/my_tool.py
class MyTool:
    """Tool description."""
    
    def my_method(self, param: str) -> str:
        """Method description for LLM."""
        return f"Result: {param}"

# In app.py
from src.tools.my_tool import MyTool

my_tool = MyTool()
agent = Agent(
    ...,
    tools=[..., my_tool],  # Instance auto-discovers methods
)
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Credits

- **Mozilla Readability** - Content extraction library
- **trafilatura** - Python content extraction
- **ConnectOnion** - AI agent orchestration framework
- **markdownify** - HTML to Markdown conversion
- **FastAPI** - Modern Python web framework

---

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/Thambolo/Markdownizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Thambolo/Markdownizer/discussions)

---