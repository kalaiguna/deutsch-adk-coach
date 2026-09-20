# deutsch-adk-coach — Backlog & Roadmap

---

## Milestone map

| Version | Theme | AI approach |
|---|---|---|
| v1.0.0 | Foundation — conversation + voice | Single `ConversationAgent`, Gemini tool-calling for session save |
| v1.1.0 | Cross-session memory + vocab recall | Firestore history reads; `VocabRecallAgent` with SRS-style drill |
| v1.2.0 | Adaptive quiz | `QuizAgent` with Fehler-Rewind (mistake-weighted) + Sticky Challenge |
| v1.3.0 | Grammar deep-dive + monthly report | `GrammarAgent` (12-topic rotation) + `MonatsrueckblickAgent` (aggregation) |
| v1.4.0 | Exam preparation | `ExamPrepAgent` — telc B2 mock with /45 rubric and Trap Drill |
| v2.0.0 | Real-world input (reading + listening) | `LektureAgent` + `HoerenAgent` — WebSearch + WebFetch tooling required |
| v3.0.0 | Web companion — dashboard + real-time voice calls | lernpaket dashboard migrated to Vite/React/TS; Firestore live data; Gemini Live API Gespräch panel |

---

## v1.0.0 — Foundation ✅

- `ConversationAgent`: multi-turn B2 conversation, text + voice, 11 mistake categories, B2-Umformulierung
- `validate_and_save_session` Gemini tool: dual-destination (local JSON / Firestore)
- Telegram bot: `/start`, text handler, voice handler, per-user `asyncio.Lock`
- Access control: `ALLOWED_TELEGRAM_USERS` filter
- Cloud Run + Cloud Scheduler deployment specs
- `test_agent_cli.py` standalone local test runner

---

## v1.1.0 — Cross-session memory + vocab recall

- `read_recent_sessions(user_id, days)` in `firestore_tool.py` — unlocks all downstream history features
- `vocab_review_misses: string[]` field added to `session_schema.json`
- `VocabRecallAgent`: reads misses from last 14 days across all session types; noun-article + verb-infinitive SRS drill; up to 12 words per session
- `/vocab` Telegram command

---

## v1.2.0 — Adaptive quiz

- `QuizAgent`: game-show format, 4–5 rounds, one question per turn
- **Fehler-Rewind**: reads all past `mistakes[]` from Firestore, tallies category recurrence across sessions, weights questions toward persistent errors
- **Sticky Challenge**: if any mistake category appears 3+ times in the last 14 days, opens with a targeted 3-question micro-drill
- `/quiz` Telegram command
- Friday 09:00 Berlin Cloud Scheduler cron

---

## v1.3.0 — Grammar deep-dive + monthly report

- `MonatsrueckblickAgent`: aggregates all Firestore sessions from past 30 days; outputs mistake category tallies, vocab growth curve, session counts by type, reuse rate, and 3 focus areas for next month; saves `type="review"` with `date=YYYY-MM-01`
- `GrammarAgent`: 12-topic monthly rotation (Konjunktiv II, Passiv, Relativsätze, Genitiv, Infinitivkonstruktionen, Modalpartikeln, Wortbildung, Adjektivdeklination, Indirekte Rede, Temporalangaben, Präpositionen mit Kasus, Satzverbindungen); reads Monatsrückblick to align topic with weakest category; 3 exercise types per session (fill-blank, transformation, free production)
- `/bericht` Telegram command + 1st-of-month cron
- `/grammatik` Telegram command + 10th-of-month cron

---

## v1.4.0 — Exam preparation

- `ExamPrepAgent`: on-demand via `/pruefung`; four selectable components:
  - **Schreiben**: official telc /45 rubric (Inhalt 15, Aufbau 10, Grammatik 10, Wortschatz 10)
  - **Sprechen Teil 1**: 5-step monologue scaffold
  - **Sprechen Teil 2+3**: discussion with Konjunktiv I required; partner-style challenge
  - **Trap Drill**: 5 MC question types (word-match trap, extreme words, own-logic trap, opinion-shift signal, negation flip)
- No Firestore save (practice mode only); summary on `/finish`
- No cron — on-demand only

---

## v2.0.0 — Real-world input (reading + listening)

**Requires:** Google Custom Search API key + `web_search_tool.py` + `web_fetch_tool.py`

- `LektureAgent`: searches for a real 300–500 word German article (tagesschau, Spiegel, Handelsblatt 💼, Heise 💼); pre-teaches 5 vocab items; 6 comprehension question types; saves `type="reading"` with `source_url`
- `HoerenAgent`: fetches a DW or Easy German episode; pre-teaches 3 transcript words; one theme drives both comprehension questions and translation paragraph (sentence-by-sentence B2-Umformulierung); saves `type="listening"`
- `/lektuere` command + fortnightly Wednesday cron
- `/hoeren` command + Sunday cron

---

## v3.0.0 — Web companion (dashboard + real-time voice calls)

Inspired by Duolingo Max's "Call with Lily". Telegram stays for async/mobile use; the web app adds a progress dashboard and a "call your coach" mode for desktop sessions.

**Foundation:** The `deutsch-lernpaket` dashboard (`core/dashboard/dashboard.html`) is a production-quality vanilla HTML/CSS/JS + Chart.js app whose session data model already matches adk-coach Firestore sessions exactly. v3.0 migrates it to a Vite + React + TypeScript project, wires it to live Firestore data, and adds a `Gespräch` call panel as a new nav section.

**Requires:** Gemini Live API · Vite + React + TypeScript · Firebase Hosting or Cloud Run static · Cloud Functions (ephemeral token endpoint)

### Dashboard migration (carried over from lernpaket)

- Port existing panels to React components: KPI tiles, GitHub-style activity heatmap, vocab explorer (search / sort / stale-word highlighting / gender drill modal), session log with drill-down, B2 cheatsheet (Grammatik / Schreiben / Sprechen / Prüfung tabs)
- Replace static `SNAPSHOT_SESSIONS` JS constant with live Firestore SDK reads — no more manual snapshot regeneration
- Nav: `Übersicht` · `Vokabular` · `Grammatik` · `Sitzungen` · `Spickzettel` · **`Gespräch`** (new)

### Gespräch panel (new)

- Mic button + call status indicator (idle / connecting / live / ended)
- `getUserMedia` → `AudioWorklet` → 16kHz PCM → WebSocket → Gemini Live API
- 24kHz PCM from Gemini → `AudioContext` → speakers
- Live transcript panel alongside call
- Real-time mistake ticker — categories flagged as they are detected mid-call
- Fehler-Rewind: pre-call Firestore query surfaces persistent mistake categories; coach weights live prompts accordingly
- Adaptive pacing: coach slows down on request, pauses naturally while formulating responses
- No in-call text corrections; spoken B2-Umformulierung delivered after each learner turn
- End-of-call spoken summary + B2-Umformulierung replay panel
- Session saved to Firestore on hang-up (`type="conversation"`, same schema as Telegram)

### Token endpoint (Cloud Functions — 1 route)

- `POST /token` — exchanges `GEMINI_API_KEY` server-side for a short-lived ephemeral token returned to the browser; API key never exposed client-side

---

## Out of scope

- Notion MCP integration (replaced by Firestore in this repo)
- Dictation mode (covered adequately by the voice note path in `ConversationAgent`)
- Structured writing coach (`/schreiben` + `SchreibAgent`) — `ConversationAgent` already handles writing tasks on request; a separate mode adds overhead without meaningful pedagogical improvement at this stage
