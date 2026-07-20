# Tasks — Time Internet Retention Tool

Master task list. Mark done with `[x]` and a date; add new tasks in place. Synced with
`docs/take-home-plan.md` §6 (day-by-day) and `docs/spec.md`. Gaps are folded into the Days as
`[GAP #n]`.

---

## Day 1 — Foundations & Spec

- [x] Install official plugins (frontend-design, feature-dev, code-review, commit-commands, security-guidance, playwright, github + superpowers, context7, code-simplifier, claude-md-management); documented in CLAUDE.md §10 — 2026-07-19
- [x] Convert plan PDF → `docs/take-home-plan.md` (gaps + conventions) — 2026-07-19
- [x] Set up `CLAUDE.md` backbone + `.claude/tracking/` foundation — 2026-07-19
- [x] Expand §9 conventions with frontend/backend folder structure — 2026-07-19
- [x] Write spec/PRD → `docs/spec.md` (data model, offer ladder, API, AI layer, frontend) — 2026-07-19
- [x] AI-layer feasibility (streaming shape, mock strategy, cache-key soundness) — reasoned in spec §4 — 2026-07-19
- [x] `git init` + `.gitignore` (`.env` excluded) — 2026-07-19
- [x] Commit: docs, CLAUDE.md, spec, tracking — 2026-07-19

## Day 2 — Monorepo scaffold + Data & Backend Core

- [x] Monorepo scaffold: root `package.json` (private) + `pnpm-workspace.yaml` (`apps/web`, `packages/*`) — 2026-07-19
- [x] `apps/web` (Next.js) + `apps/api` (FastAPI/uv, `/api/health`) + `packages/shared-types` skeletons — 2026-07-19
- [x] `apps/api/scripts/export_openapi.py` + root `gen:types` script (openapi-typescript → shared-types) — 2026-07-19
- [x] Version files set to repo version (0.2.2) in `apps/web/package.json` + `apps/api/pyproject.toml` + shared-types (CLAUDE.md §8) — 2026-07-19
- [x] Plan catalog config module — MYR fibre 100/300/500/1000 @ 99/129/159/199 — 2026-07-19
- [x] Seed 60 customers (Faker): plan, tenure, `usage_history` (12mo), `contract_end_date` clustered this month `[GAP #1]`; usage archetypes (flat_low / climbing / heavy) — 2026-07-19
- [x] Derived usage scalars: `avg_monthly_gb` + `last_month_gb` `[GAP #4]` — 2026-07-19
- [x] Offer ladder derivation (retain / value_upgrade / upsell + `recommended`) — 2026-07-19
- [x] DB layer (SQLite + SQLAlchemy); repository behind a Protocol via `Depends()` — 2026-07-19
- [x] `GET /customers`: search name/id `[GAP #5]` / filter plan / sort tenure|avg_gb|expiry / pagination — 2026-07-19
- [x] `GET /customers/{id}`: detail + usage_history + offer ladder + latest pitch — 2026-07-19
- [x] `GET /dashboard/summary`: expiring **this month** by plan tier (KL timezone `[GAP #5]`) — 2026-07-19
- [x] `GET /health` (reports `llm_mode`) — 2026-07-19
- [x] Review pass (code-review + database-reviewer agents): fixed N+1 + pagination stability — 2026-07-19
- [ ] Commit incrementally — one per endpoint / logical unit

## Day 3 — AI Layer (highest weight)

### Phase A — single-pitch vertical slice (done, reviewed)
- [x] LLM abstraction with `LLM_MODE=mock|gemini`; deterministic **mock first** — 2026-07-19
- [x] Grounding prompt (customer + offer ladder + `recommended`); **sanitize** customer text (2nd-order injection) — 2026-07-19
- [x] Pitch-as-a-product prompt + `PROMPT_TEMPLATE_VERSION` — 2026-07-19
- [x] Output grounding verification (quoted plan/price ∈ ladder; auto-regenerate once, else clean error) — 2026-07-19
- [x] Cache: key = `hash(grounding snapshot + template version + model id)` incl. exact tenure/usage; invalidation proven — 2026-07-19
- [x] Regenerate = force cache bypass `[GAP #3]` — 2026-07-19
- [x] Single-flight / request coalescing per `cache_key` — 2026-07-19
- [x] Fallback (hop → next hop → last-cached → clean error) — proven — 2026-07-19
- [x] SSE streaming endpoint; cache-hit = replay stored text as stream — 2026-07-19
- [x] Token/cost logging (structured JSON per call) — 2026-07-19
- [x] Review pass (code-review + database-reviewer): fixed single-flight-failure crash, stale-cache key, indexes/WAL/tiebreaker — 2026-07-19

