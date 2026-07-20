# Spec / PRD — Time Internet Retention Tool

Concrete, buildable design derived from `docs/take-home-plan.md` (strategy) and
`docs/take_home_assignment_fangwei.pdf` (source of truth). The **AI layer (§4)** is the most detailed
section because it is weighted most heavily. This spec is **versioned, not frozen** — amend + commit
if reality forces a change.

- Stack & conventions: see `docs/take-home-plan.md` §9.
- Scope boundary (build-well vs. stub): see `docs/take-home-plan.md` §4.
- **Monorepo:** pnpm workspaces — `apps/web` (Next.js), `apps/api` (FastAPI/uv), `packages/shared-types`
  (TS contract types **generated from the FastAPI OpenAPI schema** via `pnpm gen:types`).

---

## 1. Domain model

### 1.1 Plan catalog (fixed — grounds the LLM on real names/prices)

| id | name | speed (Mbps) | list price (RM/mo) |
|----|------|--------------|--------------------|
| `fibre_100`  | TIME Fibre 100  | 100  | 99  |
| `fibre_300`  | TIME Fibre 300  | 300  | 129 |
| `fibre_500`  | TIME Fibre 500  | 500  | 159 |
| `fibre_1000` | TIME Fibre 1Gbps | 1000 | 199 |

Ordered tiers; "next tier up" = the next row. `fibre_1000` has no upgrade rung (upsell falls back to
a larger discount). Currency **MYR**. Catalog lives in one config module, imported by seeding, offer
logic, and grounding — single source of truth.

### 1.2 Customer

| field | type | notes |
|-------|------|-------|
| `id` | str (`CUST-00042`) | stable, searchable |
| `name` | str | searchable |
| `email` / `phone` | str | contact; not used in grounding |
| `current_plan_id` | FK → catalog | |
| `monthly_price` | int (RM) | may sit below list (legacy promo) — feeds discount math |
| `tenure_months` | int | months as a customer |
| `contract_end_date` | date | **seeded so a meaningful slice ∈ current month** |
| `usage_history` | list[{month: `YYYY-MM`, gb: int}] | last 12 months |
| `avg_monthly_gb` | int (derived) | sort/filter scalar |
| `last_month_gb` | int (derived) | drives recommendation |
| `region` | str | realism only |

**Usage archetypes** (drive the recommended offer, seeded ~evenly):
- *flat-low* — steady, well under plan capacity → **Retain** (price-sensitive).
- *climbing* — trending up toward the plan ceiling → **Value upgrade**.
- *heavy* — at/over a soft cap for the tier → **Upsell**.

### 1.3 Offer ladder (the retention product — "retain while making additional profit")

Deterministically derived per customer from current plan + usage archetype + tenure. Three rungs:

| rung | type | target plan | price rule | intent |
|------|------|-------------|-----------|--------|
| `retain` | discount | same plan | ~15% off `monthly_price`, 24-mo term | defensive, lowest margin |
| `value_upgrade` | upgrade | next tier | ≈ current `monthly_price`, 24-mo | same spend, stickier |
| `upsell` | upgrade | next tier | current + ~RM30 (still < list), 24-mo | highest margin |

Each rung: `{ type, target_plan_id, monthly_price, term_months, vs_current_delta, headline }`.
A `recommended` field points at one rung via the rule: heavy→`upsell`, climbing→`value_upgrade`,
flat-low or high tenure→`retain`; top-tier customers → deeper `retain` discount. The **pitch leads
with `recommended`** and may offer the `retain` rung as a step-down.

### 1.4 Pitch

| field | type | notes |
|-------|------|-------|
| `customer_id` | FK | |
| `status` | enum | `not_generated` / `generating` / `ready` / `failed` |
| `text` | str | generated pitch |
| `cache_key` | str | see §4.3 |
| `model` | str | model id used (or `mock`) |
| `prompt_tokens` / `completion_tokens` | int | cost accounting |
| `cost_usd` | float | tokens × pinned price constants |
| `grounding_ok` | bool | passed output verification (§4.4) |
| `created_at` | datetime | |

---

## 2. Seeding

- 50–100 customers via **Faker** (seeded RNG for reproducibility).
- `contract_end_date` spread across the next ~90 days with a deliberate cluster in the **current
  calendar month** (so the dashboard is non-trivial).
- Usage archetypes assigned ~evenly; `usage_history` shaped to match the archetype.
- Offer ladder computed at seed time (or on read) from the deterministic rule.
- **Seed-on-boot** into SQLite (Cloud Run filesystem is ephemeral — see plan §7).

---

## 3. API (FastAPI)

All responses are Pydantic DTOs. Envelope for lists: `{ data, page, page_size, total }`.

