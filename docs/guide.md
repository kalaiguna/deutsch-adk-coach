# deutsch-adk-coach — Guide

---

## 1. For Users

### What can I send?

| Input | What happens |
|---|---|
| German text message | Coach evaluates grammar, labels mistake categories, gives B2-Umformulierung, asks a follow-up question |
| Telegram voice note (`.ogg`) | Gemini transcribes spoken German, then applies the same correction + paraphrase cycle |
| `/start` | Begins a new conversation session (resets the current session if one is active) |
| `/finish` | Ends the session — coach summarizes vocabulary and mistakes, saves telemetry to Firestore |

### What does a session look like?

Every coach reply follows this format:

```
🇩🇪 **Ich bin gestern ins Kino gegangen.**

🇬🇧 I went to the cinema yesterday.

---
⚠️ Mistake — Verbform: "Ich gehe gestern" → "Ich bin gestern gegangen" (Perfekt required for completed past events)

🇩🇪 **B2-Umformulierung:** Gestern Abend habe ich mir einen Film im Kino angesehen.

🇬🇧 Last night I watched a film at the cinema.

---
🇩🇪 **Wie hat dir der Film gefallen?**

🇬🇧 How did you like the film?
```

### What gets saved at /finish?

- Vocabulary encountered: nouns (with article + plural), verbs (infinitive + Perfekt), adjectives, idioms
- All mistakes: category, wrong form, correct form, explanation
- Session stats: number of turns, total words, session duration, grammar feature usage
- Theme and date

Nothing else is stored. Audio bytes are not saved.

---

## 2. Security

### Exactly what happens when I send a voice note?

1. **Telegram** receives your voice note and stores it on their servers. You download it via the Telegram Bot API using a temporary URL.
2. **Cloud Run** (this bot) downloads the `.ogg` bytes into memory. The bytes are never written to disk.
3. **Gemini API** receives the raw bytes + a transcription prompt. Gemini processes it and returns text. The audio is not stored by Gemini.
4. **The reply** (text only) is sent back through Telegram. The `.ogg` bytes are discarded from memory.

Voice audio never touches Firestore or local storage.

### Who can use the bot?

If `ALLOWED_TELEGRAM_USERS` is set, only those Telegram user IDs can interact with the bot. All other users receive "Unauthorized" or are silently ignored. If the variable is empty, the bot is open to anyone who finds it.

---

## 3. For Developers

### Tech stack

| Layer | Technology | Why |
|---|---|---|
| AI model | Gemini 3.6 Flash (`google-genai` SDK) | Native multimodal audio support; Gemini tool-calling for session save |
| Bot framework | `python-telegram-bot` 21+ | Async-first; clean handler model |
| Persistence | Cloud Firestore (or local JSON) | Schemaless per-user document store; enables cross-session history reads |
| Deployment | Cloud Run + Cloud Scheduler | Scale-to-zero; cron triggers for automated morning sessions |
| Schema validation | `session_schema.json` (JSON Schema draft-07) | Shared contract between all agent types |

### Architecture

```
src/
├── main.py               Telegram handlers + asyncio.Lock per user
├── config.py             Env vars, BASE_DIR, model defaults
├── agents/
│   ├── conversation.py   ConversationAgent — Gemini Chat session
│   └── prompts.py        B2 system prompts
├── tools/
│   ├── firestore_tool.py validate_and_save_session + read_recent_sessions (planned)
│   └── voice_tool.py     .ogg → Gemini payload helper
└── schemas/
    └── session_schema.json
```

### Key design decisions

**One agent per skill, not modes on one agent.** Each pedagogy mode (conversation, quiz, grammar) is a separate agent class with its own system prompt and tool set. This prevents prompt bleed and keeps individual agents testable in isolation.

**Gemini tool-calling for session persistence.** `validate_and_save_session` is registered as a Gemini function tool. The agent decides when to call it (on `/finish` or natural session end). This lets the model populate the full session schema without explicit parsing logic in Python.

**Per-user asyncio.Lock.** Telegram users can send messages faster than the model responds. The lock ensures turns are processed in order, preventing race conditions between concurrent Telegram webhook callbacks for the same user.

### AI usage

| Step | Model call | Input | Output |
|---|---|---|---|
| Text turn | `chat.send_message(text)` | Learner's German text | Correction + B2-Umformulierung + follow-up question |
| Voice turn | `chat.send_message([audio_part, instruction])` | `.ogg` bytes + transcription prompt | Transcription + correction cycle |
| Session save | Gemini tool call → `validate_and_save_session` | Model-generated session JSON | Firestore write confirmation |

