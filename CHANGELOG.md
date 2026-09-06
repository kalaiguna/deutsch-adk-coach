# Changelog

All notable changes to the **Deutsch ADK Coach** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-06

Initial release of **Deutsch ADK Coach**, re-engineering the B2 German Learning framework into an event-driven AI agent architecture powered by Google Cloud & Gemini.

### Added
- **Google Agent Engine (`ConversationAgent`)**: Multi-turn B2 conversation stateful agent built using the `google-genai` SDK and `gemini-3.6-flash`.
- **Telegram Bot Interface (`src/main.py`)**: Asynchronous Telegram bot (`python-telegram-bot`) using long-polling with per-user concurrency locking (`asyncio.Lock`) to prevent race conditions and out-of-order responses.
- **Multimodal Voice Note Processing (`src/tools/voice_tool.py`)**: Direct Telegram `.ogg` Opus audio note ingestion into Gemini 3.6 for transcription, grammar correction, and audio feedback.
- **Schema-Validated Telemetry (`src/tools/firestore_tool.py`)**: Dual-destination session telemetry system conforming strictly to `session_schema.json`, saving either locally (`data/sessions/`) or directly to Google Cloud Firestore.
- **Standalone CLI Test Runner (`test_agent_cli.py`)**: Local terminal runner allowing instant testing of agent conversation logic without requiring Telegram setup.
- **Cloud Run & Scheduler Deployment Specs (`deploy/`)**: Docker containerization (`Dockerfile`) with Knative Cloud Run manifest (`cloud-run.yaml`) and Cloud Scheduler triggers (`scheduler.yaml`) for automated morning practice sessions.
- **Access Control**: Optional security filtering (`ALLOWED_TELEGRAM_USERS`) to restrict bot usage to authorized Telegram user IDs.

---

### Historical Evolution
- **v2.0.0 (deutsch-lernpaket fork)**: Introduced Notion MCP integration, 7 specialized skills, machine-readable `session_schema.json`, and progress dashboard.
- **v1.0.0 (original concept)**: Created by Mohga Nabil with 3 core prompt skills and foundational B2 pedagogical design rules.
