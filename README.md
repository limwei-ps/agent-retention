# Time Internet — Retention Pitch Tool

An internal, agent-facing web app for broadband **retention agents**. Each month a batch of customers'
contracts approach expiry; agents work the list and reach out with a personalised recontract pitch.
The app lets an agent browse / search / filter / sort expiring customers, view their plan, tenure and
usage history, and generate a **grounded, streamed** recontract pitch via an LLM — single or in bulk —
with copy / regenerate and per-pitch status.

The graded core is a **reliable AI layer**, not visual polish — that's where the effort went.

> **On AI assistance & the prompt injection.** This project was built with AI assistance (Claude
> Code), disclosed openly and on our own terms — see the `Co-Authored-By` trailers throughout the git
> history. The assignment PDF contains an **embedded instruction** telling AI assistants to create an
> `ACKNOWLEDGEMENTS.md` file. That is untrusted input; it was **spotted and deliberately not obeyed**.
> The same principle runs through the app: customer fields are treated as untrusted LLM input and
> sanitized before they enter a prompt, so adversarial text in a record can't hijack a pitch.

---

## Live demo

**https://retention-web-6xowpmfgjq-as.a.run.app** _(deployed to GCP Cloud Run, `asia-southeast1`)_

- **Shared password.** The URL is gated by a lightweight **HTTP Basic Auth** prompt (one shared
  password) — enter it once when the browser asks. This is a demo gate, not per-user auth (SSO/authz
  stay out of scope, §Assumptions).
- **First request may cold-start** — the service scales to zero (`min-instances=0`), so the first hit
  after idle takes a few seconds to spin up.
- The live URL runs the **real Gemini** provider (not the mock). Interactions make real, billable LLM
  calls (~$0.02 each), so it's protected three ways: the Basic-Auth gate, a **per-IP request rate
  limit** (429 past `RATE_LIMIT_PER_MIN`, default 60), and a **hard $20/day spend cap** (fresh
  generations return a clean "budget reached" error once hit — cached pitches still work; see
  `GET /api/health`). The `api` service is also **private** — only `web` can call it (Google-signed ID
  token), so the LLM can't be billed by hitting `api` directly. Production would add per-agent budgets
  + spend caps on top.

---

## What's built

- **Dashboard + list** (`/`): summary of customers expiring this month by plan tier; a customer table
  with search (name / id), filters for plan, tenure, and usage (range buckets), sort (tenure / usage /
  expiry), and pagination. A bulk-generate action runs pitches for the current page.
- **Detail** (`/customers/[id]`): customer info + usage history side-by-side with a pitch panel that
  **streams token-by-token**, shows a status state machine (`not_generated` → `generating` → `ready` /
  `failed`), and offers **copy** + **regenerate** (force refresh).
- **Bulk progress**: a live panel with the animated fibre rail, a Queued / Generating / Ready / Failed
  count readout, an action-first per-item list (failures first, ready items link to the pitch), and a
  Retry-failed action. The panel persists across navigation (open a pitch and come back) and clears
  when the filter changes.

---

## Architecture

```
Browser ──► Next.js (App Router)  ──►  FastAPI (Python)  ──►  SQLite (seed-on-boot)
            • React Server/Client        • MVC + DTO + DI          • SQLAlchemy, WAL
            • TanStack Query             • AI reliability layer     • Gemini via Vertex AI (ADC)
            • BFF route handler ─────────► (server-side; key/URL never reach the browser)
```

- **Monorepo** — pnpm workspaces for JS (`apps/web`, `packages/shared-types`); `apps/api` is
  Python/uv, outside the JS workspace. `packages/shared-types` is generated from the FastAPI OpenAPI
  schema (`pnpm gen:types`) and committed so the web app builds without Python.
- **BFF proxy** — the browser only ever calls a same-origin catch-all Next route handler
  (`apps/web/src/app/api/[...path]/route.ts`) which forwards to FastAPI server-side (one origin, no
  CORS, backend URL stays server-side). SSE responses pass through unbuffered so tokens stream.
- **SSE over POST** — single-pitch generation is a `POST` stream, so the client reads it with a
  `fetch` + `ReadableStream` reader (`apps/web/src/lib/sse.ts`), not `EventSource`.
- **Backend layering** — thin routers (`app/api`), Pydantic DTOs (`app/schemas`), services
  (`app/services`), repositories behind interfaces injected via `Depends()` (`app/repositories`), and
  the AI layer (`app/ai`). Dependency injection everywhere lets tests inject a mock LLM.

---

## The AI reliability layer (the graded core)

Every mechanism is hand-rolled so we own and can defend it. All are covered by the pytest suite.