### Adding an agent

1. Create `src/agents/<skill_name>.py` with a class that wraps a `google-genai` Chat session
2. Write a system prompt in `src/agents/prompts.py`
3. Register any new Gemini tools in the agent's `__init__`
4. Add a command handler in `src/main.py`:
   ```python
   async def my_command(update, context):
       lock = get_or_create_lock(update.effective_user.id)
       async with lock:
           agent = get_or_create_my_agent(update.effective_user.id)
           reply = agent.send_message(update.message.text)
           await update.message.reply_text(reply)

   app.add_handler(CommandHandler("mycommand", my_command))
   ```
5. If the agent runs on a schedule, add a cron entry to `deploy/scheduler.yaml`
6. If the agent saves sessions, ensure the session `type` field uses a value from the `session_schema.json` enum

### Running locally

```bash
# No Telegram needed — test agent logic directly
python test_agent_cli.py

# Full bot (long-polling, connects to Telegram)
python -m src.main
```

---

## 4. For DevOps

### Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | For local dev and the container base image |
| Google Cloud project | Needed for Firestore + Cloud Run + Cloud Scheduler |
| Gemini API key | Google AI Studio (free tier available) or Vertex AI |
| Telegram Bot Token | Create via [@BotFather](https://t.me/BotFather) |
| `gcloud` CLI | Authenticated with project set |
| Docker | For building the container image |

### Environment variables

Copy `.env.example` to `.env`:

```env
GEMINI_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
GEMINI_MODEL=gemini-3.6-flash
GCP_PROJECT_ID=your_gcp_project
USE_LOCAL_STORAGE=false
ALLOWED_TELEGRAM_USERS=123456789,987654321
```

### Cloud Run deployment

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/deutsch-adk-coach

# Deploy (replace PROJECT_ID in cloud-run.yaml first)
gcloud run services replace deploy/cloud-run.yaml --region europe-west1
```

### Cloud Run settings

| Setting | Value | Reason |
|---|---|---|
| `maxScale` | 1 | Prevents multiple instances from holding conflicting in-memory session state |
| `containerConcurrency` | 1 | One request processed at a time per instance |
| Memory | 512Mi | Sufficient for audio byte buffers |
| CPU | 1 | Single-threaded workload |

### Cloud Scheduler

All cron jobs post to Cloud Run trigger routes (routes not yet implemented — add them in `src/main.py` as webhook handlers when enabling scheduler-driven sessions):

```bash
# Tuesday & Thursday daily conversation (09:00 Berlin)
gcloud scheduler jobs create http deutsch-daily-practice \
    --schedule="0 9 * * 2,4" --time-zone="Europe/Berlin" \
    --uri="https://YOUR_CLOUD_RUN_URL/trigger/daily" --http-method=POST

# Friday quiz (09:00 Berlin)
gcloud scheduler jobs create http deutsch-friday-quiz \
    --schedule="0 9 * * 5" --time-zone="Europe/Berlin" \
    --uri="https://YOUR_CLOUD_RUN_URL/trigger/quiz" --http-method=POST

# Sunday listening & translation (09:00 Berlin)
gcloud scheduler jobs create http deutsch-sunday-listening \
    --schedule="0 9 * * 0" --time-zone="Europe/Berlin" \
    --uri="https://YOUR_CLOUD_RUN_URL/trigger/listening" --http-method=POST
```

See `deploy/scheduler.yaml` for the full set including planned grammar and monthly report crons.

### Observability

1. **Cloud Run logs** — structured logs from `logging.basicConfig` in `src/main.py`; filter by `levelname=ERROR` in Cloud Logging
2. **Firestore** — session documents at `users/{user_id}/sessions/{date}`; use the Firestore console to verify saves
3. **Telegram bot health** — if the bot stops responding, check Cloud Run instance count and last request timestamp in Cloud Monitoring

### Extending deutsch-adk-coach

**Add a new Telegram command:**
- Add a handler in `src/main.py` (see [For Developers → Adding an agent](#adding-an-agent))
- Deploy a new container revision: `gcloud builds submit && gcloud run services replace ...`

**Add a new scheduled session type:**
- Add a `/trigger/<type>` route to `src/main.py`
- Register the cron with `gcloud scheduler jobs create http ...`
- Add the agent class under `src/agents/`
