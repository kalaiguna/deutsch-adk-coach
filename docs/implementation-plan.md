# deutsch-adk-coach — Implementation Plan

Based on spec v1.0 + retrofit analysis of deutsch-lernpaket codebase.

---

## Spec Validation

Cross-check of what spec v1.0 describes vs. what currently exists in the codebase.

| Spec claim | Status | Gap |
|---|---|---|
| `ConversationAgent` with Gemini Chat session | ✅ Exists | — |
| `validate_and_save_session` Gemini tool | ✅ Exists | — |
| Dual-destination (local JSON / Firestore) | ✅ Exists | — |
| Per-user `asyncio.Lock` | ✅ Exists | — |
| Voice note processing via `send_audio()` | ✅ Exists | — |
| Access control (`ALLOWED_TELEGRAM_USERS`) | ✅ Exists | — |
| Cross-session Firestore read | ❌ Missing | Agent only writes; never reads history |
| `vocab_review_misses` schema field | ❌ Missing | Field absent from `session_schema.json` |
| Multi-agent command routing (`/quiz`, `/vocab`, etc.) | ❌ Missing | Only `/start` exists |
| Firestore document ID collision on same-day multi-session | ⚠️ Known gap | ID = `{date}` only; two sessions same day overwrite |

---

## Technical Decisions (Locked)

| # | Decision | Rationale |
|---|---|---|
| 1 | Each new skill = a new agent class, not a mode flag on `ConversationAgent` | Keeps system prompts isolated; prevents prompt bleed between pedagogy modes |
| 2 | Firestore document ID extended to `{date}_{type}` for all new session saves | Prevents same-day overwrite when conversation + quiz happen on the same date |
| 3 | `read_recent_sessions(user_id, days)` added to `firestore_tool.py` (not a new module) | It's persistence logic; keeps the tool surface small and import paths simple |
| 4 | `vocab_review_misses: string[]` added to `session_schema.json` as optional field | All agents that encounter vocab misses populate it; `VocabRecallAgent` reads it |
| 5 | Tier 2 web tools (`web_search_tool`, `web_fetch_tool`) deferred to a separate phase | Requires Google Search API key procurement and rate-limit design; not blocking Tier 1 |
| 6 | Cloud Scheduler triggers are additive — existing daily/Friday/Sunday crons are preserved | Existing scheduler.yaml entries are already scoped to routes that don't exist yet; they stay as-is |
| 7 | `MonatsrueckblickAgent` must run before `GrammarAgent` can select a topic | Grammar deep-dive reads the Monatsrückblick focus areas to pick the weakest category |

---

## Phase Plan

| Phase | Branch | Version | Deliverables |
|---|---|---|---|
| 0 | `main` | v1.0.0 ✅ | `ConversationAgent`, Telegram bot, Firestore write, voice support |
| 1 | `phase/1-firestore-read` | v1.1.0 | `read_recent_sessions()`, `vocab_review_misses` field, `/vocab` + `VocabRecallAgent` |
| 2 | `phase/2-quiz` | v1.2.0 | `QuizAgent` (Fehler-Rewind + Sticky Challenge), `/quiz` command, Friday cron |
| 3 | `phase/3-grammar-report` | v1.3.0 | `MonatsrueckblickAgent` + `/bericht`, `GrammarAgent` + `/grammatik`, 1st-of-month + 10th-of-month crons |
| 4 | `phase/4-exam-prep` | v1.4.0 | `ExamPrepAgent` + `/pruefung` (on-demand, no cron) |
| 5 | `phase/5-web-skills` | v2.0.0 | `LektureAgent` + `HoerenAgent`, `web_search_tool`, `web_fetch_tool`, fortnightly Wed + Sunday crons |

---

## File-Level Implementation Notes

### Phase 1

**`src/schemas/session_schema.json`**
Add optional field under `properties`:
```json
"vocab_review_misses": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Words the learner missed — fed to VocabRecallAgent drill"
}
```

**`src/tools/firestore_tool.py`**
Add below `validate_and_save_session`:
```python
def read_recent_sessions(user_id: str, days: int = 14) -> list[dict]:
    # Query Firestore users/{user_id}/sessions where date >= (today - days)
    # Returns list of session dicts sorted by date descending
```
Exports: `validate_and_save_session`, `read_recent_sessions`

**`src/agents/vocab_recall.py`**
```python
class VocabRecallAgent:
    # Reads vocab_review_misses from last 14 days via read_recent_sessions()
    # Selects up to 12 words, runs SRS-style noun-article + verb-infinitive drill
    # Saves type="grammar" session on /finish (no new schema fields needed)
```
Exports: `VocabRecallAgent`

**`src/main.py`**
Add:
```python
app.add_handler(CommandHandler("vocab", vocab_command))
```

---

### Phase 2

**`src/agents/quiz.py`**
```python
class QuizAgent:
    # Reads ALL past mistakes[] arrays via read_recent_sessions(days=90)
    # Tallies category recurrence; weights question selection toward persistent errors
    # Sticky Challenge: if any category appears 3+ times in 14 days, opens with 3-question micro-drill
    # Game-show format: 4-5 rounds, one question at a time, score tracking
    # Saves type="review" session on finish
```
Exports: `QuizAgent`