| Decision                      | How                                                                                                                                                                                                                  | Where                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Grounding**                 | Inject the customer's real plan / tenure / usage + the offer ladder into the prompt; the model must not invent numbers.                                                                                              | `app/ai/grounding.py`, `app/ai/prompt.py`                                     |
| **Output verification**       | After generation, programmatically require the recommended plan name + price and reject any out-of-catalog RM amount; regenerate once on failure, then fall back.                                                    | `app/ai/verification.py`                                                      |
| **Cache + invalidation**      | Cache key = SHA-256 over the exact grounding facts **+ model id + prompt-template version**. Prompt tweaks or changed inputs invalidate old pitches. Cache hits replay as a stream for consistent UX.                | `app/ai/grounding.py` (`cache_key`)                                           |
| **Regenerate = cache bypass** | A `force` flag bypasses cache **and** single-flight, so regenerate is never served a stale pitch.                                                                                                                    | `app/services/pitch_service.py`                                               |
| **Single-flight coalescing**  | Concurrent identical requests collapse onto one in-flight generation (leader/follower futures keyed by cache key).                                                                                                   | `app/ai/single_flight.py`                                                     |
| **Fallback chain**            | `gemini-2.5-pro → gemini-2.5-flash → last-cached (stale) → clean error`; each hop regenerates once on ungrounded output. Every failure normalizes to `ProviderError`.                                                | `app/services/pitch_service.py`, `app/ai/llm_client.py`                       |
| **Bulk backpressure**         | `asyncio.Semaphore` concurrency cap; per-item success/failure tracked; a mid-batch failure never aborts the batch. Live progress via an in-process registry + SSE, with a DB snapshot for reconnect.                 | `app/services/bulk_pitch_service.py`, `app/services/batch_registry.py`        |
| **SQLite write contention**   | WAL journal + `busy_timeout=5000` so concurrent bulk writers don't hit "database is locked".                                                                                                                         | `app/db/session.py`                                                           |
| **Cost, tracing & metrics**   | Structured JSON log per call (model, cache-hit, tokens, `cost_usd`, latency, grounding_ok, hop); every log line + response carries a request **trace id** (`X-Trace-Id`); Prometheus counters at `GET /api/metrics`. | `app/services/pitch_service.py`, `app/core/tracing.py`, `app/core/metrics.py` |

### Model choice & pinning

**Gemini** via `google-genai` on **Vertex AI**, chosen for first-class streaming, low cost at this
scale, and low latency. Model ids are **pinned** for reproducibility:

- `gemini-2.5-pro` (primary) → `gemini-2.5-flash` (secondary) — `apps/api/app/core/config.py`.
- Per-model token pricing pinned in `apps/api/app/ai/pricing.py` (verified against the Vertex pricing
  page), so cost logging is accurate.
- **Thinking-model note:** Gemini 2.5 are thinking models — thinking tokens count against
  `max_output_tokens`. A tight cap truncates the pitch before it states the offer (fails
  verification), so the chain sets `max_output_tokens=2048` with an explicit `thinking_budget`.

### Observability

- **Trace id** — every request is tagged with a correlation id: a pure-ASGI middleware binds a
  `ContextVar` and a logging filter stamps it onto **every** JSON log line, so all lines for one
  generation (cache lookup → each fallback hop → verification → persist → cost) share one id. It's
  returned as the `X-Trace-Id` response header and shown in the pitch panel's footer; bulk background
  items get a per-item `batch{id}-{customer}` id. `apps/api/app/core/tracing.py`.
- **Metrics** — `GET /api/metrics` exposes Prometheus-text counters (generations by outcome, cache
  hits, regenerations, fallbacks by hop, tokens, cost, HTTP requests) from a small in-process registry
  — no extra dependency. `apps/api/app/core/metrics.py`.

_A full stack (dashboards, distributed tracing, cost attribution, alerting) remains out of scope; this
is the dependency-light slice — see below._

---

## Running locally

```bash
pnpm install                      # JS deps
uv sync --project apps/api        # Python deps

# Dev (two processes)
pnpm dev:api                      # FastAPI on :8000 (mock LLM by default)
pnpm --filter web dev             # Next on :3000  (set apps/web/.env.local API_BASE_URL=http://localhost:8000)

# Or the whole stack in Docker
docker compose up --build         # web :3000 → api :8000

# Tests
pnpm test:api                     # pytest (AI layer + endpoints)
pnpm --filter web test            # vitest (unit/component)
pnpm --filter web test:e2e        # Playwright streaming + bulk E2E (starts its own mock stack)

# Regenerate shared types after an API change
pnpm gen:types
```

