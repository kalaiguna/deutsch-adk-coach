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
| 8 | Google ADK runner adopted from v1.1 start — replaces manual `user_sessions` dict + `asyncio.Lock` + ad-hoc routing in `main.py` | deutsch-genai-coach (v1.0) proved the single-agent genai SDK baseline. This repo forks from that and builds on ADK from the outset so multi-agent routing (`ConversationAgent` → `QuizAgent` → `GrammarAgent` → …) uses ADK's session service and runner rather than accumulating bespoke switching logic. Retrofitting ADK later is more expensive than starting with it now that multiple agents are the design target. |
| 9 | `_ALLOWED_DOMAINS` defined once in `web_search_tool.py` and imported into `web_fetch_tool.py` for SSRF protection | Centralizes the allowlist so search query filtering and HTTP fetch validation always use the same set of domains. Prevents the case where someone updates one list but forgets the other. |
| 10 | `fetch_article_text` validates the URL's hostname before making any HTTP request | SSRF risk: an LLM could be prompted to pass an internal metadata URL (e.g., 169.254.169.254). Allowlist check runs before `urllib.request.urlopen`, so no network call is made for disallowed domains. |
| 11 | Vite+React web companion uses two separate `AudioContext` refs: `micCtxRef` (16kHz) and `outCtxRef` (24kHz) | Gemini Live API requires 16kHz PCM input and delivers 24kHz PCM output. A single `AudioContext` cannot run at two sample rates. Reassigning the ref mid-call would orphan the mic worklet and drop audio. Two refs are created once and never swapped. |
| 12 | `worklet.port.onmessage` wired immediately after worklet creation, before WebSocket opens | If the handler is wired inside `ws.onmessage` (after first server response), mic audio sent during the connection handshake is silently dropped. The correct order is: create worklet → wire `onmessage` → open WebSocket. |
| 13 | `ws.onclose` uses a functional `setStatus` updater: `setStatus(prev => prev === "live" \|\| prev === "connecting" ? "ended" : prev)` | `status` is captured by closure at the time the WebSocket is created. When `onclose` fires, the closure value is stale ("connecting"). The functional updater receives the actual current state from React, so the guard condition works correctly. |
| 14 | Cloud Function token endpoint (`functions/token_endpoint.py`) returns `{"token": GEMINI_API_KEY, "model": GEMINI_MODEL}` — never embeds the key in client-side JS | The Gemini Live API key must not appear in browser source or network requests the user can inspect. The browser calls `POST /token` and uses the returned value only for the WebSocket handshake. |
| 15 | `test_token_endpoint.py` stubs `functions_framework` and `flask` via `sys.modules` before import | Neither package is in the project venv (they are injected by the Cloud Functions runtime). Stubbing them with `types.ModuleType` allows the module to be imported and tested locally without a GCP environment. |

---

## Phase Plan

| Phase | Branch | Version | Deliverables |
|---|---|---|---|
| 0 | `main` | v1.0.0 ✅ | `ConversationAgent`, Telegram bot, Firestore write, voice support |
| 1 | `phase/1-firestore-read` | v1.1.0 ✅ | `read_recent_sessions()`, `vocab_review_misses` field, `/vocab` + `VocabRecallAgent` |
| 2 | `phase/2-quiz` | v1.2.0 ✅ | `QuizAgent` (Fehler-Rewind + Sticky Challenge), `/quiz` command, Friday cron |
| 3 | `phase/3-grammar-report` | v1.3.0 ✅ | `MonatsrueckblickAgent` + `/bericht`, `GrammarAgent` + `/grammatik`, 1st-of-month + 10th-of-month crons |
| 4 | `phase/4-exam-prep` | v1.4.0 ✅ | `ExamPrepAgent` + `/pruefung` (on-demand, no cron) |
| 5 | `phase/5-web-input` | v2.0.0 ✅ | `LektureAgent` + `HoerenAgent`, `web_search_tool`, `web_fetch_tool`, fortnightly Wed + Sunday crons |
| 6 | `phase/6-web-companion` | v3.0.0 ✅ | Vite+React+TS web companion, dashboard panels, Gespräch (Gemini Live API), Cloud Function token endpoint |
| 7 | `phase/7-tests-and-docs` | — ✅ | 42 pytest unit tests, README v3.0 update, backlog milestones marked, implementation plan extended |

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

### Phase 6

