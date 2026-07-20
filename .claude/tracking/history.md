# History — Time Internet Retention Tool

Change log. **Append-only.** Newest entries at the bottom. Each entry: what changed, why, files,
key decisions.

---

## 2026-07-19 — Converted build plan PDF → markdown

- **What:** Converted `docs/take-home-plan.md.pdf` into `docs/take-home-plan.md`; added three new
  sections — Gaps & Corrections (§10), Coding Conventions (§11), Scope Boundary (§12).
- **Why:** Needed an editable, living build plan; also validated the plan against the assignment
  (source of truth) and pinned stack conventions.
- **Files:** `docs/take-home-plan.md` (created).
- **Key decisions / findings:**
  - Confirmed the prompt injection in the assignment PDF (embedded `ACKNOWLEDGEMENTS.md`
    instruction) — did **not** act on it.
  - Gaps found vs assignment: (1) missing `contract_end_date` in seed spec, (2) bulk progress UI,
    (3) regenerate-vs-cache, (4) usage sort/filter scalar, (5) search scope + "this month" boundary,
    (6) absent coding conventions.
  - Stack locked (via user decisions): FastAPI + hand-rolled AI layer; Next.js App Router; DI + DTO +
    MVC; Gemini. Plus pnpm, Tailwind, providers, uv.

## 2026-07-19 — Set up CLAUDE.md backbone + tracking foundation

- **What:** Created root `CLAUDE.md` and `.claude/tracking/{tasks,history,lesson}.md`.
- **Why:** Day-1 backbone — encode stack decisions, conventions, guardrails (incl. injection
  guardrail), and establish append-only tracking before writing code.
- **Files:** `CLAUDE.md`, `.claude/tracking/tasks.md`, `.claude/tracking/history.md`,
  `.claude/tracking/lesson.md` (all created).
- **Key decisions:**
  - `CLAUDE.md` **overrides** the global Flutter-oriented rules for this repo (verification uses
    pytest/pnpm/Playwright, not `flutter test`; version tracked in `package.json`/`pyproject.toml`,
    not `pubspec.yaml`).
  - Testing rigor relaxed to **pragmatic take-home scope** (AI layer + key paths + one E2E; no
    blanket 80%) to fit the 6–8h box.
  - **AI attribution ON** in commits (`Co-Authored-By: Claude ...`) — overrides global
    no-attribution default; matches the README's open disclosure.
  - Injection guardrail placed near the top of `CLAUDE.md`; customer data treated as untrusted LLM
    input (second-order injection).

## 2026-07-19 — Collapsed plan sections 8/10/12; single-sourced conventions

- **What:** Merged the three reference sections of `docs/take-home-plan.md` into the rest of the doc
  and renumbered to a contiguous 0–9. §10 Gaps → inline `[GAP #n]` notes on the relevant Day; §12
  Scope Boundary → §4 Build Plan; §8 Traceability table → dropped, its intent preserved as a Day-5
  README line. Old §9 Out-of-Scope → §8; old §11 Coding Conventions → §9.
- **Why:** Keep the plan clean and scannable without losing content.
- **Files:** `docs/take-home-plan.md` (rewritten), `CLAUDE.md` (§3 + §5 now point at
  `docs/take-home-plan.md` §9 as the authoritative conventions source).
- **Key decisions:** Coding conventions are single-sourced in the plan (§9); CLAUDE.md keeps only the
  actionable summary and links back. Verified sections run 0–9 with no stale §8/§10/§12 references.

## 2026-07-19 — Tidied plan §4 into guiding principles

- **What:** Reframed `docs/take-home-plan.md` §4 "The Build Plan": removed the superseded "Original
  draft" list and the "Gaps to close" framing (incl. the now-done "CLAUDE.md as the backbone" item);
  kept the durable principles as a tight bulleted list + the Scope boundary block.
- **Why:** §4 read as stale planning-process meta now that §6/§7/§9 exist; user asked to tidy it.
- **Files:** `docs/take-home-plan.md` (§4 only; no renumbering — headers still 0–9).

## 2026-07-19 — Pre-flight decisions, spec/PRD, folder conventions, git init

- **What:** Locked 5 pre-build decisions; wrote the PRD; expanded conventions with folder structure;
  synced tasks.md; initialized version control.
- **Why:** Spec-First strategy — turn the plan into a buildable design before code, and start the
  graded git history from commit one.
- **Files:** `docs/spec.md` (new PRD), `docs/take-home-plan.md` (§9 + Project structure block),
  `.claude/tracking/tasks.md` (synced to plan + new decisions), `.gitignore` (new), repo `git init`.