### Phase B — bulk generation (done)
- [x] `PitchService.generate` — non-streaming outcome adapter over `stream_pitch` (reuses cache/single-flight/fallback/verify/cost) — 2026-07-19
- [x] `PitchBatch` model + `batch_repository` (persists customer_ids/total for DB-snapshot fallback; no `Pitch.batch_id` — cache hits make it unreliable) — 2026-07-19
- [x] In-memory `BatchRegistry` (live X-of-N; `asyncio.Condition` + version counter for reconnect-safe SSE) — 2026-07-19
- [x] `bulk_pitch_service.run_batch` — `asyncio.Semaphore(bulk_concurrency)` fan-out; per-item failure isolation; own session per worker — 2026-07-19
- [x] Bulk routes: `POST /pitches/bulk` (BackgroundTasks) + `GET /pitches/bulk/{id}` poll + `GET /pitches/bulk/{id}/stream` SSE w/ DB fallback — 2026-07-19
- [x] Tests: all-succeed, partial-failure isolation, semaphore cap, DB fallback, dedup, validation (21 new) — 2026-07-19
- [x] Teeth step: live POST/stream/poll; 3 succeed + 1 bogus fails in isolation; pitch grounded — 2026-07-19

### Phase C — done (2026-07-20)
- [x] Swap in real Gemini behind the flag; read outputs to confirm no hallucination — 2026-07-20:
      `GeminiLLM` over Vertex AI + ADC (no API key); live teeth step confirmed grounded pitches
      (exact plan/price/term/tenure), cache-hit replay, cost logging. Also fixed Gemini token pricing.
- [x] Commit each capability separately — 2026-07-20: v0.12.5 dep, v0.12.6 pricing, v0.13.0
      adapter+chain, v0.13.1 thinking-model token fix, v0.13.2 docs/spec amendment.

## Day 4 — Frontend  (done 2026-07-20)

- [x] Customer table: search/filter/sort/pagination — 2026-07-20 (v0.15.0)
- [x] Dashboard summary by plan tier — 2026-07-20 (v0.15.0)
- [x] Detail view: customer info + usage + pitch **side by side** — 2026-07-20 (v0.16.0)
- [x] Streaming render (token-by-token) + status states (not generated/generating/ready/failed) — 2026-07-20 (v0.16.0)
- [x] Copy + regenerate (force) controls — 2026-07-20 (v0.16.0)
- [x] Bulk progress UI (X of N, live) + per-item state `[GAP #2]` — 2026-07-20 (v0.17.0)
- [x] Providers (`PitchProvider`, `FiltersProvider`, `QueryProvider`) + TanStack Query; `usePitchStream` — 2026-07-20
- [x] Commit per component/feature — 2026-07-20: v0.13.3 gitattributes, v0.14.0 BFF/client/sse,
      v0.15.0 dashboard+table, v0.16.0 detail+pitch, v0.17.0 bulk, v0.17.1 tests
- Notes: BFF is a single catch-all proxy (`app/api/[...path]`); single-pitch SSE is POST → read via
  fetch+ReadableStream, not EventSource; teeth step verified streaming/bulk through the live BFF
  (Playwright browser MCP unavailable → HTTP-level verification). Playwright E2E deferred to Day 5.

## Day 5 — Tests, Docker, Deploy, README  (done 2026-07-20)

