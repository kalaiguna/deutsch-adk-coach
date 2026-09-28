import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"

ALLOWED_USERS_RAW = os.getenv("ALLOWED_TELEGRAM_USERS", "")
ALLOWED_TELEGRAM_USERS = [int(x.strip()) for x in ALLOWED_USERS_RAW.split(",") if x.strip().isdigit()]

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.6-pro")
