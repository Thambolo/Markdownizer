# Tests

This file consolidates the test-related information.

Run the test suite:

```bash
cd agent
pytest tests/ -v
```

Coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

Key test areas:
- comparator (scoring algorithm and tie-breaking)
- extractor (trafilatura extraction and Markdown conversion)
- preprocessor (code block handling and placeholders)
- blockers (Playwright-based detection, mocked in tests)

See the `agent/tests/` directory for the actual test files.