| method + path | purpose | params / body |
|---------------|---------|---------------|
| `GET /api/customers` | list | `search` (name/id), `plan`, `tenure_min`/`tenure_max` (months, `le=1200`), `usage_min`/`usage_max` (avg GB, `le=1_000_000`), `expiring` (bool), `sort` (tenure\|avg_gb\|contract_end_date), `order`, `page`, `page_size` |
| `GET /api/customers/{id}` | detail | → customer + usage_history + offer ladder + latest pitch |
| `GET /api/dashboard/summary` | dashboard | → count expiring **this month** grouped by plan tier |
| `POST /api/customers/{id}/pitch` | generate (foreground stream) | body `{ force?: bool }`; **SSE** token stream, generated in-request; `force` = cache bypass |
| `POST /api/pitches/bulk` | bulk start (background) | body `{ filter }`; starts a **BackgroundTask** semaphore fan-out; returns `{ batch_id }`; per-item status persisted |
| `GET /api/pitches/bulk/{batch_id}/stream` | bulk progress (**SSE**) | live per-item progress events from the running task |
| `GET /api/pitches/bulk/{batch_id}` | bulk status (poll / reconnect) | DB-persisted snapshot `{ total, done, succeeded, failed, items[] }` |
| `GET /api/health` | health | → `{ status, llm_mode }` |

**"This month"** = server-local calendar month `[first_day, last_day]`; timezone fixed in config
(Asia/Kuala_Lumpur) and documented.

---

## 4. AI layer (weighted most heavily)

### 4.1 Grounding
Prompt is assembled from a structured context block: customer name, current plan (name + price),
tenure, `avg_monthly_gb` + `last_month_gb`, and the **full offer ladder with the `recommended` rung
flagged**. The model is instructed to quote **only** plans/prices present in that block and to lead
with the recommended offer. Customer free-text fields are **sanitized** before insertion
(second-order injection defense) — treated as data, never instructions.

### 4.2 Prompt as a product
Template enforces: a warm opener referencing tenure/usage, the recommended offer with its concrete
price + term, one clear CTA, on-brand tone, ~120–160 words. Template carries a
`PROMPT_TEMPLATE_VERSION` constant.

### 4.3 Caching / idempotency
`cache_key = sha256(grounding_snapshot + PROMPT_TEMPLATE_VERSION + model_id)` where
`grounding_snapshot` = the exact facts fed to the model (plan, price, tenure bucket, usage buckets,
contract_end month, serialized offer ladder). Same inputs → cache hit; any relevant change
invalidates. **Regenerate** sends `force: true` → bypasses read, writes a fresh entry. Cache-hit on a
stream: replay the stored text as a stream for consistent UX.

### 4.4 Output grounding verification
After generation, assert every RM amount in the output ∈ the allow-list (customer's current price ∪
catalog prices ∪ offer-ladder rung prices) and that the recommended plan name + price are present. The
plan-name check targets **numeric plan identifiers** — `<brand> Fibre/Fiber <digit…>` (all catalog
names are digit-suffixed, e.g. `TIME Fibre 100` … `TIME Fibre 1Gbps`) — so it flags misspellings and
numeric fabrications (`TIME Fiber 300`, `TIME Fibre 9000`, `MaxSpeed Fibre 900`) without false-flagging
ordinary prose ("TIME Fibre plans", "Our Fibre network"). On failure: mark `grounding_ok=false` and
**auto-regenerate once**; if it fails again, advance the fallback chain rather than serve a hallucinated
pitch. This turns "prompted carefully" into a reliability guarantee.

_Accepted residual gap:_ a fabricated brand with a **non-numeric** suffix ("MaxSpeed Fibre Ultra")
isn't caught by the plan-name regex — but a fabricated **price** still is, and the model is instructed
to quote only listed plans. See `docs/take-home-plan.md` §8.

### 4.5 Concurrency / backpressure
Bulk generation runs under an **asyncio semaphore** (concurrency cap, config constant). **Single-
flight**: an in-flight generation per `cache_key` is shared so two agents on the same customer don't
fire two LLM calls. Watch SQLite write-lock contention — serialize writes / short transactions.

### 4.6 Fallback
`gemini (primary) → gemini (flash/secondary) → last cached pitch → clean error state`. Each hop is
logged. Fallback is unit-tested by forcing provider errors against the mock.

### 4.7 Failure handling (bulk)
Per-item status tracked (`succeeded` / `failed` + error). A mid-batch failure never aborts the batch;
the progress payload shows exactly which succeeded and which failed, with retry of failed-only.

### 4.8 Cost & observability
Structured JSON logs per call: `customer_id, model, cache_hit, prompt/completion tokens, cost_usd,
latency_ms, grounding_ok, fallback_hop`. Cost from pinned per-model price constants. Pin the exact
Gemini model id in config + README.

**Cost enforcement (public-demo hardening):** beyond logging, a hard **daily spend cap**
(`LLM_DAILY_BUDGET_USD`, in-process `DailyBudget`, `app/core/budget.py`) refuses a fresh generation
once the day's estimated cost is reached — cache hits + last-cached fallbacks stay free; state in
`GET /api/health`. At the edge, the `web` service adds an HTTP **Basic-Auth gate** + a **per-IP
request rate limit** (`apps/web/src/middleware.ts`, `RATE_LIMIT_PER_MIN`) so the shared public URL
isn't open to anonymous, unbounded billable calls. Both are demo-scope (single-instance, env-var
secret); production wants per-agent budgets + SSO + Secret Manager.

