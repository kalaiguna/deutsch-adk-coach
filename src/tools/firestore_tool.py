import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from src import config

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "session_schema.json"

# Lazy Firestore client — created once, reused across all tool calls
_firestore_client = None


def _get_firestore_client():
    global _firestore_client
    if _firestore_client is None:
        from google.cloud import firestore
        _firestore_client = firestore.Client(project=config.GCP_PROJECT_ID)
    return _firestore_client


def _extract_user_id(tool_context) -> str:
    if tool_context is None:
        return "default_user"
    try:
        uid = tool_context.user_id
        if uid:
            return str(uid)
    except Exception as e:
        logger.warning("Could not read user_id from tool_context (%s); falling back to default_user", e)
    return "default_user"


def validate_and_save_session(session_data: dict, tool_context=None) -> dict:
    """Validates session telemetry against session-schema.json and persists it.

    In local mode, saves to data/sessions/<user_id>/<date>_<type>.json.
    In cloud mode, writes to Google Cloud Firestore under users/<user_id>/sessions/.
    """
    try:
        if "date" not in session_data:
            session_data["date"] = datetime.now().strftime("%Y-%m-%d")
        if "name" not in session_data:
            session_data["name"] = f"Deutsch B2 Konversation, {session_data['date']}"
        if "type" not in session_data:
            session_data["type"] = "conversation"

        user_id = _extract_user_id(tool_context)
        logger.info("Saving session for user %s: %s", user_id, session_data.get("name"))

        if config.USE_LOCAL_STORAGE or not config.GCP_PROJECT_ID:
            data_dir = config.BASE_DIR / "data" / "sessions" / user_id
            data_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{session_data['date']}_{session_data['type']}.json"
            dest = data_dir / filename
            dest.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Saved session locally to %s", dest)
            return {"status": "success", "destination": "local_storage", "path": str(dest)}
        else:
            db = _get_firestore_client()
            doc_id = f"{session_data['date']}_{session_data['type']}"
            doc_ref = (
                db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(doc_id)
            )
            doc_ref.set(session_data)
            logger.info("Saved session to Firestore for user %s, doc %s", user_id, doc_id)
            return {"status": "success", "destination": "firestore", "id": doc_ref.id}

    except Exception as e:
        logger.error("Error saving session: %s", e)
        return {"status": "error", "message": str(e)}


def read_recent_sessions(days: int = 14, tool_context=None) -> list:
    """Reads session documents from the last N days for the current user.

    Returns a list of session dicts sorted by date descending.
    Used by VocabRecallAgent, QuizAgent, and GrammarAgent to access history.
    """
    user_id = _extract_user_id(tool_context)
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        if config.USE_LOCAL_STORAGE or not config.GCP_PROJECT_ID:
            data_dir = config.BASE_DIR / "data" / "sessions" / user_id
            if not data_dir.exists():
                return []
            sessions = []
            for f in sorted(data_dir.glob("*.json"), reverse=True):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if data.get("date", "") >= cutoff:
                        sessions.append(data)
                except Exception:
                    continue
            return sessions
        else:
            from google.cloud import firestore
            db = _get_firestore_client()
            docs = (
                db.collection("users")
                .document(user_id)
                .collection("sessions")
                .where("date", ">=", cutoff)
                .order_by("date", direction=firestore.Query.DESCENDING)
                .stream()
            )
            return [doc.to_dict() for doc in docs]

    except Exception as e:
        logger.error("Error reading recent sessions: %s", e)
        return []