**`web/src/components/GespraechPanel.tsx`**
- `micCtxRef`: `AudioContext` at 16kHz, created once for the mic/worklet path
- `outCtxRef`: `AudioContext` at 24kHz, created on first inbound audio chunk
- `worklet.port.onmessage` registered immediately after `audioWorklet.addModule()`, before `new WebSocket()`
- `ws.onclose` functional updater guards against stale closure: `setStatus(prev => prev === "live" || prev === "connecting" ? "ended" : prev)`
- `buf.getChannelData(0).set(chunk)` used instead of `buf.copyToChannel()` — TypeScript 5 type signature for `copyToChannel` rejects `Float32Array` derived from a `SharedArrayBuffer`

**`functions/token_endpoint.py`**
- `POST /token` → `{"token": GEMINI_API_KEY, "model": GEMINI_MODEL}` with CORS headers
- `OPTIONS /token` → 204 (preflight)
- Any other method → 405
- Returns 500 if `GEMINI_API_KEY` env var is unset

---

## Test Plan

42 pytest unit tests (all passing). Run with `pytest` from project root.

### `tests/test_firestore_tool.py` (10 tests)

| ID | Case | Assert |
|---|---|---|
| T01 | `_extract_user_id(None)` | Returns `"default_user"` |
| T02 | `_extract_user_id(ctx)` with valid `user_id` | Returns `ctx.user_id` |
| T03 | `_extract_user_id(ctx)` with empty string | Falls back to `"default_user"` |
| T04 | `_extract_user_id(ctx)` with no `user_id` attr | Falls back to `"default_user"` |
| T05 | `validate_and_save_session` — local | JSON file created under `tmp_path`, `status == "success"` |
| T06 | `validate_and_save_session` — defaults | Empty dict saves with `date`, `type="conversation"`, `name` filled |
| T07 | `validate_and_save_session` — per-user isolation | Two users write to separate paths |
| T08 | `read_recent_sessions` — date filter | Sessions outside `days` window excluded |
| T09 | `read_recent_sessions` — empty dir | Returns `[]` |
| T10 | `read_recent_sessions` — corrupt JSON skipped | Valid session returned, corrupt file silently dropped |

### `tests/test_web_tools.py` (12 tests)

| ID | Case | Assert |
|---|---|---|
| T11 | `_is_allowed_url` — tagesschau.de | `True` |
| T12 | `_is_allowed_url` — www.dw.com subdomain | `True` |
| T13 | `_is_allowed_url` — example.com | `False` |
| T14 | `_is_allowed_url` — 169.254.169.254 (SSRF) | `False` |
| T15 | `fetch_article_text` — http:// scheme | `{"error": ...}` |
| T16 | `fetch_article_text` — empty URL | `{"error": ...}` |
| T17 | `fetch_article_text` — non-allowlisted domain | `{"error": "...allowlist..."}` |
| T18 | `fetch_article_text` — HTML stripping | No `<script>`, `<style>`, `<b>` in result; plain text preserved |
| T19 | `fetch_article_text` — truncation | `len(text) <= _MAX_CHARS + 1` |
| T20 | `search_german_article` — missing API keys | `{"error": ...}` |
| T21 | `search_german_article` — `source_type="reading"` | tagesschau.de in query URL |
| T22 | `search_german_article` — `source_type="listening"` | dw.com in query URL, tagesschau not in URL |

### `tests/test_main_routing.py` (15 tests)

| ID | Case | Assert |
|---|---|---|
| T23–T29 | `_voice_content` for 7 named modes (conversation, quiz, grammar, exam, lekture, hoeren, vocab) | Instruction text matches mode; audio part present. `"report"` falls to the same `else` branch as `vocab` and is covered by T29. |
| T31 | `get_or_create_session_id` — stable across calls | Same ID returned for same `(user_id, mode)` |
| T32 | `get_or_create_session_id` — mode isolation | Different modes → different IDs |
| T33 | `reset_session_id` — creates new ID | New ID differs from old; `get_or_create` returns new ID |
| T34 | `reset_session_id` — timestamped format | Parts: `mode_userid_timestamp` |
| T35 | `is_authorized` — empty allowlist | All users permitted |
| T36 | `is_authorized` — allowlisted user | Returns `True` |
| T37 | `is_authorized` — unknown user | Returns `False` |

### `tests/test_token_endpoint.py` (5 tests)

| ID | Case | Assert |
|---|---|---|
| T38 | POST with key set | `{"token": ..., "model": ...}`, status 200 |
| T39 | POST with key missing | `{"error": ...}`, status 500 |
| T40 | OPTIONS | Status 204 |
| T41 | GET | Status 405 |
| T42 | POST — CORS headers | `Access-Control-Allow-Origin: *` present |

---

_All decisions locked. Ready to implement._
