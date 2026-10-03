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
| v4.0.0 | Infrastructure as code | Terraform provisioning + GCP Budget Alerts; deploy from zero in one command |
| v4.1.0 | Cost visibility | Billing API proxy Cloud Function; cost panel in web companion |
| v4.2.0 | Writing coach with image evaluation | `SchreibAgent` — Gemini Vision evaluates handwritten/typed B2 emails against /45 rubric |

---

## v1.0.0 — Foundation ✅

- `ConversationAgent`: multi-turn B2 conversation, text + voice, 11 mistake categories, B2-Umformulierung
- `validate_and_save_session` Gemini tool: dual-destination (local JSON / Firestore)
- Telegram bot: `/start`, text handler, voice handler, per-user `asyncio.Lock`
- Access control: `ALLOWED_TELEGRAM_USERS` filter
- Cloud Run + Cloud Scheduler deployment specs
- `test_agent_cli.py` standalone local test runner

---

## v1.1.0 — Cross-session memory + vocab recall ✅

- `read_recent_sessions(user_id, days)` in `firestore_tool.py` — unlocks all downstream history features
- `vocab_review_misses: string[]` field added to `session_schema.json`
- `VocabRecallAgent`: reads misses from last 14 days across all session types; noun-article + verb-infinitive SRS drill; up to 12 words per session
- `/vocab` Telegram command

---

## v1.2.0 — Adaptive quiz ✅

- `QuizAgent`: game-show format, 4–5 rounds, one question per turn
- **Fehler-Rewind**: reads all past `mistakes[]` from Firestore, tallies category recurrence across sessions, weights questions toward persistent errors
- **Sticky Challenge**: if any mistake category appears 3+ times in the last 14 days, opens with a targeted 3-question micro-drill
- `/quiz` Telegram command
- Friday 09:00 Berlin Cloud Scheduler cron

---

## v1.3.0 — Grammar deep-dive + monthly report ✅

- `MonatsrueckblickAgent`: aggregates all Firestore sessions from past 30 days; outputs mistake category tallies, vocab growth curve, session counts by type, reuse rate, and 3 focus areas for next month; saves `type="review"` with `date=YYYY-MM-01`
- `GrammarAgent`: 12-topic monthly rotation (Konjunktiv II, Passiv, Relativsätze, Genitiv, Infinitivkonstruktionen, Modalpartikeln, Wortbildung, Adjektivdeklination, Indirekte Rede, Temporalangaben, Präpositionen mit Kasus, Satzverbindungen); reads Monatsrückblick to align topic with weakest category; 3 exercise types per session (fill-blank, transformation, free production)
- `/bericht` Telegram command + 1st-of-month cron
- `/grammatik` Telegram command + 10th-of-month cron

---

## v1.4.0 — Exam preparation ✅

- `ExamPrepAgent`: on-demand via `/pruefung`; four selectable components:
  - **Schreiben**: official telc /45 rubric (Inhalt 15, Aufbau 10, Grammatik 10, Wortschatz 10)
  - **Sprechen Teil 1**: 5-step monologue scaffold
  - **Sprechen Teil 2+3**: discussion with Konjunktiv I required; partner-style challenge
  - **Trap Drill**: 5 MC question types (word-match trap, extreme words, own-logic trap, opinion-shift signal, negation flip)
- No Firestore save (practice mode only); summary on `/finish`
- No cron — on-demand only

---

## v2.0.0 — Real-world input (reading + listening) ✅

**Requires:** Google Custom Search API key + `web_search_tool.py` + `web_fetch_tool.py`

- `LektureAgent`: searches for a real 300–500 word German article (tagesschau, Spiegel, Handelsblatt 💼, Heise 💼); pre-teaches 5 vocab items; 6 comprehension question types; saves `type="reading"` with `source_url`
- `HoerenAgent`: fetches a DW or Easy German episode; pre-teaches 3 transcript words; one theme drives both comprehension questions and translation paragraph (sentence-by-sentence B2-Umformulierung); saves `type="listening"`
- `/lektuere` command + fortnightly Wednesday cron
- `/hoeren` command + Sunday cron

---

## v3.0.0 — Web companion (dashboard + real-time voice calls) ✅

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

## v4.0.0 — Infrastructure as code

**Value: High.** Without this, deploying to a fresh GCP project requires running ~15 ordered `gcloud` commands with no rollback. Terraform gives reproducible deploys, state tracking, and infra as version-controlled code.

**Scope: `terraform/` directory covering:**

| Resource | Terraform type |
|---|---|
| Cloud Run service (bot) | `google_cloud_run_v2_service` |
| Cloud Function (token endpoint) | `google_cloudfunctions2_function` |
| Firestore database | `google_firestore_database` |
| Cloud Scheduler jobs (×5) | `google_cloud_scheduler_job` |
| GCP Billing Budget + alerts | `google_billing_budget` |
| IAM bindings for all services | `google_*_iam_member` |

**Budget alert** (bundled here, low effort once Terraform is wired):
- Monthly budget cap set via `terraform.tfvars` variable
- Email alerts at 50% / 90% / 100% of budget threshold
- Pub/Sub topic for programmatic subscribers (e.g. future bot-side enforcement)