- [x] Tests: AI layer mocked (cache hit, fallback, partial batch failure, single-flight) + key UI + streaming E2E — 2026-07-20: AI/UI tests already existed (82 pytest + 12 vitest); added Playwright streaming + bulk E2E (v0.17.4). Also fixed the orphaned SSE_TOKEN_CHUNK_DELAY_MS.
- [x] Dockerfile(s) + docker-compose — 2026-07-20 (v0.17.5): Next standalone + $PORT + ignore files; verified via `docker compose up --build`.
- [x] **Actually deploy** to GCP Cloud Run — 2026-07-20: live at https://retention-web-6xowpmfgjq-as.a.run.app. Deviates from the "mock default / Secret Manager" plan per user: **real Gemini** via Vertex ADC (runtime SA), min=0/max=1, no API key. Deploy scripted in deploy/deploy.sh (v0.18.0).
- [x] Model choice + version pinning (config constant + README line) — 2026-07-20 (README §Model choice; config + ai/pricing.py).
- [x] Finalize README: architecture, tradeoffs, run/deploy, injection acknowledgement, auth assumption, curated out-of-scope — 2026-07-20 (v0.18.1).
- [ ] Screen recording / GIF of the streaming pitch — deferred: cannot screen-record from here; README has a ready-to-uncomment embed for `docs/streaming-demo.gif` (manual step).
- [x] Final self code-review pass — 2026-07-20 (code-reviewer agent over the Day 4–5 diff).
- [x] Commit: tests, docker, deploy config, README — 2026-07-20: v0.17.4 → v0.18.x, incremental.

## Gap traceability (folded into Days above)

- `[x] [GAP #1]` `contract_end_date` in model + seed → Day 2 — 2026-07-19
- `[x] [GAP #2]` bulk progress UI + channel → Day 4 — 2026-07-20 (v0.17.0; SSE-driven poll, X-of-N + per-item)
- `[x] [GAP #3]` regenerate forces cache bypass → Day 3 — 2026-07-19
- `[x] [GAP #4]` usage sort/filter scalar → Day 2 — 2026-07-19
- `[x] [GAP #5]` search scope + "this month" boundary/timezone → Day 2 — 2026-07-19
- `[x] [GAP #6]` coding conventions pinned (CLAUDE.md + plan §9) — 2026-07-19

All six gaps identified vs. the assignment brief are now closed.

## Post-Day-5 enhancements (user requests, 2026-07-20)

- [x] Customer-table row select ("highlight then open") + page size 10 — v0.19.0–0.19.1
- [x] "Fibre Signal" UI redesign (fonts, tokens, top bar, pitch console + streaming rule, usage
      waveform, offer ladder); light-first + auto dark — v0.20.0–0.20.2
- [x] Fix api Docker startup (run prebuilt venv uvicorn; Cloud Run health check) — v0.20.3
- [x] Clickable dashboard tiles → filter list by plan + expiring-this-month (new `expiring` API
      filter, active highlight, clear chip) — v0.21.0–0.21.1
- [x] Observability: request trace id (X-Trace-Id, per-item bulk ids, on every log line + pitch
      footer) + Prometheus metrics at `GET /api/metrics` — v0.22.0–0.22.3
- [x] Requirements-traceability doc (assignment → files checklist) — v0.21.2
- [x] Test hardening + tenure/usage filters — v0.22.5–0.23.0: stale-cache fallback test, verification
      regex broaden, BFF proxy test, coverage tooling + GitHub Actions CI, and tenure/usage **range
      filters** (closes "filter by plan, tenure, or usage" — previously sort-only)
- [x] Three-agent review pass (security / code / simplifier) + approved fixes — v0.23.1–0.23.5:
  - [x] A+B verification regex false-positive on grounded prose (re-anchored to numeric plan ids) + tests
  - [x] C FiltersProvider bucket→range + page-reset tests
  - [x] D `le=` bounds on tenure/usage params (422 not 500)
  - [x] E+F CI `permissions: contents: read` + `--cov-fail-under=85`
  - [x] Docs + tracking updated (spec §3/§4.4, traceability, plan §8, README)
  - Deferred (accepted, plan §8): non-numeric fabricated-brand verification gap; `min>max` not rejected;
    CI SHA-pin + auto-deploy
- [x] Redeploy latest to Cloud Run — 2026-07-20 (v0.23.6 live at retention-web-6xowpmfgjq-as.a.run.app)
- [x] Harden the public URL before sharing — v0.24.0–0.25.3:
  - [x] Backend $20/day LLM spend cap (`DailyBudget`; over-budget → clean error, cache stays free) — v0.24.0
  - [x] Web HTTP Basic Auth gate + per-IP rate limit (`middleware.ts`; 401 / 429) — v0.25.0
  - [x] Deploy env (`APP_PASSWORD`, `RATE_LIMIT_PER_MIN`, `LLM_DAILY_BUDGET_USD`) — v0.25.1
  - [x] Docs + tracking — v0.25.2–0.25.3
  - [ ] Redeploy with the gate/cap env (needs the shared `APP_PASSWORD` from the user)
