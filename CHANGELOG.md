# Changelog

All notable changes to **deutsch-adk-coach** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned — v1.1.0
- `read_recent_sessions(user_id, days)` in `firestore_tool.py`
- `vocab_review_misses: string[]` field in `session_schema.json`
- `VocabRecallAgent` — SRS-style drill from recent session misses
- `/vocab` Telegram command

### Planned — v1.2.0
- `QuizAgent` with Fehler-Rewind (mistake-weighted questions) and Sticky Challenge (3-question micro-drill for recurring errors)
- `/quiz` Telegram command + Friday 09:00 Berlin Cloud Scheduler cron

### Planned — v1.3.0
- `MonatsrueckblickAgent` — monthly Firestore aggregation, 3 focus areas output
- `GrammarAgent` — 12-topic monthly rotation, reads Monatsrückblick for topic selection
- `/bericht` command + 1st-of-month cron
- `/grammatik` command + 10th-of-month cron

### Planned — v1.4.0
- `ExamPrepAgent` — mock telc B2 with /45 Schreiben rubric, Sprechen scaffolds, Trap Drill
- `/pruefung` command (on-demand, no cron)

### Planned — v2.0.0
- `LektureAgent` — real German article fetch + 6 comprehension question types
- `HoerenAgent` — DW/Easy German episode fetch + translation paragraph
- `web_search_tool`, `web_fetch_tool` — Google Custom Search API integration
- `/lektuere` command + fortnightly Wednesday cron
- `/hoeren` command + Sunday cron

### Planned — v3.0.0
- Migrate lernpaket dashboard to Vite + React + TypeScript; replace static snapshot with live Firestore SDK reads
- Port existing panels: KPI tiles, activity heatmap, vocab explorer, session log, B2 cheatsheet
- Add `Gespräch` panel: mic → AudioWorklet → 16kHz PCM → WebSocket → Gemini Live API; real-time transcript + mistake ticker
- Fehler-Rewind carried into live call from Firestore history; adaptive pacing; spoken B2-Umformulierung
- End-of-call summary; session saved to Firestore (same schema as Telegram)
- Cloud Functions ephemeral token endpoint (keeps API key server-side)

---

## [1.0.0] — 2026-09-06

Initial release of **deutsch-adk-coach**, re-engineering the B2 German learning framework into an autonomous event-driven AI agent architecture.

### Added
- `ConversationAgent`: stateful multi-turn B2 conversation agent built with `google-genai` SDK and `gemini-3.6-flash`; 11 mistake categories; mandatory B2-Umformulierung; one question per turn
- `validate_and_save_session` Gemini function tool: dual-destination telemetry (local JSON or Cloud Firestore) conforming to `session_schema.json`
- Telegram bot (`src/main.py`): asynchronous long-polling with per-user `asyncio.Lock` preventing out-of-order message processing
- Native Telegram `.ogg` Opus voice note processing: `send_audio()` sends raw bytes to Gemini Multimodal for direct speech comprehension
- Access control: `ALLOWED_TELEGRAM_USERS` environment variable restricts bot to authorized Telegram user IDs
- `session_schema.json`: JSON Schema draft-07 data contract covering all session types (`conversation`, `listening`, `writing`, `reading`, `grammar`, `review`), 11 mistake categories, full stats fields
- `test_agent_cli.py`: standalone terminal test runner — exercises agent conversation logic without Telegram
- `Dockerfile`: `python:3.11-slim` container running `python -m src.main`
- `deploy/cloud-run.yaml`: Cloud Run Knative service spec (`maxScale: 1`, `containerConcurrency: 1`)
- `deploy/scheduler.yaml`: Cloud Scheduler cron templates for daily (Tue/Thu), Friday quiz, Sunday listening sessions
- Restructured docs following finanzBot conventions: `docs/spec.md`, `docs/implementation-plan.md`, `docs/guide.md`, `docs/backlog.md`

---

## Historical Evolution

This project is the third stage of an evolution across three repositories:

**v2.0.0 — [deutsch-lernpaket](https://github.com/kalaiguna/deutsch-lernpaket)**
Re-architected by Gunasekaran Chandrasekaran for universal cross-platform and cross-agent support (Google Antigravity IDE, Claude Code, Copilot, Roo Code, OpenWebUI, n8n across Windows, Android, macOS). Replaced Apple Notes MCP with Notion MCP; introduced `session_schema.json` machine-readable telemetry; expanded from 3 to 7 specialized skills (`schreib-skill`, `lektuere-skill`, `monatsrueckblick`, `grammatik-vertiefung`); built the interactive HTML/CSS progress dashboard with heatmaps, streak tracking, and vocabulary explorer.

**v1.0.0 — [MohgaNabil/deutsch-lernpaket](https://github.com/MohgaNabil/deutsch-lernpaket)**
Created by Mohga Nabil with 3 prompt skills (`daily-german-practice`, `german-weekend-review`, `german-sunday-schreiben-und-hoeren`) tightly coupled to Claude and macOS-only Apple Notes MCP. Established the foundational B2 pedagogical design: bilingual 🇩🇪/🇬🇧 chat rhythm, 10 mistake categories, mandatory B2-Umformulierung, and 1–2 questions per turn.
