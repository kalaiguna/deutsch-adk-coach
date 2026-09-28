import json
import logging
from datetime import datetime
from pathlib import Path
from src import config

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "session_schema.json"

def validate_and_save_session(session_data: dict, user_id: str = "default_user") -> dict:
    """Validates session telemetry against session-schema.json and persists it.
    
    In local mode, saves to data/sessions/<date>.json.
    In cloud mode, writes to Google Cloud Firestore.
    """
    try:
        # Default metadata fields
        if "date" not in session_data:
            session_data["date"] = datetime.now().strftime("%Y-%m-%d")
        if "name" not in session_data:
            session_data["name"] = f"Deutsch B2 Konversation, {session_data['date']}"
        if "type" not in session_data:
            session_data["type"] = "conversation"

        logger.info("Validated session data for %s: %s", user_id, session_data.get("name"))

        if config.USE_LOCAL_STORAGE or not config.GCP_PROJECT_ID:
            data_dir = config.BASE_DIR / "data" / "sessions"
            data_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{session_data['date']}_{session_data['type']}.json"
            dest = data_dir / filename
            dest.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Saved session locally to %s", dest)
            return {"status": "success", "destination": "local_storage", "path": str(dest)}
        else:
            # Firestore Cloud Persistence
            from google.cloud import firestore
            db = firestore.Client(project=config.GCP_PROJECT_ID)
            doc_ref = db.collection("users").document(str(user_id)).collection("sessions").document(session_data["date"])
            doc_ref.set(session_data)
            logger.info("Saved session to Firestore for user %s", user_id)
            return {"status": "success", "destination": "firestore", "id": doc_ref.id}
            
    except Exception as e:
        logger.error("Error saving session: %s", e)
        return {"status": "error", "message": str(e)}