**`src/main.py`**
Add:
```python
app.add_handler(CommandHandler("quiz", quiz_command))
```

**`deploy/scheduler.yaml`**
Uncomment Friday quiz cron (already present as comment).

---

### Phase 3

**`src/agents/monatsrueckblick.py`**
```python
class MonatsrueckblickAgent:
    # Reads all sessions from past 30 days via read_recent_sessions(days=30)
    # Aggregates: mistake category tallies, vocab growth, session counts by type, reuse rate
    # Outputs 3 focus areas for next month; saves type="review" + date=YYYY-MM-01
```
Exports: `MonatsrueckblickAgent`

**`src/agents/grammar.py`**
```python
class GrammarAgent:
    # 12-topic monthly rotation: Konjunktiv II, Passiv, Relativsätze, Genitiv, ...
    # Reads most recent Monatsrückblick to select topic aligned with weakest category
    # 3 exercise types per session: fill-blank (Lückentext), transformation (Umformung), free production
    # Saves type="grammar" with Lückentext richtig, Umformung richtig, Freie Sätze stats
```
Exports: `GrammarAgent`

**`src/main.py`**
Add:
```python
app.add_handler(CommandHandler("bericht", bericht_command))
app.add_handler(CommandHandler("grammatik", grammatik_command))
```

**`deploy/scheduler.yaml`**
Add 1st-of-month (Monatsrückblick) and 10th-of-month (Grammatik) crons.

---

### Phase 4

**`src/agents/exam_prep.py`**
```python
class ExamPrepAgent:
    # On-demand telc B2 mock exam — four selectable components:
    #   A. Schreiben: official /45 rubric (Inhalt/15, Aufbau/10, Grammatik/10, Wortschatz/10)
    #   B. Sprechen Teil 1: 5-step monologue scaffold
    #   C. Sprechen Teil 2+3: discussion with Konjunktiv I required
    #   D. Trap Drill: 5 MC question types (word-match trap, extreme words, own logic, opinion-shift, negation)
    # No Firestore save (practice only); session summary on /finish
```
Exports: `ExamPrepAgent`

**`src/main.py`**
Add:
```python
app.add_handler(CommandHandler("pruefung", pruefung_command))
```

---

### Phase 5

**`src/tools/web_search_tool.py`**
Wraps Google Custom Search API; returns top-3 article URLs for a given query.

**`src/tools/web_fetch_tool.py`**
Fetches and strips HTML from a URL; returns plain-text body (300–500 word target).

**`src/agents/lekture.py`**
```python
class LektureAgent:
    # Searches for a real German article (tagesschau, Spiegel, Handelsblatt, Heise)
    # Pre-teaches 5 vocab items from the article before the learner reads
    # 6 comprehension question types: skimming, scanning, inference, vocab-in-context, opinion, summary
    # Saves type="reading" with source_url and Leseverstehen stats
```

**`src/agents/hoeren.py`**
```python
class HoerenAgent:
    # Fetches a DW or Easy German episode URL
    # Pre-teaches 3 transcript words before listening
    # One theme drives both comprehension questions AND translation paragraph
    # Translation is sentence-by-sentence with B2-Umformulierung per sentence
    # Saves type="listening" with Hörverstehen stats
```

---

## Test Plan

| ID | Case | Setup | Assert |
|---|---|---|---|
| T01 | Conversation text turn | Send "Ich gehe gestern ins Kino." | Response contains mistake category label + B2-Umformulierung |
| T02 | Conversation voice turn | Send valid .ogg bytes | Response contains transcription + correction cycle |
| T03 | Session save — local | `USE_LOCAL_STORAGE=true`, send `/finish` | JSON file created under `data/sessions/` matching schema |
| T04 | Session save — Firestore | `GCP_PROJECT_ID` set, send `/finish` | Firestore document exists at `users/{id}/sessions/{date}` |
| T05 | Auth filter | Send message as unlisted user ID | Bot replies "Unauthorized" or silently ignores |
| T06 | Concurrent messages | Two rapid messages same user | Second message waits for lock; no interleaved response |
| T07 | `read_recent_sessions` — empty | User has no prior sessions | Returns empty list, no exception |
| T08 | `read_recent_sessions` — date filter | Sessions older than `days` param | Only sessions within range returned |
| T09 | Vocab drill — no misses | `vocab_review_misses` empty across all sessions | Agent gracefully reports no misses, exits |
| T10 | Quiz — Fehler-Rewind | Past sessions contain 4+ `Kasus` mistakes | Quiz opens with Kasus-weighted questions |
| T11 | Quiz — Sticky Challenge | `Wortstellung` appears 3+ times in last 14 days | Sticky Challenge micro-drill fires in round 1 |
| T12 | Grammar — topic selection | Monatsrückblick lists `Konjunktiv II` as top focus area | GrammarAgent selects Konjunktiv II topic |
| T13 | Monatsrückblick — aggregation | 10 sessions in last 30 days, mixed types | Report counts session types correctly, lists top 3 mistake categories |
| T14 | Schema — `vocab_review_misses` | Session saved with populated field | Field present and is `string[]` in stored JSON |
| T15 | Same-day two sessions | Conversation session saved, then quiz saved, same date | Two distinct documents (`date_conversation`, `date_review`) — no overwrite |

---

_All decisions locked. Ready to implement._
