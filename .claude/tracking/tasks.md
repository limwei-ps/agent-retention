# Tasks — Time Internet Retention Tool

Master task list. Mark done with `[x]` and a date; add new tasks in place. Synced with
`docs/take-home-plan.md` §6 (day-by-day) and `docs/spec.md`. Gaps are folded into the Days as
`[GAP #n]`.

---

## Day 1 — Foundations & Spec

- [x] Convert plan PDF → `docs/take-home-plan.md` (gaps + conventions) — 2026-07-19
- [x] Set up `CLAUDE.md` backbone + `.claude/tracking/` foundation — 2026-07-19
- [x] Expand §9 conventions with frontend/backend folder structure — 2026-07-19
- [x] Write spec/PRD → `docs/spec.md` (data model, offer ladder, API, AI layer, frontend) — 2026-07-19
- [x] AI-layer feasibility (streaming shape, mock strategy, cache-key soundness) — reasoned in spec §4 — 2026-07-19
- [x] `git init` + `.gitignore` (`.env` excluded) — 2026-07-19
- [x] Commit: docs, CLAUDE.md, spec, tracking — 2026-07-19

## Day 2 — Monorepo scaffold + Data & Backend Core

- [ ] Monorepo scaffold: root `package.json` (private) + `pnpm-workspace.yaml` (`apps/web`, `packages/*`)
- [ ] `apps/web` (Next.js) + `apps/api` (FastAPI/uv) + `packages/shared-types` skeletons
- [ ] `apps/api/scripts/export_openapi.py` + root `gen:types` script (openapi-typescript → shared-types)
- [ ] Set `version: 0.1.0` in `apps/web/package.json` + `apps/api/pyproject.toml` (SemVer source of truth — CLAUDE.md §8)
- [ ] Plan catalog config module — MYR fibre 100/300/500/1000 @ 99/129/159/199 (single source for seed/offer/grounding)
- [ ] Seed 50–100 customers (Faker): plan, tenure, `usage_history` (12mo), `contract_end_date` clustered this month `[GAP #1]`; usage archetypes (flat-low / climbing / heavy)
- [ ] Derived usage scalars: `avg_monthly_gb` + `last_month_gb` `[GAP #4]`
- [ ] Offer ladder derivation (retain / value_upgrade / upsell + `recommended`)
- [ ] DB layer (SQLite + SQLAlchemy); repositories/DAO behind `Depends()`
- [ ] `GET /customers`: search name/id `[GAP #5]` / filter plan / sort tenure|usage|expiry / pagination
- [ ] `GET /customers/{id}`: detail + usage_history + offer ladder + latest pitch
- [ ] `GET /dashboard/summary`: expiring **this month** by plan tier (month + timezone defined `[GAP #5]`)
- [ ] `GET /health` (reports `llm_mode`)
- [ ] Commit incrementally — one per endpoint / logical unit

## Day 3 — AI Layer (highest weight)

- [ ] LLM abstraction with `LLM_MODE=mock|gemini`; deterministic **mock first**
- [ ] Grounding prompt (customer + offer ladder + `recommended`); **sanitize** customer text (2nd-order injection)
- [ ] Pitch-as-a-product prompt + `PROMPT_TEMPLATE_VERSION`
- [ ] Output grounding verification (quoted plan/price ∈ ladder; auto-regenerate once, else clean error)
- [ ] Cache: key = `hash(grounding snapshot + template version + model id)`; prove invalidation
- [ ] Regenerate = force cache bypass `[GAP #3]`
- [ ] Single-flight / request coalescing per `cache_key`
- [ ] Fallback (gemini → flash → cached → clean error) — prove it fires
- [ ] SSE streaming endpoint; cache-hit = replay stored text as stream
- [ ] Bulk generation: semaphore cap + per-item success/failure tracking
- [ ] Token/cost logging (structured JSON per call)
- [ ] Swap in real Gemini behind the flag; read outputs to confirm no hallucination
- [ ] Commit each capability separately

## Day 4 — Frontend

- [ ] Customer table: search/filter/sort/pagination
- [ ] Dashboard summary by plan tier
- [ ] Detail view: customer info + usage + pitch **side by side**
- [ ] Streaming render (token-by-token) + status states (not generated/generating/ready/failed)
- [ ] Copy + regenerate (force) controls
- [ ] Bulk progress UI (X of N, live) + per-item state `[GAP #2]`
- [ ] Providers (`PitchProvider`, `FiltersProvider`, `QueryProvider`) + TanStack Query; `usePitchStream`
- [ ] Commit per component/feature

## Day 5 — Tests, Docker, Deploy, README

- [ ] Tests: AI layer mocked (cache hit, fallback, partial batch failure, single-flight) + key UI + streaming E2E
- [ ] Dockerfile(s) + docker-compose
- [ ] **Actually deploy** to GCP Cloud Run (mock-LLM default); secrets via Secret Manager; test deploy path early
- [ ] Model choice + version pinning (config constant + README line)
- [ ] Finalize README: architecture, tradeoffs, run/deploy notes, injection acknowledgement, auth assumption, curated out-of-scope items
- [ ] Screen recording / GIF of the streaming pitch
- [ ] Final self code-review pass
- [ ] Commit: tests, docker, deploy config, README

## Gap traceability (folded into Days above)

- `[GAP #1]` `contract_end_date` in model + seed → Day 2
- `[GAP #2]` bulk progress UI + channel → Day 4
- `[GAP #3]` regenerate forces cache bypass → Day 3
- `[GAP #4]` usage sort/filter scalar → Day 2
- `[GAP #5]` search scope + "this month" boundary/timezone → Day 2
- `[x] [GAP #6]` coding conventions pinned (CLAUDE.md + plan §9) — 2026-07-19
