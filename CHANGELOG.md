# Changelog

All notable changes to **deutsch-adk-coach** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.0] — 2026-10-03

### Added
- `terraform/` module — provisions all GCP infrastructure from scratch with a single `terraform apply`
- `google_cloud_run_v2_service` — bot deployment with Secret Manager injection, `maxScale: 1`, `containerConcurrency: 1`
- `google_cloudfunctions2_function` — token endpoint (gen2), source uploaded from GCS, unauthenticated public access
- `google_firestore_database` — Firestore native database in the configured region
- `google_cloud_scheduler_job` (×5) — all five session crons (Tue/Thu conversation, Fri quiz, Sun hoeren, 1st bericht, 10th grammatik)
- `google_secret_manager_secret` — all four API keys stored as secrets; never in plaintext Cloud Run spec
- `google_billing_budget` — monthly budget cap (default $20 USD) with email + Pub/Sub alerts at 50%, 90%, and 100%
- `google_pubsub_topic` — budget alert topic for future programmatic subscribers (e.g. disabling paid commands on breach)
- `google_monitoring_notification_channel` — email channel for budget alert delivery
- `terraform.tfvars.example` — copy-and-fill template; actual `terraform.tfvars` is gitignored
- `.gitignore` — Terraform state, lock file, build artifacts, and `terraform.tfvars` excluded
- `docs/guide.md` §4 updated with Terraform-first deploy instructions

---

## [3.0.0] — 2026-10-03

### Added
- Vite 8 + React 19 + TypeScript web companion (`web/`)
- `ActivityHeatmap` component — GitHub-style calendar heatmap of session activity
- `VocabExplorer` component — searchable, sortable vocabulary table with gender-drill modal for nouns
- `SessionLog` component — session list with drill-down into mistakes and vocabulary
- `GespraechPanel` component — real-time voice call via Gemini Live API over WebSocket; 16kHz PCM mic input via AudioWorklet, 24kHz PCM playback
- `useSessions` Firestore hook — live query with server-side date filter (`where("date", ">=", cutoff)`)
- `functions/token_endpoint.py` — Cloud Function (`POST /token`) returning `{token, model}`; keeps Gemini API key out of the browser

### Technical
- Two separate `AudioContext` refs (`micCtxRef` 16kHz, `outCtxRef` 24kHz) — avoids mid-call orphan when switching contexts
- `worklet.port.onmessage` wired before WebSocket opens — prevents mic audio drop at call start
- Functional `setStatus` updater in `ws.onclose` — fixes stale closure where status read "connecting" at fire time

---

## [2.0.0] — 2026-10-03

### Added
- `LektureAgent` — searches for a real German news article (tagesschau, Spiegel, Heise, Handelsblatt); pre-teaches 5 vocabulary items; 6 comprehension question types (skimming, scanning, inference, vocab-in-context, opinion, summary); saves `type="reading"` with `source_url`
- `HoerenAgent` — finds a DW or Easy German episode; pre-teaches 3 transcript words; comprehension questions + sentence-by-sentence translation with B2-Umformulierung; saves `type="listening"`
- `web_search_tool.py` — Google Custom Search API wrapper; domain allowlist split by `source_type` (reading vs listening)
- `web_fetch_tool.py` — HTML fetch, script/style strip, entity decode, 6000-char truncation; SSRF protection via `_ALLOWED_DOMAINS` hostname check before any HTTP request
- `/lektuere` Telegram command + fortnightly Wednesday cron
- `/hoeren` Telegram command + Sunday cron
- `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_CX` env vars in `src/config.py`

---

## [1.4.0] — 2026-10-03

### Added
- `ExamPrepAgent` — on-demand telc B2 mock exam with four selectable components: Schreiben (official /45 rubric: Inhalt 15, Aufbau 10, Grammatik 10, Wortschatz 10), Sprechen Teil 1 (5-step monologue scaffold), Sprechen Teil 2+3 (partner discussion with Konjunktiv I), Trap Drill (5 MC question types that frequently catch candidates)
- `/pruefung` Telegram command — practice only, no session save

---

## [1.3.0] — 2026-10-03

### Added
- `MonatsrueckblickAgent` — aggregates all sessions from the past 30 days; tallies 11 mistake categories; outputs vocab growth, session counts by type, reuse rate, and 3 focus areas for next month; saves `type="review"` with `date=YYYY-MM-01`
- `GrammarAgent` — 12-topic monthly rotation (Konjunktiv II, Passiv, Relativsätze, Genitiv, Infinitivkonstruktionen, Modalpartikeln, Wortbildung, Adjektivdeklination, Indirekte Rede, Temporalangaben, Präpositionen mit Kasus, Satzverbindungen); reads most recent Monatsrückblick to align topic with weakest category; 3 exercise types per session (Lückentext, Umformung, Freie Sätze)
- `/bericht` Telegram command + 1st-of-month 08:00 Berlin cron
- `/grammatik` Telegram command + 10th-of-month 09:00 Berlin cron

---

## [1.2.0] — 2026-10-03

### Added
- `QuizAgent` — game-show format, 4–5 rounds, one question per turn
- Fehler-Rewind: reads all past `mistakes[]` from Firestore, tallies category recurrence across sessions, weights questions toward persistent errors
- Sticky Challenge: if any mistake category appears 3+ times in the last 14 days, opens with a targeted 3-question micro-drill for that category
- `/quiz` Telegram command + Friday 09:00 Berlin cron

---

## [1.1.0] — 2026-10-02

### Added
- `read_recent_sessions(user_id, days)` in `firestore_tool.py` — queries Firestore (or local JSON) for sessions within a rolling date window; shared by all downstream agents
- `vocab_review_misses: string[]` field added to `session_schema.json`
- `VocabRecallAgent` — reads `vocab_review_misses` from last 14 days across all session types; SRS-style noun-article + verb-infinitive drill; up to 12 words per session
- `/vocab` Telegram command
- Migrated from `google-genai` SDK to Google ADK 2.11.0 — `LlmAgent`, `Runner`, `InMemorySessionService`; `RUNNERS` dict in `src/main.py` replaces manual session routing
- Firestore document ID extended to `{YYYY-MM-DD}_{type}` — prevents same-day overwrite when multiple session types occur on the same date

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
