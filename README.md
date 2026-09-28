# deutsch-adk-coach

Autonomous German B2 language coach — multi-agent, Google ADK-native, Telegram + web.

> **Active development.** This repo picks up from [deutsch-genai-coach](https://github.com/g-aa-chandrasekaran/deutsch-genai-coach) (v1.0, frozen) and rebuilds on Google ADK for multi-agent orchestration.

---

```
You → Telegram (text / .ogg voice) → ADK Runner → ConversationAgent / QuizAgent / GrammarAgent / …
                                                              |
                                                       Firestore / local JSON
```

---

## Why deutsch-adk-coach?

**Speak to improve, not to transcribe.** Earlier versions of this coach lived as prompt skills in Claude or n8n — they required the learner to paste session notes manually. This rewrite removes all manual steps.

- **Voice-first.** Send a Telegram voice note and the coach hears it directly via Gemini Multimodal — no transcription step, no copy-paste.
- **Multi-agent.** Google ADK runner orchestrates routing between specialized agents — conversation, quiz, grammar, vocab recall, exam prep — without manual session switching logic.
- **Persistent telemetry.** Every session is saved to Cloud Firestore in a machine-readable schema, enabling Fehler-Rewind (mistake-weighted quiz) and monthly progress reports.
- **Always available.** Runs on Cloud Run; Cloud Scheduler triggers quiz on Fridays, grammar on the 10th, monthly report on the 1st.
- **B2-grade feedback.** 11 mistake categories, mandatory B2-Umformulierung, one question per turn — applied consistently across all agent modes.

---

## What it does

- Conducts bilingual (DE/EN) B2 conversation sessions over text or voice
- Routes between specialized agents via ADK runner (`/quiz`, `/vocab`, `/grammatik`, `/pruefung`, `/bericht`)
- Categorizes grammar mistakes into 11 fixed categories per turn
- Provides a B2-Umformulierung (B2 paraphrase) after every learner response
- Saves session vocabulary, mistakes, and stats to Firestore on `/finish`

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

Python 3.11 · Google ADK · google-genai SDK · Gemini 3.6 Flash · python-telegram-bot · Cloud Firestore · Cloud Run · Cloud Scheduler

---

## Extending deutsch-adk-coach

- **Add a new agent**: subclass ADK `BaseAgent`, register in the ADK runner, wire a `CommandHandler` in `src/main.py`
- **Enable web-fetch skills** (reading, listening): add `web_search_tool.py` and `web_fetch_tool.py` under `src/tools/` and register them in the relevant agent

→ Full roadmap: [docs/backlog.md](docs/backlog.md)

---

## Running tests

```bash
python test_agent_cli.py
```

Exercises the full `ConversationAgent` loop (text and audio paths) without a Telegram connection.

---

## License & history

MIT. See [CHANGELOG.md](CHANGELOG.md) for version history. Evolved from [deutsch-genai-coach](https://github.com/g-aa-chandrasekaran/deutsch-genai-coach) (v1.0 reference implementation using raw google-genai SDK), which itself is the third stage of an evolution that started with [MohgaNabil/deutsch-lernpaket](https://github.com/MohgaNabil/deutsch-lernpaket).
