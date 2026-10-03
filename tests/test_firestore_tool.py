"""Unit tests for src/tools/firestore_tool.py — local storage path, user ID extraction, defaults."""
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── _extract_user_id ──────────────────────────────────────────────────────────

def test_extract_user_id_none_returns_default():
    from src.tools.firestore_tool import _extract_user_id
    assert _extract_user_id(None) == "default_user"


def test_extract_user_id_from_context():
    from src.tools.firestore_tool import _extract_user_id
    ctx = MagicMock()
    ctx.user_id = "user_42"
    assert _extract_user_id(ctx) == "user_42"


def test_extract_user_id_empty_string_falls_back():
    from src.tools.firestore_tool import _extract_user_id
    ctx = MagicMock()
    ctx.user_id = ""
    assert _extract_user_id(ctx) == "default_user"


def test_extract_user_id_attribute_error_falls_back():
    from src.tools.firestore_tool import _extract_user_id
    ctx = MagicMock(spec=[])  # no user_id attribute
    assert _extract_user_id(ctx) == "default_user"


# ── validate_and_save_session (local storage) ─────────────────────────────────

def test_save_session_local_creates_file(tmp_path):
    from src import config
    from src.tools.firestore_tool import validate_and_save_session

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        result = validate_and_save_session({
            "date": "2026-10-01",
            "type": "conversation",
            "name": "Test Session",
            "mistakes": [],
            "vocab_review_misses": [],
        })

    assert result["status"] == "success"
    assert result["destination"] == "local_storage"
    saved = Path(result["path"])
    assert saved.exists()
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["type"] == "conversation"
    assert data["date"] == "2026-10-01"


def test_save_session_fills_defaults(tmp_path):
    from src import config
    from src.tools.firestore_tool import validate_and_save_session

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        result = validate_and_save_session({})

    assert result["status"] == "success"
    saved = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
    assert "date" in saved
    assert saved["type"] == "conversation"
    assert "name" in saved


def test_save_session_per_user_isolation(tmp_path):
    from src import config
    from src.tools.firestore_tool import validate_and_save_session

    ctx_a = MagicMock(); ctx_a.user_id = "alice"
    ctx_b = MagicMock(); ctx_b.user_id = "bob"

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        r_a = validate_and_save_session({"date": "2026-10-01", "type": "vocab"}, tool_context=ctx_a)
        r_b = validate_and_save_session({"date": "2026-10-01", "type": "quiz"}, tool_context=ctx_b)

    assert "alice" in r_a["path"]
    assert "bob"   in r_b["path"]
    assert r_a["path"] != r_b["path"]


# ── read_recent_sessions (local storage) ──────────────────────────────────────

def test_read_recent_sessions_returns_within_window(tmp_path):
    from src import config
    from src.tools.firestore_tool import read_recent_sessions

    recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    user_dir = tmp_path / "data" / "sessions" / "default_user"
    user_dir.mkdir(parents=True)
    recent = {"date": recent_date, "type": "conversation"}
    old    = {"date": "2020-01-01", "type": "conversation"}
    (user_dir / f"{recent_date}_conversation.json").write_text(json.dumps(recent), encoding="utf-8")
    (user_dir / "2020-01-01_conversation.json").write_text(json.dumps(old), encoding="utf-8")

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        sessions = read_recent_sessions(days=14)

    assert len(sessions) == 1
    assert sessions[0]["date"] == recent_date


def test_read_recent_sessions_empty_dir_returns_empty(tmp_path):
    from src import config
    from src.tools.firestore_tool import read_recent_sessions

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        sessions = read_recent_sessions(days=14)

    assert sessions == []


def test_read_recent_sessions_skips_corrupt_json(tmp_path):
    from src import config
    from src.tools.firestore_tool import read_recent_sessions

    recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    older_date  = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
    user_dir = tmp_path / "data" / "sessions" / "default_user"
    user_dir.mkdir(parents=True)
    (user_dir / f"{older_date}_conversation.json").write_text("{bad json", encoding="utf-8")
    (user_dir / f"{recent_date}_vocab.json").write_text(json.dumps({"date": recent_date, "type": "vocab"}), encoding="utf-8")

    with patch.object(config, "USE_LOCAL_STORAGE", True), \
         patch.object(config, "BASE_DIR", tmp_path):
        sessions = read_recent_sessions(days=14)

    assert len(sessions) == 1
    assert sessions[0]["type"] == "vocab"
