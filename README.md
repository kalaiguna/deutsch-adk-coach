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

## Project Evolution & Attribution

This project is the culmination of a 3-stage evolution in AI-assisted language learning:

### 1️⃣ Foundational Pedagogy & Prompts (v1.0.0)
* **Author:** [Mohga Nabil](https://github.com/MohgaNabil/deutsch-lernpaket)
* **Scope & Stack:** Created the original 3 prompt skills (`daily-german-practice`, `german-weekend-review`, `german-sunday-schreiben-und-hoeren`), tightly coupled to **Claude** and macOS-only **Apple Notes MCP**.
* **Core Contribution:** Established core B2 pedagogical design rules (bilingual 🇩🇪/🇬🇧 chat rhythm, 10-category mistake taxonomy, mandatory `B2-Umformulierung`, and 1-2 questions per turn).

### 2️⃣ Cross-Platform System, Notion Telemetry & 7-Skill Framework (v2.0.0)
* **Author:** [Gunasekaran Chandrasekaran](https://github.com/kalaiguna/deutsch-lernpaket)
* **Scope & Stack:** Re-architected for universal **Cross-Platform & Cross-Agent** support (Google Antigravity IDE, Claude Code, Copilot, Roo Code, OpenWebUI, n8n across Windows, Android, and macOS).
* **Core Contribution:** 
  * Replaced Apple Notes with **Notion MCP** and machine-readable `session_schema.json` telemetry.
  * Expanded from 3 to **7 specialized skills** (`schreib-skill`, `lektuere-skill`, `monatsrueckblick`, `grammatik-vertiefung`).
  * Built the interactive progress dashboard (heatmaps, streak tracking, vocabulary explorer, sticky micro-drills) and added dictation error detection.

### 3️⃣ Autonomous Agent Engine & Telegram Bot (`deutsch-adk-coach`)
* **Author:** Gunasekaran Chandrasekaran
* **Scope & Stack:** Re-engineered from prompt-based MCP skills into an autonomous, event-driven agent architecture.
* **Core Contribution:**
  * Built with **Google Agent Development Kit (ADK)** and the **Gemini 3.6 Multimodal API** (`google-genai`).
  * Native Telegram `.ogg` Opus voice note processing (direct audio comprehension, eliminating manual dictation/transcription).
  * Asynchronous **Telegram Bot** with per-user concurrency locking (`asyncio.Lock`).
  * Dual-destination telemetry (Cloud Firestore & local JSON) and automated Google Cloud Run / Scheduler triggers.

---

## License & History

* See [CHANGELOG.md](CHANGELOG.md) for version release notes.
* Licensed under the [MIT License](LICENSE).
