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

## Out of scope

- Dashboard / HTML progress report (lives in the separate deutsch-lernpaket skills; pulling HTML generation into the Telegram bot adds complexity for no UX gain)
- Notion MCP integration (replaced by Firestore in this repo)
- Dictation mode (covered adequately by the voice note path in `ConversationAgent`)
- Structured writing coach (`/schreiben` + `SchreibAgent`) — `ConversationAgent` already handles writing tasks on request; a separate mode adds overhead without meaningful pedagogical improvement at this stage
