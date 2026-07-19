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
