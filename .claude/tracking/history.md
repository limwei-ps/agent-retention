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