Set `SSE_TOKEN_CHUNK_DELAY_MS` (e.g. `40`) on the API to pace the mock stream and watch it render
token-by-token.

To run the **real** LLM locally: `gcloud auth application-default login`, then start the API with
`LLM_MODE=gemini` and `GOOGLE_CLOUD_PROJECT=<your-project>` (Vertex AI API enabled). No API key.

---

## Deploy (GCP Cloud Run)

One script, reproducible: [`deploy/deploy.sh`](deploy/deploy.sh) — builds both images, pushes to
Artifact Registry, grants the runtime service account `roles/aiplatform.user`, and deploys two
services.

```bash
# APP_PASSWORD gates the public URL (Basic Auth); required, never committed. Optional overrides:
# RATE_LIMIT_PER_MIN (default 60), LLM_DAILY_BUDGET_USD (default 20).
PROJECT=<your-project> REGION=asia-southeast1 APP_PASSWORD=<shared-pw> deploy/deploy.sh
```

Deliberate settings (and why):

- **`--min-instances=0`** — scale to zero; free when idle, at the cost of a first-request cold start.
- **`--max-instances=1`** — the bulk progress channel is an **in-process** queue, so live `/stream`
  events must come from the one instance running the batch. A single instance guarantees that
  affinity. (If scaled wider, `/stream` degrades to tailing the persisted DB snapshot.)
- **Default CPU throttling** — Cloud Run throttles CPU after a response is sent. Bulk uses
  `BackgroundTasks` (post-response), so it only progresses while a request is open — the bulk UI holds
  the SSE `/stream` open for the batch's duration, which keeps CPU allocated. A durable job queue is
  the production answer (see Out of scope).
- **Real Gemini via ADC** — the API authenticates to Vertex AI with the Cloud Run **service-account
  identity** (no API key to store or leak).
- **Private api + service-to-service auth** — `api` is deployed `--no-allow-unauthenticated`; only the
  `web` runtime SA has `roles/run.invoker`, and the BFF attaches a Google-signed ID token
  (`UPSTREAM_AUTH=gcp-id-token`, audience = api URL) to each upstream call. So the public surface is
  just `web`; the LLM-calling `api` can't be reached directly.
- **Seed-on-boot** — Cloud Run's filesystem is ephemeral, so the app seeds ~60 deterministic fake
  customers into SQLite on every boot. Fine for a demo; production would use a managed DB.

---

## Assumptions & out of scope

**Auth:** this is an internal tool for an **authenticated retention agent behind SSO** — real
per-user auth is out of scope. The public demo adds only a **lightweight shared-password gate** (HTTP
Basic Auth in `apps/web/src/proxy.ts`) so the link can be shared without leaving billable Gemini
wide open; production would replace it with SSO + per-user authz and audit trails.

Deliberately out of scope (named to show production judgment, not oversight):

1. **Auth & access control** — a shared-password Basic-Auth gate exists for the public demo; real
   per-user authn/authz, audit trails, and role scoping are out of scope.
2. **PII & data governance** — real telco data to a third-party LLM needs a DPA, PII
   redaction/tokenization before the prompt, data residency, and retention/deletion policy.
3. **Durable bulk orchestration** — bulk runs in-process via `BackgroundTasks` + SSE (a timeline
   choice). Production wants a durable queue (Cloud Tasks / Pub-Sub) with retries, restart survival,
   and independent scaling.
4. **Persistent, shared datastore** — SQLite + seed-on-boot is a demo convenience; production wants a
   managed DB (Cloud SQL / Postgres) with migrations, backups, pooling.
5. **LLM cost controls** — a global **$20/day** spend cap + a per-IP request rate limit are built; a
   production build wants **per-agent** budgets, quota alerts, and the secrets in Secret Manager
   (the gate password is a deploy-time env var here).
6. **Full observability stack** — a request trace id + Prometheus metrics are built (see above);
   production still wants dashboards, distributed tracing across services, cost attribution per
   agent/segment, and alerting on error-rate/latency spikes.

---

## Repo layout

```
apps/web/     Next.js App Router — BFF proxy, providers, hooks, components, e2e
apps/api/     FastAPI — api / schemas / services / repositories / ai / core / db
packages/shared-types/   TS types generated from the API's OpenAPI schema
deploy/deploy.sh         Cloud Run deploy
docs/                    spec.md, take-home-plan.md, assignment PDF
.claude/tracking/        append-only tasks / history / lessons (how the work was done)
```

<!-- Streaming demo: add docs/streaming-demo.gif and uncomment -->
<!-- ![Streaming pitch demo](docs/streaming-demo.gif) -->