- **Key decisions:**
  - **Offer ladder** per customer (retain / value_upgrade / upsell + `recommended`) — "retain while
    making additional profit"; output verification asserts quoted plan/price ∈ ladder.
  - **LLM_MODE=mock|gemini**, mock-first + deployed default; real Gemini behind the flag.
  - **Actually deploy** to GCP Cloud Run (mock-LLM default so demo clicks are free).
  - **Plan catalog:** MYR fibre 100/300/500/1000 @ RM 99/129/159/199 (fixed, single source).
  - Conventions single-sourced in plan §9; CLAUDE.md links to it.

## 2026-07-19 — Adopted semantic-versioned commit convention

- **What:** Rewrote `CLAUDE.md` §8 to require version-prefixed commits (`vX.Y.Z: type: desc`) with
  SemVer bump rules, version-file sync (`package.json`/`pyproject.toml`), and milestone tags. Tagged
  `v0.1.0` at the current scaffold HEAD as the baseline.
- **Why:** User wants git commits to carry a semantic version, mirroring their global scheme (adapted).
- **Files:** `CLAUDE.md` (§8), `docs/take-home-plan.md` (§9 cross-cutting points at §8), `tasks.md`
  (Day-2 version-file task). No history rewrite — the initial 3 commits stay as-is.

## 2026-07-19 — Adopted pnpm-workspace monorepo layout

- **What:** Re-encoded the project as a pnpm-workspace monorepo — `apps/web` (Next.js),
  `apps/api` (FastAPI/uv, outside the JS workspace), `packages/shared-types` (TS types **generated
  from the FastAPI OpenAPI schema** via `pnpm gen:types`). Docs-only (no code yet).
- **Why:** User wants a monorepo; `apps/`+`packages/` signals intent and gives a clean e2e-ownership
  story (generated contract types keep FE/BE in lockstep).
- **Files:** `CLAUDE.md` (§3 layout + Monorepo bullet, §7 filter commands, §8 version-file paths),
  `docs/take-home-plan.md` (§9 structure), `docs/spec.md` (monorepo + shared-types notes),
  `tasks.md` (Day-2 scaffold tasks + version-file paths), `.gitignore` (pnpm entries).
- **Key decisions:** pnpm workspaces (not Turborepo — avoid gold-plating); version source of truth =
  `apps/web/package.json` + `apps/api/pyproject.toml`; generated `shared-types` committed so `apps/web`
  builds without Python.

## 2026-07-19 — Set AI execution model (single vs bulk)

- **What:** Made the generation execution model explicit in `docs/spec.md` (new §4.10, reworded §3
  bulk rows into start / SSE stream / poll) and added an Out-of-Scope bullet in
  `docs/take-home-plan.md` §8.