**Out of scope for this milestone:** Firebase Hosting (managed via `firebase deploy`, Terraform support is partial); bot-side budget enforcement (disabling paid commands when threshold is hit — separate item).

---

## v4.1.0 — Cost visibility panel (candidate)

**Value: Medium.** GCP Billing API has a ~24-hour lag, so this shows yesterday's spend, not real-time. Still useful for monthly awareness.

**What the panel shows:**
- Current month estimated spend (total + breakdown by service: Gemini, Cloud Run, Cloud Functions, Custom Search API, Firestore, Scheduler)
- Budget remaining (budget cap − current spend)
- Month-over-month spend trend (bar chart, last 6 months)

**Implementation:**
- Cloud Function `GET /billing-summary` — proxies GCP Billing API (`billingaccounts.services.list`); the billing account credential stays server-side
- New `CostPanel` React component in the web companion — calls `/billing-summary` on dashboard load
- **Prerequisite:** `billing.accounts.get` IAM permission on the billing account (trivial for a personal GCP account; needs review for org accounts)
- **Prerequisite:** v4.0.0 (Terraform) — budget cap value read from the same `terraform.tfvars` variable so panel and alerts stay in sync

**User-settable budget:** via `terraform.tfvars` + `terraform apply`. Web UI for budget updates is out of scope — Terraform variable is simpler and keeps the change version-controlled.

---

## v4.2.0 — Writing coach with image evaluation (candidate)

> Not yet committed to. Added to backlog for scoping before implementation.

**Concept:** Generate a random telc B2 Schreiben task on demand, accept the learner's handwritten or typed response as a Telegram photo, and evaluate it from an examiner's perspective.

**User flow:**
1. Learner sends `/schreiben` → agent generates a random task prompt (formal email, complaint, request, etc.) drawn from past telc B2 exam formats
2. Learner writes their response (on paper or digitally), photographs it, and sends the image back via Telegram
3. Agent processes the image via Gemini Vision, extracts the text, evaluates it against the official /45 rubric (Inhalt 15, Aufbau 10, Grammatik 10, Wortschatz 10), and returns:
   - A rubric breakdown with per-category scores and justification
   - A corrected version of the full email at B2 level
   - 2–3 specific improvement notes for the next attempt
4. Session saved as `type="writing"` with rubric scores in `stats` and mistakes in `mistakes[]`

**Technical requirements:**
- Telegram photo handler (`MessageHandler(filters.PHOTO, ...)`) — downloads the image bytes, passes to Gemini Vision
- `SchreibAgent` — `LlmAgent` with `SCHREIBEN_SYSTEM_PROMPT` and `validate_and_save_session` tool
- `SCHREIBEN_SYSTEM_PROMPT` — task bank (10–15 prompts), vision-aware evaluation instructions, /45 rubric enforcement
- No new tools needed — Gemini Vision handles image-to-text natively via the multimodal content API

**Distinguishes from `ExamPrepAgent`:** `ExamPrepAgent` is text-only and does not save. `/schreiben` is photo-in, structured feedback out, and saves to history so the rubric scores are visible in the dashboard.

---

## Dev tooling (not versioned features)

### Google Cloud MCP servers + ADK MCP integration (candidate)

**ADK MCP support — confirmed available in ADK 2.11.0:**

ADK ships built-in MCP client support. The `MCPToolset` class (note: all-caps, not `McpToolset`) in `google.adk.tools.mcp_tool` lets an agent connect to any MCP server and dynamically load its tools — no custom wrapper needed. Requires the mcp extra:

```bash
pip install "google-adk[mcp]"
```

Once installed, an agent can connect via stdio (local subprocess) or SSE/HTTP (remote, e.g. Cloud Run):

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

my_agent = LlmAgent(
    name="my_agent",
    model=config.DEFAULT_MODEL,
    instruction=MY_PROMPT,
    tools=[MCPToolset(connection_params=...)],
)
```

**When ADK MCPToolset applies to this project:**

- **Not applicable** to the web companion or Cloud Functions — those are React + plain Python HTTP handlers, not ADK agents. The v4.1.0 cost panel Cloud Function should call the Billing API directly.
- **Applicable** to a future Telegram bot command (e.g. `/kosten`) backed by an ADK agent that connects to `observability-mcp` to fetch spend data and answer conversationally: _"You've spent $4.20 this month, 68% on Gemini API."_ This would be a separate backlog item, not part of v4.1.0.

**Two GCP MCP servers relevant to this project:**

- **gcloud-mcp** (`googleapis/gcloud-mcp`) — Claude Code dev sessions only: check Cloud Run health, tail logs, update env vars, inspect Cloud Scheduler jobs without manual `gcloud` commands.
- **observability-mcp** — Claude Code debugging: query Cloud Run and Cloud Functions logs directly. Also the MCP server a future `/kosten` ADK agent would connect to for billing metrics.

Both are dev-workflow improvements (Claude Code MCP config, `.claude/settings.json`). Neither changes the app itself unless a `/kosten` agent is built.

**ADK dev UI:** `adk web` ships with ADK and provides a local browser UI for inspecting agent runs and tool call events — useful without any MCP setup.

---

## Out of scope

- Notion MCP integration (replaced by Firestore in this repo)
- Dictation mode (covered adequately by the voice note path in `ConversationAgent`)
