"""Unit tests for web_search_tool and web_fetch_tool."""
import pytest
from unittest.mock import patch


# ── web_fetch_tool: _is_allowed_url ──────────────────────────────────────────

def test_allowed_url_tagesschau():
    from src.tools.web_fetch_tool import _is_allowed_url
    assert _is_allowed_url("https://www.tagesschau.de/inland/article.html") is True


def test_allowed_url_subdomain():
    from src.tools.web_fetch_tool import _is_allowed_url
    assert _is_allowed_url("https://www.dw.com/de/article") is True


def test_disallowed_url_example():
    from src.tools.web_fetch_tool import _is_allowed_url
    assert _is_allowed_url("https://example.com/") is False


def test_disallowed_url_internal_metadata():
    from src.tools.web_fetch_tool import _is_allowed_url
    assert _is_allowed_url("https://169.254.169.254/latest/meta-data/") is False


def test_disallowed_url_http_scheme():
    from src.tools.web_fetch_tool import _is_allowed_url
    # http:// not https:// — caught by the startswith check before _is_allowed_url
    from src.tools.web_fetch_tool import fetch_article_text
    result = fetch_article_text("http://tagesschau.de/article")
    assert "error" in result


def test_disallowed_url_empty():
    from src.tools.web_fetch_tool import fetch_article_text
    result = fetch_article_text("")
    assert "error" in result


def test_fetch_rejects_non_allowlisted_domain():
    from src.tools.web_fetch_tool import fetch_article_text
    result = fetch_article_text("https://evil.com/steal")
    assert "error" in result
    assert "allowlist" in result["error"].lower() or "Domain" in result["error"]


# ── web_fetch_tool: HTML stripping ───────────────────────────────────────────

def test_fetch_strips_html_tags():
    """fetch_article_text should strip tags and return plain text."""
    from src.tools.web_fetch_tool import fetch_article_text
    import urllib.request

    fake_html = b"""<html><head><title>Test</title>
    <script>var x = 1;</script>
    <style>body { color: red; }</style>
    </head><body><p>Hello <b>World</b>!</p></body></html>"""

    mock_response = __import__("io").BytesIO(fake_html)
    mock_response.read = lambda: fake_html

    class FakeResponse:
        def read(self): return fake_html
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch("urllib.request.urlopen", return_value=FakeResponse()), \
         patch("src.tools.web_fetch_tool._is_allowed_url", return_value=True):
        result = fetch_article_text("https://tagesschau.de/fake")

    assert "error" not in result
    assert "<script>" not in result["text"]
    assert "<style>"  not in result["text"]
    assert "<b>"      not in result["text"]
    assert "Hello"    in result["text"]
    assert "World"    in result["text"]


def test_fetch_truncates_at_6000_chars():
    from src.tools.web_fetch_tool import fetch_article_text, _MAX_CHARS

    long_html = b"<p>" + b"A" * 10000 + b"</p>"

    class FakeResponse:
        def read(self): return long_html
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch("urllib.request.urlopen", return_value=FakeResponse()), \
         patch("src.tools.web_fetch_tool._is_allowed_url", return_value=True):
        result = fetch_article_text("https://tagesschau.de/fake")

    assert len(result["text"]) <= _MAX_CHARS + 1  # +1 for the ellipsis char


# ── web_search_tool: missing API key ─────────────────────────────────────────

def test_search_returns_error_when_keys_missing():
    from src import config
    from src.tools.web_search_tool import search_german_article

    with patch.object(config, "GOOGLE_SEARCH_API_KEY", ""), \
         patch.object(config, "GOOGLE_SEARCH_CX", ""):
        result = search_german_article("Klimawandel")

    assert "error" in result


def test_search_reading_domain_filter():
    """search_german_article should include reading domains in query for source_type='reading'."""
    from src import config
    from src.tools.web_search_tool import search_german_article
    import urllib.request, json

    captured_url = []

    class FakeResponse:
        def read(self): return json.dumps({"items": [{"title": "T", "link": "https://tagesschau.de/x", "snippet": "S"}]}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(url, timeout=None):
        captured_url.append(url)
        return FakeResponse()

    with patch.object(config, "GOOGLE_SEARCH_API_KEY", "key"), \
         patch.object(config, "GOOGLE_SEARCH_CX", "cx"), \
         patch("urllib.request.urlopen", fake_urlopen):
        result = search_german_article("Klimawandel", source_type="reading")

    assert result.get("url") == "https://tagesschau.de/x"
    assert "tagesschau.de" in captured_url[0]


def test_search_listening_domain_filter():
    from src import config
    from src.tools.web_search_tool import search_german_article
    import json

    captured_url = []

    class FakeResponse:
        def read(self): return json.dumps({"items": [{"title": "T", "link": "https://dw.com/ep", "snippet": "S"}]}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(url, timeout=None):
        captured_url.append(url)
        return FakeResponse()

    with patch.object(config, "GOOGLE_SEARCH_API_KEY", "key"), \
         patch.object(config, "GOOGLE_SEARCH_CX", "cx"), \
         patch("urllib.request.urlopen", fake_urlopen):
        result = search_german_article("Podcast", source_type="listening")

    assert result.get("url") == "https://dw.com/ep"
    assert "dw.com" in captured_url[0]
    assert "tagesschau" not in captured_url[0]
