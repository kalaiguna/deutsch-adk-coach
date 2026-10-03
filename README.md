# deutsch-adk-coach

Autonomous German B2 language coach — Telegram + web, built towards Google ADK multi-agent orchestration.

> **Active development.** Built on Google ADK 2.11.0 with 8 specialized agents and a Vite+React web companion. Picked up from [deutsch-genai-coach](https://github.com/kalaiguna/deutsch-genai-coach) (frozen at v1.0).

---

```
You → Telegram (text / .ogg voice) → Bot → ADK Runner → Agent (mode-routed)
                                                              |
                                                       Firestore / local JSON

You → Web (GespraechPanel) → Gemini Live API (WebSocket) → ConversationAgent
                                                              |
                                                        Firestore (on hang-up)
```

---

## Why deutsch-adk-coach?

Earlier versions of this coach lived as prompt skills for Claude Code or Roo Code — a practice session required an open IDE. This repo removes that dependency.

- Runs on Cloud Run; accessible via Telegram from any device without an IDE.
- Voice notes are processed directly by Gemini Multimodal — no separate transcription step.
- Every session is saved to Cloud Firestore, which feeds the quiz (mistake-weighted), monthly report, and grammar topic selection in subsequent sessions.
- Google ADK runner routes between 8 specialized agents, each with its own system prompt and tool set, based on the active Telegram command.

---

## What it does today (v3.0)

**Telegram bot — 8 commands, 8 specialized agents:**

| Command | Agent | What it does |
|---|---|---|
| `/start` | `ConversationAgent` | Bilingual B2 conversation, 11 mistake categories, B2-Umformulierung, voice notes via Gemini Multimodal |
| `/vocab` | `VocabRecallAgent` | SRS-style noun-article + verb-infinitive drill from `vocab_review_misses` across last 14 days |
| `/quiz` | `QuizAgent` | Fehler-Rewind (mistake-weighted questions) + Sticky Challenge micro-drill for persistent errors |
| `/grammatik` | `GrammarAgent` | 12-topic monthly rotation, aligned to weakest Monatsrückblick category, 3 exercise types |
| `/bericht` | `MonatsrueckblickAgent` | Aggregates 30-day sessions, tallies 11 categories, outputs 3 focus areas, saves `type="review"` |
| `/pruefung` | `ExamPrepAgent` | telc B2 mock: Schreiben /45, Sprechen Teil 1/2+3, Trap Drill — practice-only, no save |
| `/lektuere` | `LektureAgent` | Fetches real German article (tagesschau/Spiegel/Heise/Handelsblatt), pre-teaches 5 words, 6 comprehension question types |
| `/hoeren` | `HoerenAgent` | Fetches DW/Easy German episode, pre-teaches 3 words, comprehension + sentence-by-sentence translation |

**Web companion (`web/`):**

- GitHub-style activity heatmap, vocab explorer, session log — all on live Firestore data
- **Gespräch panel**: real-time voice call via Gemini Live API (WebSocket, 16kHz PCM in / 24kHz PCM out, AudioWorklet)
- Cloud Function token endpoint (`functions/`) keeps the Gemini API key out of the browser

→ Full roadmap history: [docs/backlog.md](docs/backlog.md)

---

## Is it safe to send voice notes?

Your voice note is downloaded from Telegram's servers, sent to the Gemini API for processing, and then discarded from memory. The audio bytes are never written to disk or Firestore — only the text transcript and feedback are saved. See [Guide → Security](docs/guide.md#2-security) for the full data-flow breakdown.

---

## Quick start

1. Set your environment variables — copy `.env.example` to `.env` and fill in `GEMINI_API_KEY` and `TELEGRAM_BOT_TOKEN`
2. Install dependencies: `pip install -r requirements.txt`
3. Test the agent locally without Telegram: `python test_agent_cli.py`
4. Run the bot: `python -m src.main`

→ Full setup and deployment: [Guide → For Developers](docs/guide.md#3-for-developers)

---

## Detailed guides

| Who you are | Where to go |
|---|---|
| Learner using the Telegram bot | [Guide → For Users](docs/guide.md#1-for-users) |
| Developer adding features or agents | [Guide → For Developers](docs/guide.md#3-for-developers) |
| DevOps deploying to Cloud Run | [Guide → For DevOps](docs/guide.md#4-for-devops) |

---

## Tech stack

**Backend:** Python 3.11 · Google ADK 2.11.0 · Gemini 2.5 Flash · python-telegram-bot · Cloud Firestore · Cloud Run · Cloud Scheduler · Google Custom Search API

**Web:** Vite 6 · React 18 · TypeScript · Firebase SDK · Gemini Live API (WebSocket) · AudioWorklet · Cloud Functions (Python)

---

## Extending deutsch-adk-coach

- **Add a new agent**: create an `LlmAgent` in `src/agents/`, add a runner to `RUNNERS` in `src/main.py`, wire a `CommandHandler` and a branch in `_voice_content`
- **Add a new tool**: add it under `src/tools/`, import in the relevant agent's `tools=[]` list
- **Add a web panel**: create a React component in `web/src/components/`, wire it into the nav in `App.tsx`

→ Architecture decisions: [docs/implementation-plan.md](docs/implementation-plan.md)

---

## Running tests

```bash
pip install pytest pytest-asyncio
pytest
```

42 unit tests across 4 modules:

| Module | Tests | Coverage |
|---|---|---|
| `tests/test_firestore_tool.py` | 10 | `_extract_user_id`, `validate_and_save_session`, `read_recent_sessions` |
| `tests/test_web_tools.py` | 12 | `_is_allowed_url`, `fetch_article_text`, `search_german_article` |
| `tests/test_main_routing.py` | 15 | `_voice_content` (all 8 modes), session ID helpers, `is_authorized` |
| `tests/test_token_endpoint.py` | 5 | Cloud Function token endpoint (POST/OPTIONS/GET, CORS, missing key) |

---

## License & history

MIT. See [CHANGELOG.md](CHANGELOG.md) for version history. Evolved from [deutsch-genai-coach](https://github.com/kalaiguna/deutsch-genai-coach) (v1.0 reference implementation using raw google-genai SDK), which itself is the third stage of an evolution that started with [MohgaNabil/deutsch-lernpaket](https://github.com/MohgaNabil/deutsch-lernpaket).
