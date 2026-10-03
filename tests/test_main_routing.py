"""Unit tests for routing helpers in src/main.py."""
import pytest
from unittest.mock import MagicMock, patch
from google.genai import types


# ── _voice_content dispatch ───────────────────────────────────────────────────

def _get_voice_content(mode: str, audio: bytes = b"fake"):
    from src.main import _voice_content
    return _voice_content(audio, mode)


def test_voice_content_conversation_mode():
    content = _get_voice_content("conversation")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "B2-Umformulierung" in instruction
    assert "Transcribe" in instruction


def test_voice_content_quiz_mode():
    content = _get_voice_content("quiz")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "quiz answer" in instruction


def test_voice_content_grammar_mode():
    content = _get_voice_content("grammar")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "grammar exercise answer" in instruction


def test_voice_content_exam_mode():
    content = _get_voice_content("exam")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "spoken exam answer" in instruction


def test_voice_content_lekture_mode():
    content = _get_voice_content("lekture")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "reading or listening" in instruction


def test_voice_content_hoeren_mode():
    content = _get_voice_content("hoeren")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "reading or listening" in instruction


def test_voice_content_vocab_mode_falls_to_else():
    content = _get_voice_content("vocab")
    instruction = next(p.text for p in content.parts if hasattr(p, "text") and p.text)
    assert "drill answer" in instruction


def test_voice_content_includes_audio_part():
    content = _get_voice_content("conversation", b"\x00\x01\x02")
    audio_parts = [p for p in content.parts if not (hasattr(p, "text") and p.text)]
    assert len(audio_parts) == 1


# ── session ID helpers ────────────────────────────────────────────────────────

def test_get_or_create_session_id_stable():
    from src.main import get_or_create_session_id, user_session_ids
    user_session_ids.clear()
    sid1 = get_or_create_session_id(999, "conversation")
    sid2 = get_or_create_session_id(999, "conversation")
    assert sid1 == sid2
    assert "conversation" in sid1
    assert "999" in sid1


def test_get_or_create_session_id_different_modes():
    from src.main import get_or_create_session_id, user_session_ids
    user_session_ids.clear()
    sid_conv = get_or_create_session_id(999, "conversation")
    sid_vocab = get_or_create_session_id(999, "vocab")
    assert sid_conv != sid_vocab


def test_reset_session_id_creates_new():
    from src.main import get_or_create_session_id, reset_session_id, user_session_ids
    user_session_ids.clear()
    sid_old = get_or_create_session_id(999, "quiz")
    sid_new = reset_session_id(999, "quiz")
    assert sid_new != sid_old
    # After reset, get_or_create returns the new one
    assert get_or_create_session_id(999, "quiz") == sid_new


def test_reset_session_id_is_timestamped():
    from src.main import reset_session_id, user_session_ids
    user_session_ids.clear()
    sid = reset_session_id(42, "grammar")
    parts = sid.split("_")
    assert parts[0] == "grammar"
    assert parts[1] == "42"
    assert parts[2].isdigit()


# ── is_authorized ─────────────────────────────────────────────────────────────

def test_is_authorized_no_allowlist_permits_all():
    from src import config
    from src.main import is_authorized
    with patch.object(config, "ALLOWED_TELEGRAM_USERS", []):
        assert is_authorized(12345) is True


def test_is_authorized_with_allowlist_permits_known():
    from src import config
    from src.main import is_authorized
    with patch.object(config, "ALLOWED_TELEGRAM_USERS", [111, 222]):
        assert is_authorized(111) is True


def test_is_authorized_with_allowlist_blocks_unknown():
    from src import config
    from src.main import is_authorized
    with patch.object(config, "ALLOWED_TELEGRAM_USERS", [111, 222]):
        assert is_authorized(999) is False
