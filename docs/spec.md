# deutsch-adk-coach — Architecture & Implementation Specification v1.0

---

## 1. Purpose

An autonomous, event-driven German B2 language coach running as a Telegram bot. The agent conducts bilingual conversation sessions, processes voice notes via Gemini Multimodal, categorizes grammar mistakes, and persists structured session telemetry to Cloud Firestore.

---

## 2. System Diagram

```
Learner
  |
  | text / .ogg voice note
  v
Telegram Bot API (python-telegram-bot, long-polling)
  |
  | asyncio per-user Lock
  v
src/main.py
  |-- CommandHandler("/start") ---------> reset ConversationAgent
  |-- MessageHandler(TEXT) ------------> agent.send_message(text)
  |-- MessageHandler(VOICE) -----------> agent.send_audio(bytes, "audio/ogg")
  |
  v
ConversationAgent (google-genai Chat session)
  |-- system_instruction: CONVERSATION_SYSTEM_PROMPT
  |-- tool: validate_and_save_session
  |-- model: gemini-3.6-flash, temperature=0.7
  |
  | on /finish or session end
  v
validate_and_save_session (Gemini tool call)
  |
  |-- config.USE_LOCAL_STORAGE=true  --> data/sessions/<date>_<type>.json
  |-- config.USE_LOCAL_STORAGE=false --> Firestore: users/{user_id}/sessions/{date}
```

---

## 3. Components

| Component | File | Responsibility |
|---|---|---|
| Telegram entry point | `src/main.py` | Handler routing, per-user `asyncio.Lock`, auth filter |
| Config | `src/config.py` | Env var loading, `BASE_DIR`, model defaults |
| Conversation agent | `src/agents/conversation.py` | Stateful `google-genai` Chat session, text + audio turns |
| System prompt | `src/agents/prompts.py` | B2 pedagogy rules, formatting contract, 11 mistake categories |
| Session persistence | `src/tools/firestore_tool.py` | Schema validation, local JSON or Firestore write |
| Voice preprocessing | `src/tools/voice_tool.py` | Telegram `.ogg` → Gemini-compatible payload |
| Session schema | `src/schemas/session_schema.json` | JSON Schema draft-07 data contract for all session types |
| Container | `Dockerfile` | `python:3.11-slim`, runs `python -m src.main` |
| Cloud Run spec | `deploy/cloud-run.yaml` | `maxScale: 1`, `containerConcurrency: 1` — sequential per-instance |
| Scheduler | `deploy/scheduler.yaml` | Cron templates: Tue/Thu daily, Fri quiz, Sun listening |
| Local test runner | `test_agent_cli.py` | Terminal loop exercising agent without Telegram |

---

## 4. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio or Vertex AI key |
| `TELEGRAM_BOT_TOKEN` | Yes | — | BotFather token |
| `GEMINI_MODEL` | No | `gemini-3.6-flash` | Model override |
| `GCP_PROJECT_ID` | No | — | GCP project; absence triggers local storage |
| `USE_LOCAL_STORAGE` | No | `false` | Force local JSON even when GCP is set |
| `ALLOWED_TELEGRAM_USERS` | No | — | Comma-separated Telegram user IDs; empty = open |

---

## 5. Session Schema (`src/schemas/session_schema.json`)

JSON Schema draft-07. All agents must produce output conforming to this schema before calling `validate_and_save_session`.

### Required fields

| Field | Type | Notes |
|---|---|---|
| `date` | string | `YYYY-MM-DD`; Monatsrückblick uses `YYYY-MM-01` |
| `theme` | string | Topic in German; prefix with 💼 for professional sessions |
| `name` | string | Full page title — format varies by `type` |
| `type` | enum | `conversation \| listening \| writing \| reading \| grammar \| review` |

### Optional arrays

`nouns`, `adjectives`, `verbs`, `idioms`, `mistakes` — each typed with `word`/`meaning` or `wrong`/`right` + `category` (one of the 11 mistake categories).

### Mistake categories (11 fixed values)

`Artikel/Genus`, `Kasus`, `Wortstellung`, `Verbform`, `Präposition`, `Wortwahl`, `Vokabular`, `Rechtschreibung`, `Komposition`, `Anglizismus/False Friend`, `Sonstiges`

### Stats fields (selection by type)

