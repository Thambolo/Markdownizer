# Project structure

This file lists the repository structure.

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
│       └── vendor/
│           └── readability.js # Mozilla Readability
├── shared/
│   └── protocol.json          # API contract
├── docs/                      # Developer & user documentation
│   ├── architecture.md        # Architecture diagram & flow
│   ├── algorithm.md           # Decision algorithm & scoring
│   ├── preprocessor.md        # Code block preprocessing details
│   ├── FAQ.md                 # Troubleshooting & FAQ
│   └── project_structure.md   # This file
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
├── setup.ps1                  # Download Readability.js (Windows)
├── README.md
├── QUICKSTART.md              # 5-minute setup guide
├── LICENSE
└── .gitignore
```
