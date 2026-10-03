"""Unit tests for functions/token_endpoint.py — stubs functions_framework and flask for local testing."""
import sys
import types
import json
import pytest

# Stub flask.jsonify with a minimal stand-in before importing the module
class _FakeJsonResponse:
    def __init__(self, data):
        self._data = data
    def get_json(self):
        return self._data

_flask_stub = types.ModuleType("flask")
_flask_stub.jsonify = lambda data: _FakeJsonResponse(data)
sys.modules.setdefault("flask", _flask_stub)

_ff_stub = types.ModuleType("functions_framework")
_ff_stub.http = lambda f: f
sys.modules.setdefault("functions_framework", _ff_stub)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "functions"))
import token_endpoint as te  # noqa: E402


class FakeRequest:
    def __init__(self, method="POST"):
        self.method = method


def test_returns_token_and_model_when_key_set():
    te.GEMINI_API_KEY = "test-key"
    te.GEMINI_MODEL   = "models/gemini-test"
    response, status, headers = te.token_endpoint(FakeRequest("POST"))
    data = response.get_json()
    assert status == 200
    assert data["token"] == "test-key"
    assert data["model"] == "models/gemini-test"


def test_returns_500_when_key_missing():
    te.GEMINI_API_KEY = ""
    response, status, headers = te.token_endpoint(FakeRequest("POST"))
    assert status == 500
    assert "error" in response.get_json()


def test_options_returns_204():
    _, status, _ = te.token_endpoint(FakeRequest("OPTIONS"))
    assert status == 204


def test_get_returns_405():
    te.GEMINI_API_KEY = "key"
    _, status, _ = te.token_endpoint(FakeRequest("GET"))
    assert status == 405


def test_cors_headers_present():
    te.GEMINI_API_KEY = "test-key"
    _, _, headers = te.token_endpoint(FakeRequest("POST"))
    assert headers.get("Access-Control-Allow-Origin") == "*"