| Field | Type used in |
|---|---|
| `Anzahl Antworten`, `Wörter insgesamt`, `Sitzungsdauer (Minuten)` | conversation |
| `Komplexe Sätze`, `Konjunktiv II`, `Passiv`, `Genitiv` | conversation |
| `Hörverstehen (richtig/gesamt)` | listening |
| `Leseverstehen (richtig/gesamt)`, `Wörter im Artikel`, `source_url` | reading |
| `Lückentext richtig`, `Umformung richtig`, `Freie Sätze` | grammar |
| `Sitzungen gesamt`, `Neue Vokabeln`, `Wiederverwendungsrate (%)` | review |

---

## 6. Conversation Pedagogy (CONVERSATION_SYSTEM_PROMPT)

| Rule | Detail |
|---|---|
| Bilingual format | Every German line: `🇩🇪 **bold German**`, blank line, `🇬🇧 English` |
| Rhythm | Exactly ONE question per turn; maximum TWO when naturally paired |
| Mistake feedback | Label category from the 11 fixed values; show wrong → right |
| B2-Umformulierung | Always paraphrase the learner's thought at B2 level after correcting |
| Voice turns | Transcribe first, then apply the same correction + paraphrase cycle |
| Session close | On `/finish`: summarize vocab + mistakes, call `validate_and_save_session` |

---

## 7. Firestore Layout

```
Firestore
└── users/
    └── {telegram_user_id}/
        └── sessions/
            └── {YYYY-MM-DD}       ← session document (session_schema fields)
```

For multi-session days (e.g. conversation + quiz on the same date), the document ID should be extended to `{YYYY-MM-DD}_{type}` — this is a known limitation to address in v1.1.

---

## 8. Concurrency Model

Cloud Run is set to `maxScale: 1` and `containerConcurrency: 1` — one request processed at a time per instance. Inside the process, each Telegram user additionally gets their own `asyncio.Lock` to prevent interleaved turns from rapid message sends.

---

## 9. Deployment

```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/deutsch-adk-coach

# Deploy to Cloud Run
gcloud run services replace deploy/cloud-run.yaml --region europe-west1

# Register scheduler crons (see deploy/scheduler.yaml for full commands)
gcloud scheduler jobs create http deutsch-daily-practice \
    --schedule="0 9 * * 2,4" --time-zone="Europe/Berlin" \
    --uri="https://YOUR_CLOUD_RUN_URL/trigger/daily" --http-method=POST
```

→ Full deployment walkthrough: [docs/guide.md#4-for-devops](guide.md#4-for-devops)

---

## 10. Future Enhancements

| Feature | New component | Complexity | Tier |
|---|---|---|---|
| Cross-session history read | `firestore_tool.read_recent_sessions()` | Low | 1 |
| Vocab recall drill (`/vocab`) | `VocabRecallAgent` + `vocab_review_misses` schema field | Medium | 1 |
| Adaptive quiz (`/quiz`) | `QuizAgent` with Fehler-Rewind + Sticky Challenge | Medium | 1 |
| Grammar deep-dive (`/grammatik`) | `GrammarAgent`, 12-topic rotation | Medium | 1 |
| Mock exam prep (`/pruefung`) | `ExamPrepAgent`, telc /45 rubric | Medium | 1 |
| Monthly report (`/bericht`) | `MonatsrueckblickAgent` | Medium | 1 |
| Reading comprehension (`/lektuere`) | `LektureAgent` + `web_search_tool` + `web_fetch_tool` | High | 2 |
| Listening + translation (`/hoeren`) | `HoerenAgent` + same web tooling | High | 2 |
| Structured writing (`/schreiben`) | `SchreibAgent`, 6 task types | Low | 3 |

→ Phased implementation plan: [docs/implementation-plan.md](implementation-plan.md)

---

## 11. Instructions for Claude Code

When implementing features in this repo:
- Always conform new session types to `src/schemas/session_schema.json` — validate before saving
- New agents go in `src/agents/`; new tools go in `src/tools/`
- Wire new Telegram commands in `src/main.py` using `CommandHandler`
- Every new agent needs a corresponding entry in `deploy/scheduler.yaml` if it runs on a cron
- The `asyncio.Lock` pattern in `main.py` must be applied to every new command handler that touches a session
- Run `python test_agent_cli.py` to verify agent logic before wiring to Telegram
