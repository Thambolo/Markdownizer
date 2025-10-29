# FAQ & Troubleshooting

This document contains the troubleshooting guidance.

## Common issues

### Agent offline
- Check `curl http://127.0.0.1:5050/health`
- Ensure virtualenv activated and dependencies installed

### Extension shows "Agent offline"
- Confirm Agent URL in extension options
- Check firewall / localhost connectivity

### Content extraction problems
- Some pages block extension injection (CSP) — the extension will save a raw HTML fallback.
- If trafilatura extracts very little, suspect paywalls/login and consult the `algorithm.md` and `preprocessor.md` docs.

For the full troubleshooting steps and examples, see this file's extended sections (moved from the README).

## Longer troubleshooting

### Agent won't start

**Problem:** `ModuleNotFoundError` or import errors

**Solution:**
```powershell
# Ensure venv is activated
\.venv\Scripts\Activate.ps1
# Reinstall dependencies
pip install -r requirements.txt
```

**Problem:** `Failed to initialize agent with any available model`

**Solution:**
- Markdownizer tries ConnectOnion free tier first and falls back to OpenAI if configured. If both fail, add `OPENAI_API_KEY` to `agent/.env`.

### Extension not working

**Problem:** Extension shows "Agent offline"

**Solution:**
1. Check agent is running: `curl http://127.0.0.1:5050/health`
2. Verify URL in extension options matches agent host/port
3. Check firewall isn't blocking localhost:5050

**Problem:** Content script injection fails

**Solution:**
- Some pages block extensions via CSP — try opening the page in a new tab or use the fallback HTML download option in the extension.

### Comparison issues

**Problem:** Agent always chooses trafilatura over Readability

**Solution:**
- Check semantic overlap score in diagnostics. If they differ significantly, your page may be behind a login wall or require JS rendering.