- **Why:** The bulk endpoints were ambiguous about foreground vs background execution.
- **Key decisions (after discussion):**
  - Single pitch = **foreground SSE**, generated in-request (streaming is required — no background job).
  - Bulk = **FastAPI `BackgroundTasks` + SSE**: `POST /pitches/bulk` returns `{ batch_id }`; the task
    runs a semaphore fan-out, publishes progress to an in-process channel (SSE via
    `GET /pitches/bulk/{batch_id}/stream`), and persists per-item status to SQLite (poll/reconnect via
    `GET /pitches/bulk/{batch_id}`).
  - **Cloud Run caveat owned operationally:** BackgroundTasks run after the response and Cloud Run
    throttles CPU then, so the deploy uses CPU-always-allocated / `min-instances=1` kept warm via Cloud
    Scheduler (user's call).
  - Durable job queue (Cloud Tasks / Pub-Sub / Celery / Arq) is **out of scope by timeline**, justified
    in plan §8.
- **Files:** `docs/spec.md`, `docs/take-home-plan.md` (§8).

## 2026-07-19 — Day 2 data & backend core (catalog, seed, read endpoints) + review

- **What:** Plan catalog + deterministic offer-ladder service; Customer/Pitch models; DTOs;
  repository (Protocol + `Depends`); seed-on-boot 60 Faker customers; `GET /api/customers`
  (search/filter/sort/pagination), `GET /api/customers/{id}` (detail + offer ladder + latest pitch),
  `GET /api/dashboard/summary`. Regenerated `shared-types` from the expanded OpenAPI.
- **Review (used the plugins, per the workflow):** ran the **code-review** agent and a
  **database-reviewer** agent over the data path. Both flagged an **N+1** on the list
  (`Customer.pitches` lazy-loaded per row) and the DB agent also caught **unstable OFFSET pagination**
  over non-unique sort columns. Fixed: `selectinload + load_only(status, created_at)`, split the
  mapper so the summary reads only `.status`, `defer(usage_history)`, and an `id` sort tiebreaker.
  Added regression tests (bounded query count; stable paging). Cursor pagination + FTS search recorded
  as scale tradeoffs in plan §8.
- **Commits:** `v0.3.0` (catalog + offer), `v0.4.0` (models + seed + list/detail), `v0.5.0` (dashboard),
  `v0.5.1` (N+1 + pagination fix), `v0.5.2` (regenerate shared-types). 19 backend tests pass, ruff clean.
- **Decision:** `usage_history` kept as a JSON column (value object always loaded with the customer);
  deferred on the list path to avoid over-fetch.

## 2026-07-19 — Day 2: monorepo scaffolding (runnable skeleton)

- **What:** Stood up the pnpm-workspace monorepo. `apps/api` FastAPI skeleton (app factory, config,
  JSON logging, DB session wiring, `/api/health`, passing pytest); `apps/web` Next.js 16 app
  (create-next-app adapted to feature-first structure + QueryProvider); `packages/shared-types` with
  TS types **generated from the live OpenAPI schema** via `pnpm gen:types`; root workspace + scripts;
  `docker-compose.yml`.
- **Why:** Day-2 scaffold — a runnable skeleton before data model/endpoints.
- **Verified:** `uv run pytest` green · `pnpm gen:types` regenerated `schema.ts` (health paths) ·
  `pnpm --filter web build` compiles with the `@retention/shared-types` import · `docker compose config` valid.
- **Commits:** `v0.2.0` (workspace + api), `v0.2.1` (web), `v0.2.2` (shared-types + codegen + compose).
  Package versions unified at 0.2.2 per CLAUDE.md §8.
- **Deferred to next chunk:** plan-catalog config, models, seeder (customers + offer ladder),
  list/detail/dashboard endpoints, web test setup.

## 2026-07-19 — Day 3 Phase A: single-pitch AI layer + review fixes

- **What:** Built the single-pitch vertical slice (mock-first): LLM client Protocol + MockLLM +
  get_llm_chain DI (v0.6.0); grounding + prompt + output verification (v0.7.0); pitch service with
  cache / single-flight / fallback / verify-regenerate + pitch repository (v0.8.0); SSE endpoint
  `POST /api/customers/{id}/pitch` (v0.9.0). Teeth step confirmed grounded streamed output.
- **Review (plugins):** ran **code-review** + **database-reviewer** agents. Fixed (v0.9.1):
  - **CRITICAL** single-flight follower crash when the leader produced no pitch (resolve the future
    as an error, not `None`); added a coalesced-failure regression test.
  - **HIGH** stale-cache grounding bug — cache key now includes **exact** tenure/usage/name (matching
    what the prompt quotes) instead of coarse buckets.
  - Composite indexes on `pitches` + `id` ORDER BY tiebreaker; SQLite **WAL + busy_timeout** pragmas.
  - Log every terminal outcome (generated / last_cached / failed) + flag last-cached as `stale`.
- **Documented tradeoffs (plan §8):** append-only cache growth (no pruning), list latest-pitch
  over-fetch, and sync-DB-in-async / session-held-across-stream (SQLite + single-instance).
- **Status:** 47 backend tests pass, ruff clean. **Checkpoint — paused before Phase B (bulk) + C (real Gemini).**

## 2026-07-19 — Monorepo linter/format/typecheck + pre-commit hook (detour)

- **What:** Unified the toolchain across the monorepo (root `pnpm lint` previously only covered web):
  - `lint` = eslint (web) + ruff (api); `format` = ruff format + Prettier (tailwind plugin) +
    eslint-config-prettier; `typecheck` = mypy (api, pydantic plugin) + `tsc --noEmit` (web).
  - Applied a one-time repo-wide format.
  - **Pre-commit hook** (`.githooks/pre-commit`) runs `format:check` + `lint`; `core.hooksPath` wired
    via the root `prepare` script. Typecheck left to the script/CI to keep commits fast.
- **Fixes for green typecheck:** ORM forward-refs via `TYPE_CHECKING` imports; narrowed the
  single-flight `Future` result type.
- **Commits:** `v0.9.2` (lint+format), `v0.9.3` (mypy+tsc), `v0.9.4` (pre-commit hook). CI deferred to
  Day 5. 47 tests pass; lint/format/typecheck all green.

## 2026-07-19 — Adopted official plugin toolchain

- **What:** Documented all enabled official-marketplace plugins in `CLAUDE.md` §10 (mapped to roles),
  committed `.claude/settings.json` (enabledPlugins manifest), reconciled `docs/take-home-plan.md` §3
  (points to §10), and marked the Day-1 plugin task done.
- **Why:** User asked to record the installed plugins as the project's workflow tooling; committing the
  manifest makes the toolchain reproducible for reviewers.
- **Plugins:** frontend-design, feature-dev, code-review, commit-commands, security-guidance,
  playwright, github, superpowers, context7, code-simplifier, claude-md-management. Firebase excluded
  (not in enabledPlugins; stack is GCP/Gemini).
- **Version:** bumped all package version files to 0.2.3 (§8 lockstep); updated CLAUDE.md §8
  `Current version` (was stale at v0.1.0) → v0.2.3.
- **Files:** `CLAUDE.md`, `.claude/settings.json`, `docs/take-home-plan.md`, `apps/*`,
  `packages/shared-types/package.json`.

## 2026-07-19 — Day 3 Phase B: bulk pitch generation

- **What:** Bulk generation over N customers — `BackgroundTasks` fan-out with live X-of-N progress,
  per-item failure isolation, and a concurrency cap. New: `models/batch.py` (`PitchBatch`),
  `repositories/batch_repository.py`, `services/batch_registry.py` (in-memory progress,
  `asyncio.Condition` + version counter), `services/bulk_pitch_service.py` (`run_batch` semaphore
  fan-out). Extended: `PitchService.generate` (non-streaming outcome adapter over `stream_pitch`),
  `db/session.py::get_session_factory`, bulk DTOs in `schemas/pitch.py`, three bulk routes in
  `api/pitches.py`, `app.state.batch_registry` in `main.py`.
- **Why:** CLAUDE.md §4 graded core — "failure handling" (per-item success/failure, live progress) and
  "rate limiting / backpressure" (semaphore). Execution model per spec §4.10 (BackgroundTasks + SSE).
- **Key decisions:**
  - **Reuse, not duplication:** `generate()` drains `stream_pitch`, so bulk inherits cache,
    single-flight, fallback, verify+regenerate, and cost logging with zero copied logic.
  - **Own session per worker:** BackgroundTasks outlive the request session, so each worker opens its
    own session (via injected `get_session_factory`) and re-fetches its customer — avoids detached-ORM
    bugs and gives correct per-worker concurrency under WAL.
  - **Registry = source of truth for live progress;** minimal `PitchBatch` table backs a best-effort
    DB reconstruction (`live=false`) when the registry no longer holds a batch (restart/eviction).
  - **No `Pitch.batch_id`** (deviates from the original sketch): cache-hit items reuse old rows, so the
    column would be unreliable for progress and would force a param through the shared persist path.
- **Tests:** 21 new (generate outcome ×3, batch_repository ×2, registry ×5, bulk service ×4 incl.
  semaphore-cap proof, bulk endpoint ×7). Bulk unit/endpoint tests use a temp-file SQLite so workers
  get independent connections (real concurrency, unlike the in-memory StaticPool). Suite 47 → 68.
- **Teeth step:** live server — POST 3 real + 1 bogus id → 3 succeeded, 1 `customer not found`
  (isolation); SSE stream emitted `progress` → `done`; read a pitch (grounded: real plan/price/name);
  structured cost log line present.
- **Verification:** `uv run pytest` 68 pass; `pnpm lint`/`format:check`/`typecheck` green;
  `pnpm gen:types` regenerated (`pitches/bulk` paths present in `shared-types`).
- **Commits:** `v0.10.0` (generate + batch model/repo/registry foundation), `v0.11.0` (bulk fan-out
  service), `v0.12.0` (bulk routes + schemas + wiring + regenerated types). §8 lockstep version bumps.

## 2026-07-19 — Day 3 Phase B: checkpoint review fixes

- **What:** Triaged `code-reviewer` + `database-reviewer` findings over the bulk slice; fixed the
  worthwhile ones, documented the rest as known-minor.
- **Correctness (v0.12.2):**
  - **[HIGH]** DB-fallback false-positive: `_db_fallback_snapshot` counted *any* historical ready
    pitch as this batch's success. Added a `created_since` filter to
    `get_latest_ready_for_customer`; the fallback now only credits pitches generated at/after the
    batch's `created_at`, else `pending`. (`api/pitches.py`, `repositories/pitch_repository.py`)
  - **[MED]** Item could stick at `running` forever if `session_factory()` raised (outside the
    try). Moved session creation inside the `try`; `finally` guards `db is not None`.
    (`services/bulk_pitch_service.py`)
  - **[MED]** `get_bulk_status` was sync (threadpool) reading the event-loop-mutated registry — a
    cross-thread data race. Made it `async def`. (`api/pitches.py`)
- **Perf/hardening (v0.12.3):**
  - **[MED]** `BatchRegistry` never evicted → unbounded memory. Added a bounded cap (default 256)
    that drops the oldest *completed* batches on `create` (in-flight never evicted; dropped batches
    fall back to the DB reconstruction). (`services/batch_registry.py`)
  - **[MED-db]** Dropped the redundant standalone `pitches.customer_id` index (already the leading
    column of two composite indexes) — one fewer btree write per insert on the append-only table.
    (`models/pitch.py`)
  - **[MED-db]** Set `expire_on_commit=False` and removed post-commit `refresh()` in both repos —
    saves a SELECT per row created on the hot write path. (`db/session.py`, both repositories)
- **Deferred (documented, docs §8):** read snapshot held across the LLM `await` (mitigated — bulk
  closes its per-item session after each generation, so the window is one generation, not the batch);
  N-query DB fallback loop (fine at N≤200); explicit SQLite pool sizing (fine at `bulk_concurrency=4`).
- **Verification:** 71 tests pass (+3: fallback-ignores-old-pitch, registry eviction ×2);
  lint/format/typecheck green. Reviewers' verdict was WARNING (1 HIGH) → HIGH now fixed.

## 2026-07-20 — Day 3 Phase C: swap in real Gemini (Vertex AI + ADC)

- **What:** Wired the real LLM provider behind `LLM_MODE=gemini`, keeping `mock` the default. Done in
  a `day3-phase-c` worktree; incremental semantic-versioned commits.
- **Auth decision (user):** Application Default Credentials on **Vertex AI**, not an API key —
  `genai.Client(vertexai=True, project, location)`. Fits the Cloud Run deploy (service-account
  identity) and removes API-key secret management. `gemini` mode requires `GOOGLE_CLOUD_PROJECT`.
- **Changes:**
  - `v0.12.5` chore: add `google-genai` (resolved 2.12.1).
  - `v0.12.6` fix: correct pinned Gemini token pricing to Vertex standard rates (pro output was
    under-counted; flash both wrong). Verified against the live pricing page. (`ai/pricing.py`)
  - `v0.13.0` feat: `GeminiLLM` adapter over the existing `LLMClient` seam (streams deltas → one
    `UsageInfo`; normalizes connect/mid-stream/stall errors to `ProviderError`; usage-estimate
    fallback). `get_llm_chain` builds a 2-hop pro→flash chain over one shared client; SDK imported
    only on the real path; client injected → 10 unit tests, no network. Config gains
    `GOOGLE_CLOUD_PROJECT/LOCATION` + `GEMINI_TIMEOUT_S`; dropped unused `GEMINI_API_KEY`.
    (`ai/llm_client.py`, `ai/llm_provider.py`, `core/config.py`, `.env.example`)
  - `v0.13.1` fix: **thinking-model token budget** (teeth-step finding). Gemini 2.5 are thinking
    models; thinking tokens count against `max_output_tokens`, so 512 truncated the pitch
    (`finish_reason=MAX_TOKENS`) before the offer → all hops failed verification → error. Raised to
    2048 + explicit `thinking_budget=512`. Added a regression guard. (`ai/llm_provider.py`)
  - `v0.13.2` docs: recorded the ADC amendment + thinking-model gotcha in `CLAUDE.md` §3, `spec.md`
    §4.9, `take-home-plan.md`; tracking updates.
- **Teeth step (live, real Vertex calls, project `easy-struct`):** read real pitches for two
  customers. Both grounded first-pass on `gemini-2.5-pro`, no fallback: exact plan name, RM price,
  term, tenure, usage; `grounding_ok=true`; cost logged (~$0.002/pitch). Cache-hit replay confirmed
  (`cache_hit=true`, identical text). The earlier truncation run also confirmed the fallback chain
  fires (pro→flash→error) mechanically.
- **Key decisions:** reuse the untouched reliability pipeline (verification, cache, single-flight,
  fallback, streaming, bulk, cost logging all consume the seam unchanged); low temperature (0.4) +
  bounded output keep pitches grounded and tight; per-chunk stall timeout so a hung hop fails over.
- **Verification:** 82 tests pass (+11 gemini); ruff + mypy clean; hooks green on every commit.
- **Env snag (noted, not committed):** on Windows `core.autocrlf=true` with no `.gitattributes`
  makes fresh worktree checkouts CRLF, which breaks the prettier pre-commit hook. Normalized the
  worktree's web files back to LF (git-invisible) to get commits through. A `.gitattributes`
  enforcing LF is the real fix — deferred as separate repo-hygiene work.

## 2026-07-20 — Day 4: Frontend (dashboard, table, streaming pitch, bulk)

- **What:** Built the agent UI over the finished endpoints, in a `day4-frontend` worktree; six
  incremental commits (v0.13.3 → v0.17.1). Scope held: streaming + state management built well,
  visuals minimal (Tailwind defaults, hand-rolled primitives, no library); auth stubbed.
- **v0.13.3** chore: added `.gitattributes` (enforce LF) — the durable fix for the recurring
  autocrlf↔prettier problem; it also revealed the assignment PDF working copy was being CRLF-corrupted
  and restored it.
- **Architecture:** browser → single catch-all Next route handler `app/api/[...path]/route.ts` →
  FastAPI (backend URL stays server-side, one origin). SSE bodies pass through unbuffered. Single-pitch
  SSE is a POST, so the client reads it via `fetch` + `ReadableStream` (`lib/sse` parser), not
  EventSource. State: QueryProvider → FiltersProvider → PitchProvider.
- **v0.14.0** BFF proxy + typed API client + `lib/sse` parser + `types/api` aliases & SSE unions.
- **v0.15.0** dashboard summary + customer table (FiltersProvider, useCustomers/useDashboard, Filters,
  pagination) + ui primitives (Button/Badge/Spinner/PitchStatusBadge).
- **v0.16.0** detail page (info + usage bars beside the pitch) + PitchProvider state machine
  (not_generated→generating→ready/failed; regenerating/fallback reset visible text) + PitchPanel
  (token-by-token render, copy, regenerate=force, meta footer).
- **v0.17.0** bulk progress (GAP #2): useBulkGeneration — SSE `/stream` invalidates a TanStack poll of
  the status endpoint (single source of truth: counts + per-item items[]), refetchInterval fallback;
  BulkProgress X-of-N bar + per-item list; runs on the current page (cap 200).
- **v0.17.1** Vitest + RTL setup + 12 tests (sse parser incl. split-chunk/CRLF, pitch reducer
  transitions, PitchStatusBadge, BulkProgress).
- **Teeth step:** ran FastAPI (mock, SSE_TOKEN_CHUNK_DELAY_MS=40) + `next dev`; verified through the
  live BFF: list/dashboard JSON proxy, pages render 200, single-pitch SSE streams token-by-token, bulk
  start/stream/poll with per-item results, no dev-log errors. Playwright browser MCP wasn't connected
  this session, so the visual watch was done at the HTTP-streaming level, not a rendered browser.
- **Verification:** web typecheck + eslint + prettier clean; 12 Vitest tests pass; hooks green on every
  commit. Playwright streaming E2E deferred to Day 5 per the day plan.

## 2026-07-20 — Day 5: tests, Docker, live Cloud Run deploy, README

- **What:** Closed the take-home in a `day5-deploy` worktree; 6 commits (v0.17.4 → v0.18.2). Most
  Day-5 tests already existed (82 pytest + 12 vitest); the new work was the E2E, Cloud Run readiness,
  the live deploy, and the README.
- **v0.17.4** Playwright streaming + bulk E2E (next dev + mock uvicorn, headless) — asserts
  generating→ready + grounded text + copy/regenerate, and bulk to N-of-N. Also fixed the **orphaned
  `SSE_TOKEN_CHUNK_DELAY_MS`** (defined but never wired → mock never paced its stream); now
  `MockLLM(delay_s=...)`.
- **v0.17.5** Cloud Run readiness: switched web to **Next standalone** output (the prior `pnpm start`
  runner corepack-pulled pnpm 11 / Node 22 and crashed on Node 20); `$PORT` in both Dockerfiles;
  `apps/web/public/.gitkeep` (build COPY needed it); web/root `.dockerignore` + `.gcloudignore`.
  Verified via `docker compose up --build`.
- **v0.18.0** `deploy/deploy.sh` — reproducible two-service deploy.
- **v0.18.1** root README (injection acknowledgement + AI disclosure opener, architecture, every
  reliability decision, model pinning, run/deploy, auth assumption, curated out-of-scope).
- **Live deploy (user override of the mock-default plan):** real Gemini via Vertex ADC (runtime SA
  granted `roles/aiplatform.user`), `--min-instances=0 --max-instances=1`, default CPU-throttling.
  Live at https://retention-web-6xowpmfgjq-as.a.run.app. Smoke test: web 200, health `gemini`, a real
  pitch streamed grounded (it even exercised verify→regenerate live on an out-of-catalog first draft),
  `grounding_ok=true`, ~$0.002/pitch.
- **v0.18.2** code-review fixes + live URL + tracking. code-reviewer findings: [HIGH] BFF fetch didn't
  propagate `req.signal` (aborted streams kept generating/billing) → added `signal: req.signal`;
  [MED] bulk button re-clickable mid-batch → disabled while `!status.complete`; [LOW] added `..`
  path-segment guard in the proxy. [CRITICAL] flagged: the public `api` service runs real Gemini
  unauthenticated (anyone with the URL can bill Gemini / hit bulk) — a documented, user-accepted
  tradeoff (max=1 bounds blast radius); raised to the user with an offer to lock api to
  service-to-service auth. Deferred [LOW] Dockerfile `|| install` fallback (lockfile in sync).
- **GIF:** cannot screen-record here; README has a ready-to-uncomment embed for `docs/streaming-demo.gif`.
- **Verification:** api 82 pytest, web 12 vitest, 2 Playwright E2E, compose build+run, live smoke —
  all pass; typecheck/lint/prettier/ruff/mypy clean; hooks green on every commit.

## 2026-07-20 — Post-Day-5 enhancements (user feature requests)

Each built in its own worktree, incrementally committed, verified, merged, and tagged. All kept the
82→90 pytest / 12→14 vitest / 2 E2E suites green.

- **v0.19.0–0.19.1 — customer-table row select + page size.** Whole row is click-to-select then
  click-to-open ("highlight then open"); name link still opens directly (keeps the E2E). Default list
  page size 20 → 10. (`CustomerTable.tsx`, `FiltersProvider.tsx`; +1 vitest.)
- **v0.20.0–0.20.3 — "Fibre Signal" redesign.** New identity (cool instrument palette + Space Grotesk /
  IBM Plex Sans/Mono fonts, fixed the stray Arial body font), top bar, restyled dashboard/table/filters
  + pitch console with the animated fibre streaming rule, usage signal-trace waveform, and a styled
  offer-ladder on the detail page. Light-first, auto dark. Presentation-only (labels/selectors
  preserved). v0.20.3 also fixed the api Docker image to run the prebuilt venv's uvicorn directly
  (`uv run` was re-syncing at startup and failing Cloud Run's health check). Verified via Playwright
  screenshots (light/dark/mobile/streaming).
- **v0.21.0–0.21.1 — clickable dashboard tiles.** `GET /customers` gains an `expiring` filter (current
  calendar month, reuses `current_month_bounds` so counts match the tiles); tiles are buttons that
  filter the list to plan + expiring-this-month, with an active highlight, an "Expiring this month ✕"
  chip, and re-click to clear. (v0.21.2 was a requirements-traceability doc added by the user.)
- **v0.22.0–0.22.3 — observability.** Request **trace id** (ContextVar + logging filter → every JSON
  line; pure-ASGI middleware; `X-Trace-Id` header; per-item `batch{id}-{customer}` for bulk) +
  in-process **Prometheus metrics** at `GET /api/metrics` (generations/cache/regen/fallbacks/tokens/
  cost/http), no new deps. Trace id surfaced in the SSE `done` payload + pitch footer + BFF passthrough.
  README documents both. +7 pytest (tracing + metrics). Backend teeth confirmed one trace id ties a
  request's access + generation logs and the metrics counters increment.
- **Not yet redeployed:** the live URL still serves v0.20.3; these later changes await the next deploy.

## 2026-07-20 — Test hardening + tenure/usage filters (v0.22.5–v0.23.0)

- **What:** A review-driven test-and-feature pass (built in a worktree, rebuilt onto `main` as a
  monotonic v0.22.5→v0.23.0 sequence after the observability branch landed concurrently).
  - `v0.22.5` test: cover the **stale last-cached fallback** path (pro→flash→cached serves a prior
    ready pitch flagged `stale`) — previously the one uncovered fallback branch.
  - `v0.22.6` fix: broaden output-verification `_PLAN_RE` to catch fabricated brands + misspellings.
  - `v0.22.7` test: cover the **BFF proxy** route handler (forwarding, SSE headers, POST body,
    path-traversal 404, abort propagation).
  - `v0.22.8` chore: coverage tooling (`pytest-cov`, `@vitest/coverage-v8`) + `.github/workflows/ci.yml`
    (backend / frontend / e2e jobs).
  - `v0.23.0` feat: **tenure + usage list filters** — backend `tenure_min/max` + `usage_min/max` range
    params on the repo + `GET /customers`; frontend bucket dropdowns mapping to those params. This
    closes the assignment's "filter by plan, tenure, or usage" (previously tenure/usage were sort-only).
- **Why:** Close the test-strategy gaps found in an earlier review and fully satisfy the filter
  requirement. Files: `verification.py`, `customer_repository.py`, `api/customers.py`,
  `providers/FiltersProvider.tsx`, `components/customers/Filters.tsx`, `lib/api.ts` + tests.
- **Verification:** backend pytest 97, frontend vitest 23, typecheck/lint clean; filters verified
  end-to-end on seeded data (60 → 30 usage≥500 / 25 tenure≥37 / 13 both); Playwright E2E 2 passed.

## 2026-07-20 — Three-agent review pass + fixes (v0.23.1–v0.23.5)

- **What:** Ran security-reviewer, code-reviewer, and code-simplifier over the v0.22.5–v0.23.0 diff,
  surfaced findings for the user, then fixed the approved set incrementally.
- **Findings (headline):** two reviewers independently flagged the `_PLAN_RE` regex from **opposite
  directions** — code-reviewer [HIGH] false positives (it flagged legitimate capitalized prose like
  "TIME Fibre plans" / "Our Fibre network", failing fully-grounded pitches); security-reviewer [MED]
  false negatives (digit/lowercase-prefixed fabrications slipped through). Also: [MED] no frontend
  tests for bucket→range mapping; [LOW] no upper bound on filter params (OverflowError→500 risk);
  [LOW] CI missing `permissions:` + mutable action tags + no coverage gate. Simplifier: ship-ready.
- **Fixes:**
  - `v0.23.1` fix: re-anchor `_PLAN_RE` to numeric plan ids (`Fib(?:re|er) \d\S*`) — prose passes,
    numeric fabrications/misspellings caught; +capitalized-prose regression test +catalog-guard test.
  - `v0.23.2` test: `FiltersProvider` bucket→range mapping + page-reset tests.
  - `v0.23.3` fix: `le=` bounds on tenure/usage params (422 instead of driver OverflowError).
  - `v0.23.4` ci: `permissions: contents: read` + `--cov-fail-under=85`.
  - `v0.23.5` docs: traceability caveat corrected, spec §3/§4.4 updated, plan §8 limitations, README.
- **Deferred (accepted, logged in plan §8):** verification doesn't catch a *non-numeric*-suffix
  fabricated brand ("MaxSpeed Fibre Ultra") — tightening re-introduces false positives; `min>max`
  filter ranges aren't rejected (UI can't produce them); CI SHA-pinning (GitHub API unreachable here
  to resolve tags) + auto-deploy.
- **Verification:** backend pytest 100 pass (coverage 92%, gate 85%); frontend vitest green;
  regex teeth-check confirmed prose passes and `TIME Fibre 9000`/`TIME Fiber 300`/`MaxSpeed Fibre 900`
  are caught.
- **Commits:** `v0.23.1`–`v0.23.6` (this tracking entry). Built in the `review-fixes` worktree, merged
  to `main`.

## 2026-07-20 — Redeploy v0.23.6 to Cloud Run

- **What:** Ran `deploy/deploy.sh` (PROJECT=easy-struct, asia-southeast1, tag 84cdb7c) — built+pushed
  both images, deployed `retention-api` (private, real Gemini) + `retention-web` (public). Live at
  https://retention-web-6xowpmfgjq-as.a.run.app. Prior live was v0.20.3.

## 2026-07-20 — Harden the public URL: Basic-Auth gate + per-IP rate limit + $20/day spend cap

- **What:** Before sharing the public URL with a few devs, added three protections (user chose the
  simplest gate after rejecting a bespoke login-page design):
  - `v0.24.0` feat — backend **daily LLM spend cap**: in-process `DailyBudget` (`app/core/budget.py`,
    thread-safe, midnight rollover) checked before a fresh generation; over budget → clean SSE error,
    no LLM call, no row, while **cache hits + last-cached fallbacks stay free**. Cost recorded via
    `_log`; `/api/health` reports `daily_budget_usd`/`daily_spent_usd`/`budget_ok`. Config
    `LLM_DAILY_BUDGET_USD` (0 = off; 20 in prod). +4 budget unit tests, +2 pitch-service tests.
  - `v0.25.0` feat — web **HTTP Basic Auth gate + per-IP rate limit** in one new
    `apps/web/src/middleware.ts`, active only when `APP_PASSWORD` is set (local dev / CI / e2e stay
    open). Basic Auth over all routes incl. the `/api/*` BFF proxy (401 + `WWW-Authenticate`);
    per-IP fixed-window limit on `/api/*` (`RATE_LIMIT_PER_MIN`, default 60) → 429 + `Retry-After`.
    +6 middleware tests.
  - `v0.25.1` chore — `deploy.sh` requires `APP_PASSWORD` (never committed) + passes
    `RATE_LIMIT_PER_MIN` / `LLM_DAILY_BUDGET_USD`.
  - `v0.25.2` docs — README / spec §4.8 / plan §8 / traceability updated.
- **Why:** The public `web` URL runs real billable Gemini with no gate/rate-limit/cap; the "semaphore"
  is only a within-batch bulk cap, not request/cost control (CLAUDE.md §4 "rate limiting").
- **Key decision:** Basic Auth (one shared password, browser-native prompt) over a custom login
  page/cookie — auth is out of scope, so a shared gate is enough and far simpler. Cost cap + rate limit
  are in-process (coherent at `max-instances=1`); a wider fleet needs Redis (noted in plan §8).
- **Verification:** backend pytest 106; web vitest 34; typecheck/lint clean. Critical teeth step —
  **built the standalone web image and ran it with `APP_PASSWORD` set**: `/` → 401 +
  `WWW-Authenticate`, correct creds → 200, wrong → 401 (confirms middleware reads the *runtime* env in
  the production build, not a build-time inline). Redeploy with the new env pending the user's password.
