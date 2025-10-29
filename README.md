<p align="center">
  <a href="https://github.com/Thambolo/Markdownizer/actions">
    <img src="https://github.com/Thambolo/Markdownizer/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT" />
  </a>
  <a href="https://github.com/Thambolo/Markdownizer/commits/main">
    <img src="https://img.shields.io/github/last-commit/Thambolo/Markdownizer.svg?style=flat-square" alt="GitHub last commit" />
  </a>
</p>

# Markdownizer

AI-powered Web → Markdown conversion. A local browser extension captures user-visible content (including authenticated pages) and a local agent compares multiple extractions to produce high-quality Markdown.

## Key features

- Smart extraction (browser Readability vs agent trafilatura)
- Auth‑aware capture (works with pages you can see in the browser)
- Blocker detection (paywall/login/captcha detection, no bypass)
- Code block preservation and language hints
- Local-first processing (no external scraping)

## Prerequisites

- Python 3.11+
- Chrome or Edge
- Git

## Install the Agent Service

```powershell
# Clone the repository
git clone https://github.com/Thambolo/Markdownizer.git
cd Markdownizer

# Download Readability.js (Windows PowerShell)
.\setup.ps1

# Navigate to agent directory
cd agent

# Create virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (optional)
playwright install chromium

# Copy example env
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or [use connectonion's free  100k tokens](https://docs.connectonion.com/models)
```

## Start the agent

```powershell
cd agent
.\start.ps1
# or
uvicorn main:app --reload --port 5050
```

## Install the browser extension

1. Open `chrome://extensions` (Chrome/Edge)
2. Enable Developer mode
3. Click "Load unpacked" and select `extension/src`

## Where to find more details

- Decision algorithm & scoring: `docs/algorithm.md`
- Code block handling and preprocessing: `docs/preprocessor.md`
- Architecture & flow: `docs/architecture.md`
- Troubleshooting and FAQ: `docs/FAQ.md`
- Tests: `TESTS.md`

## Minimal troubleshooting

- If the extension shows "Agent offline": check `uvicorn`/agent is running and the Agent URL in extension options.
- If Markdown output is empty/short: agent may have hit a paywall; check `docs/FAQ.md`.

## Contributing & license

Contributions welcome — see the repository and tests. Licensed MIT. See `LICENSE` for details.
