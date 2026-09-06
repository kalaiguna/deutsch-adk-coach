# Deutsch ADK Coach 🇩🇪🤖

AI German B2 Language Coach powered by **Google Agent Development Kit (ADK)** / **Gemini 3.6 Multimodal**, and **Telegram Bot**.

---

## Architecture Overview

* **Agent Engine:** Stateful conversation agent built with the Google GenAI SDK (`google-genai`) and Gemini 3.6.
* **Mobile Interface:** Telegram Bot (`python-telegram-bot`) supporting typed text and native `.ogg` voice notes.
* **Audio & Multimodal:** Gemini native audio processing (`audio/ogg` Opus) for speaking feedback and pronunciation analysis.
* **Telemetry & Storage:** Cloud Firestore (or local JSON) conforming strictly to `session_schema.json`.
* **Deployment:** Containerized on Google Cloud Run with Cloud Scheduler triggers.

---

## Directory Structure

```
deutsch-adk-coach/
├── src/
│   ├── main.py                 # Telegram Bot entry point with concurrency locking & user auth
│   ├── config.py               # Environment & agent settings
│   ├── agents/
│   │   ├── conversation.py     # Stateful B2 speaking & chat partner
│   │   └── prompts.py          # B2 pedagogical system prompts
│   ├── tools/
│   │   ├── firestore_tool.py   # Schema validation & session persistence
│   │   └── voice_tool.py       # Audio note processing for Gemini
│   └── schemas/
│       └── session_schema.json # Telemetry contract
├── test_agent_cli.py           # Standalone local test runner (no Telegram required)
├── Dockerfile                  # Production container for Cloud Run
├── requirements.txt            # Python dependencies
└── deploy/
    ├── cloud-run.yaml          # Cloud Run service specification
    └── scheduler.yaml          # Scheduled 9 AM practice triggers
```

---

## Quickstart (Local Testing)

### 1. Prerequisites
* Python 3.11+
* A Gemini API key (via Google AI Studio or Google Cloud Vertex AI)
* A Telegram Bot Token (created via [@BotFather](https://t.me/BotFather))

### 2. Setup & Environment
```bash
# Clone or navigate into directory
cd deutsch-adk-coach

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows (or source venv/bin/activate on Linux/macOS)

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env   # On Windows (or cp .env.example .env on Linux/macOS)
```

Edit `.env` and set the required variables:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional: Override Gemini Model (default: gemini-3.6-flash)
GEMINI_MODEL=gemini-3.6-flash

# Optional: Restrict bot to specific Telegram User IDs (comma-separated)
ALLOWED_TELEGRAM_USERS=123456789
```

---

### 3. Test Agent via Terminal (No Telegram Needed)
Test the agent logic interactively in your command line:
```bash
python test_agent_cli.py
```

---

### 4. Run Telegram Bot Locally
Start the bot using long-polling (no public domain or ngrok tunnel required):

```bash
python -m src.main
```

1. Open **Telegram** on mobile or desktop and search for your bot.
2. Send `/start` to begin a B2 conversation session.
3. You can interact via:
   * **Typed Text:** Send German text messages for grammar evaluation, error categorization, and `B2-Umformulierung` reformulations.
   * **Voice Notes:** Record native Telegram voice notes (`.ogg` Opus). The bot transcribes and analyzes spoken German directly via Gemini Multimodal.
4. To stop the bot, press `Ctrl + C` in the terminal.

---

## Acknowledgements & Attribution

This project is the evolution of a multi-stage B2 German learning framework:

* **Foundational Pedagogy & Prompts ([v1.0.0](https://github.com/MohgaNabil/deutsch-lernpaket)):** Created by **Mohga Nabil**, defining the core B2 pedagogical design principles (bilingual 🇩🇪/🇬🇧 chat rhythm, 10 mistake categories, mandatory `B2-Umformulierung`, and original prompt concepts).
* **Framework, Telemetry & Multi-Skill Expansion ([v2.0.0](https://github.com/kalaiguna/deutsch-lernpaket)):** Built by **Gunasekaran Chandrasekaran**, migrating to Notion MCP, creating 4 additional specialized skills (`schreib-skill`, `lektuere-skill`, `monatsrueckblick`, `grammatik-vertiefung`), introducing the machine-readable `session_schema.json` telemetry contract, and building the interactive progress dashboard.
* **Agent Engine & Telegram Bot (`deutsch-adk-coach`):** Re-engineered by **Gunasekaran Chandrasekaran** into an autonomous, event-driven architecture powered by **Google Agent Development Kit (ADK)**, native **Gemini 3.6 Multimodal API** (direct Opus `.ogg` voice note processing), and **Telegram Bot** concurrency-locked session runner.

---

## License & History

* See [CHANGELOG.md](CHANGELOG.md) for version release notes.
* Licensed under the [MIT License](LICENSE).
