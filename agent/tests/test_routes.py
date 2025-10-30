import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


@pytest.fixture
def base_payload():
    return {
        "url": "https://example.com/article",
        "title": "Example Article",
        "html_extension": "<article><h1>Example</h1><p>ext</p></article>",
        "text_extension": "Example ext",
        "meta": {
            "captured_at": "2025-10-20T12:34:56Z",
            "stats": {"char_count": 1000, "headings": 2, "lists": 0},
            "iframe_info": [],
        },
    }


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"


def test_ingest_fetch_failure_uses_extension(monkeypatch, base_payload):
    # Simulate fetcher failure
    monkeypatch.setattr(main.fetcher, "fetch_url", lambda url: {"success": False, "error": "neterr"})

    # Ensure markdown conversion is predictable
    monkeypatch.setattr(main.extractor, "convert_to_markdown", lambda html, title, url: "MD_FROM_EXTENSION")
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "extension"
    assert "MD_FROM_EXTENSION" in j["markdown"]
    assert j["diagnostics"]["score_extension"] == 1.0


def test_ingest_redirect_uses_extension(monkeypatch, base_payload):
    # Simulate successful fetch but with redirect
    def fake_fetch(url):
        return {
            "success": True,
            "html": "<html></html>",
            "was_redirected": True,
            "original_url": url,
            "final_url": url + "/login",
        }

    monkeypatch.setattr(main.fetcher, "fetch_url", fake_fetch)
    monkeypatch.setattr(main.extractor, "convert_to_markdown", lambda html, title, url: "MD_FROM_EXTENSION_REDIRECT")
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "extension"
    assert "MD_FROM_EXTENSION_REDIRECT" in j["markdown"]


def test_redirect_includes_diagnostics(monkeypatch, base_payload):
    # Same redirect scenario but assert diagnostic fields are present
    def fake_fetch(url):
        return {
            "success": True,
            "html": "<html></html>",
            "was_redirected": True,
            "original_url": url,
            "final_url": url + "/login",
        }

    monkeypatch.setattr(main.fetcher, "fetch_url", fake_fetch)
    monkeypatch.setattr(main.extractor, "convert_to_markdown", lambda html, title, url: "MD_REDIRECT")
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "extension"
    assert j["diagnostics"]["redirect_detected"] is True
    assert j["diagnostics"]["original_url"].endswith("/article")
    assert j["diagnostics"]["final_url"].endswith("/article/login")


def test_blocker_probe_prefers_extension(monkeypatch, base_payload):
    # Simulate trafilatura extraction that is very short so probe runs
    monkeypatch.setattr(main.fetcher, "fetch_url", lambda url: {"success": True, "html": "<html>v</html>", "was_redirected": False})
    monkeypatch.setattr(
        main.extractor,
        "extract_with_trafilatura",
        lambda html, url: {"success": True, "html": "<p>v</p>", "text": "v", "char_count": 50},
    )

    # Mock the playwright probe to report a paywall
    monkeypatch.setattr(main.playwright_probe, "detect_blockers", lambda url: {"paywall": True})

    monkeypatch.setattr(main.extractor, "convert_to_markdown", lambda html, title, url: "MD_FROM_EXTENSION_BLOCKER")
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "extension"
    assert "MD_FROM_EXTENSION_BLOCKER" in j["markdown"]


def test_ingest_trafilatura_choice(monkeypatch, base_payload):
    # fetcher returns success
    monkeypatch.setattr(main.fetcher, "fetch_url", lambda url: {"success": True, "html": "<html>agent</html>", "was_redirected": False})

    # extractor.extract_with_trafilatura returns successful extraction
    monkeypatch.setattr(
        main.extractor,
        "extract_with_trafilatura",
        lambda html, url: {"success": True, "html": "<p>agent</p>", "text": "agent", "char_count": 1200},
    )

    # comparator chooses trafilatura
    monkeypatch.setattr(
        main.comparator,
        "compare_and_decide",
        lambda **kw: {
            "chosen": "trafilatura",
            "score_extension": 0.55,
            "score_trafilatura": 0.9,
            "signals_extension": {"len": 1000, "density": 0.5, "overlap": 0.8},
            "signals_trafilatura": {"len": 1200, "density": 0.6, "overlap": 0.9},
        },
    )

    monkeypatch.setattr(main.extractor, "convert_to_markdown", lambda html, title, url: "MD_FROM_TRAFILATURA")
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)
    monkeypatch.setattr(main.normalizer, "normalize_links", lambda md, url: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "trafilatura"
    assert "MD_FROM_TRAFILATURA" in j["markdown"]
    assert j["diagnostics"]["score_trafilatura"] == pytest.approx(0.9)


def test_ingest_extension_choice(monkeypatch, base_payload):
    # fetcher returns success and agent extraction exists
    monkeypatch.setattr(main.fetcher, "fetch_url", lambda url: {"success": True, "html": "<html>agent</html>", "was_redirected": False})

    monkeypatch.setattr(
        main.extractor,
        "extract_with_trafilatura",
        lambda html, url: {"success": True, "html": "<p>agent</p>", "text": "agent", "char_count": 1200},
    )

    # comparator chooses extension
    monkeypatch.setattr(
        main.comparator,
        "compare_and_decide",
        lambda **kw: {
            "chosen": "extension",
            "score_extension": 0.95,
            "score_trafilatura": 0.4,
            "signals_extension": {"len": 2000, "density": 0.7, "overlap": 0.95},
            "signals_trafilatura": {"len": 1200, "density": 0.6, "overlap": 0.7},
        },
    )

    # When extension chosen, convert_to_markdown should be called with extension HTML
    def fake_convert(html, title, url):
        assert "<article" in html or "ext" in html
        return "MD_EXT_CHOSEN"

    monkeypatch.setattr(main.extractor, "convert_to_markdown", fake_convert)
    monkeypatch.setattr(main.extractor, "fix_fragmented_code_blocks", lambda md: md)
    monkeypatch.setattr(main.normalizer, "normalize_links", lambda md, url: md)

    r = client.post("/ingest", json=base_payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["chosen"] == "extension"
    assert "MD_EXT_CHOSEN" in j["markdown"]


def test_ingest_validation_error(base_payload):
    # Remove required field to trigger validation error
    payload = base_payload.copy()
    del payload["url"]
    r = client.post("/ingest", json=payload)
    assert r.status_code == 422