### 4.9 LLM mode
`LLM_MODE=mock|gemini`. **Mock** = deterministic, grounded generator (echoes the recommended offer)
— used in tests and as the deployed default. **Gemini** via `google-genai` behind the flag.

**Auth (amended in Phase C): Application Default Credentials on Vertex AI, not an API key.** The chain
builds one shared `genai.Client(vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=…)`; `gemini`
mode requires `GOOGLE_CLOUD_PROJECT` and errors cleanly without it. Two hops (`pro → flash`) share the
client; each call is bounded by `GEMINI_TIMEOUT_S` (per-chunk stall → `ProviderError` → next hop).

**Thinking-model budget (Phase C teeth-step finding):** Gemini 2.5 are thinking models and thinking
tokens count against `max_output_tokens`; a tight cap truncates the pitch (`finish_reason=MAX_TOKENS`)
before it states the offer, failing §4.2 verification. The chain therefore sets `max_output_tokens=2048`
with an explicit `thinking_budget`. This is the class of defect only reading live output catches — unit
tests use a fake client that ignores generation config.

### 4.10 Execution model (single vs. long-running bulk)
- **Single pitch = foreground SSE**, generated in-request so the agent watches tokens stream. No
  background job — streaming is the whole point. Cache-hit replays stored text as a stream.
- **Bulk = FastAPI `BackgroundTasks` + SSE.** `POST /pitches/bulk` starts a background semaphore
  fan-out (§4.5) and returns `{ batch_id }` immediately. The task publishes progress to an **in-process
  channel** (an `asyncio.Queue` keyed by `batch_id`) and **persists each per-item result to SQLite** as
  it completes. The client watches live progress over a **separate SSE channel**
  (`GET /pitches/bulk/{batch_id}/stream`); the DB rows are the durable snapshot so a reconnecting or
  late-joining client catches up via `GET /pitches/bulk/{batch_id}`. A mid-batch failure is recorded
  per item and never aborts the batch (§4.7).
- **Single-instance affinity:** the progress `asyncio.Queue` is **in-process**, so `/stream` only
  delivers live events from the instance actually running the batch. This holds under `min-instances=1`
  / `max-instances=1` (our deploy). If it ever scales beyond one instance, `/stream` must **fall back to
  tailing the DB snapshot** (poll the persisted per-item rows) instead of the in-memory queue — the
  implementation degrades to that path automatically. Cross-instance live fan-out needs a shared broker
  (Redis pub/sub) — part of the durable-queue upgrade below.
- **Cloud Run deploy note:** `BackgroundTasks` run *after* the response, and Cloud Run throttles CPU
  once the response is sent. The batch therefore needs **CPU-always-allocated** (or `min-instances=1`
  with an instance kept warm via a Cloud Scheduler ping) so the fan-out isn't throttled — an
  operational setting, documented in the README deploy section.
- The production-grade alternative (a durable job queue) is **out of scope by timeline** — see
  `docs/take-home-plan.md` §8.

---

## 5. Frontend (Next.js App Router)

Structure per `docs/take-home-plan.md` §9. Screens:

- **Dashboard + list** (`/`): summary cards (expiring this month by plan tier) + customer table with
  search, plan filter, sort (tenure / usage / expiry), pagination. Bulk-generate action on the
  current filtered segment.
- **Detail** (`/customers/[id]`): customer info + usage history on one side, pitch panel on the other
  (**side by side**). Pitch panel streams token-by-token, shows the status state machine
  (`not_generated`/`generating`/`ready`/`failed`), and offers **copy** + **regenerate** (force).
- **Bulk progress**: live X-of-N bar + per-item status list, fed by the bulk SSE/poll endpoint.

State: `PitchProvider` (per-pitch state machine), `FiltersProvider` (list query state), TanStack
Query for server state; `usePitchStream` consumes the SSE pass-through from the route handler.

Contract types are imported from `@retention/shared-types` (generated from the API's OpenAPI schema),
keeping the frontend DTOs in lockstep with the backend.

---

## 6. Deployment & out-of-scope

- Per-app Dockerfiles (`apps/web`, `apps/api`) + root docker-compose (local); **actual deploy to GCP
  Cloud Run** with **mock-LLM default** on the live URL; secrets via Secret Manager. Details +
  gotchas: plan §7.
- Deliberately out of scope (state in README): plan §8.

---

## 7. Traceability to the assignment

- 5 task bullets → §3 (list/detail/pitch/bulk/copy-regenerate).
- 5 frontend bullets → §5.
- 6 AI/production bullets → §4 (grounding, caching, fallback, rate-limit/concurrency, failure, cost).
- Tech constraints → §9 of the plan (TS, Next.js, Python/FastAPI, Gemini, SQLite, Docker, Cloud Run).
