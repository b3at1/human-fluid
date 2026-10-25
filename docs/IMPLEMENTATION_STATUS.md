# Implementation status

Implemented locally from `HUMAN_FLUID_BUILD_SPEC.md`. No external publication, paid provisioning, real model call, Git commit, push, or PR was performed.

## Requirement checklist

- [x] Python 3.12 / FastAPI / Pydantic / SQLAlchemy / Alembic / SQLite; locked uv dependencies. Vue 3 / TypeScript / Vite / Router / Pinia; npm lockfile.
- [x] One-command development launcher; same-origin SPA/API production path; true API 404s; migrations, persistent WAL database, foreign keys and busy timeout.
- [x] Guest-first immediate practice; opaque random HttpOnly cookie with hashed server token; separate owner authentication and CSRF.
- [x] Five playable structured families, four designed levels: actual Reasoning Gym dependencies/logic, native ordering/induction/active hypothesis testing.
- [x] Imported bank generated and independently re-verified: **520 accepted items**, 50 practice + 15 check per family/level. Pinned source/version/config/seed/raw metadata retained privately. Structural duplicate/split checks and bounded generation.
- [x] Independent cycle/order witnesses, unique logical truth assignments, exhaustive small-order comparisons, induction target agreement, real hidden-rule query outputs and replay.
- [x] Worked first-exposure examples outside evaluation, generic instructions, progressive server-recorded hints, deterministic instance-specific explanations, truth tables, opposite order witnesses, item reporting and optional reflections.
- [x] Eight-item mixed and six-item focused sessions; pause, resume, abandon; saved draft/scratchpad/confidence; immutable first submissions and idempotent queries/hints/next issuance.
- [x] Transparent versioned rule policy with broad coverage, fresh due review, 1/3/7-day heuristic intervals, independent-sample advancement, manual level controls, action/rationale logs and null propensity.
- [x] Fixed balanced ten-item checks; frozen versioned A/B manifests with disjoint structures/configurations, fixed level 2, release/exposure/repeated-form logs. No individual correctness/solution leak before explicit release.
- [x] Exploratory six-item presentation probe uses a scheduling **table** withheld from abstract-order practice/onboarding; no far-transfer or Gf-gain claim. Related grammar reuse disclosed.
- [x] Journal with historical problem/explanation; family/mistake/assistance filters; transparent progress denominators by family/level, weekly hint-use data, delayed retrieval, confidence Brier count and separate check/probe results.
- [x] Versioned owned export includes only permitted review material, notes, scratchpad, queries and discussion. Strict bounded restore preserves unverified history without roles/grants/identity; imported outcomes never affect canonical scores or adaptation. Confirmed deletion is owner-scoped.
- [x] Optional per-attempt discussion: disabled default, server-local/cloud-compatible adapter, explicit context disclosure/scratchpad opt-in, safe text output, thread clearing, no inference on page load.
- [x] Interactive Argon2id admin bootstrap; one-hour separately scoped owner sessions; persistent login throttles; expiring hashed single-use invites; atomic redemption/token rotation; grants/revocation/global inference switch.
- [x] Persistent transactional request/token reservations, concurrency limits, principal/key/body idempotency, durable unknown outcomes, redacted errors, server-only keys/endpoints. Production rejects insecure origin/cookie settings and invalid cap configurations.
- [x] White/yellow monospaced responsive interface, self-hosted licensed font, semantic keyboard controls/focus, diagram text equivalents, mobile collapsible thinking tools, reduced-motion CSS and no page-level mobile overflow in tested flows.
- [x] Dockerfile/Compose with durable volume, non-root user, single worker, health checks; backup/restore utility, CI configuration, architecture/security/evaluation/provenance docs and a three-minute demo.

## Actual verification

- Backend: `MPLCONFIGDIR=/tmp/human-fluid-mpl .venv/bin/pytest -q` from `backend` — **56 passed**. Includes Hypothesis-generated instances (100 examples), actual source adapters across levels, all bank solution witnesses, lifecycle/ownership/CSRF/body limits, assessment embargo across routes, structural A/B exclusion, adaptation, review, restore/deletion, grants, concurrent single-use redemption, concurrent inference reservations, durable timeout states, idempotency, context consent/canary and synthetic provider-transport cap tests.
- Frontend: `npm --prefix frontend test` — **5 passed**. Structured boolean controls, ordering choices, prerequisite graph direction/isolated nodes and malformed/list input parsing.
- `npm --prefix frontend run build` — TypeScript check and production Vite build passed. Generated OpenAPI snapshot is checked against the application; explicit frontend/public-renderer contracts are tested.
- Browser: `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=... npm run test:e2e` — **10 passed**, five flows each at 1440×1000 desktop and 360×800 mobile. Full mixed session, hints, pause/reload/resume, journal, granted synthetic discussion, ten-item sealed check, active experiments, export/restore/deletion, and six-item scheduling-table probe. No page-level horizontal overflow in these flows. The full-session flow records no page JS errors.
- Screenshots actually opened and inspected: desktop homepage, mobile dependency exercise, desktop worked cycle explanation, and desktop discussion. Screenshot artifacts remain in ignored `frontend/test-results/`; they use temporary synthetic profiles, never real experiment histories. Updated captures are taken at page top to avoid full-page/sticky-position artifacts.
- Documented `make dev` launcher smoke passed: backend readiness and Vite homepage both returned HTTP 200; both services were then stopped.
- Migration/setup smoke: Alembic revisions `0001` → `0002`, initial bank generation, idempotent bank regeneration and re-verification of all **520** entries passed.
- Database backup and restore into a separate temporary database passed: 520 bank rows, `integrity_check=ok`, zero `foreign_key_check` violations.
- Dependency reproducibility: offline frozen uv sync and npm clean-install dry run passed. Dependency audit after updating vulnerable test packages reported **zero vulnerabilities**.
- Container configuration: `docker compose config --quiet` and shell entrypoint syntax passed. Container image execution has **not** been tested: Docker's daemon socket is absent in this environment.
- API/Chromium tests required approved outside-sandbox execution because this environment's sandbox stalls the local TestClient event loop/restricts browser sockets. The app tests then passed. Ordinary user startup does not depend on a coding-agent plugin.

## Limits and activation

- No live cloud or local model service was configured/called. Provider behavior is verified with an explicitly labeled stub and mocked HTTP transport only. Core app needs neither a key nor internet after installation.
- Cloud activation requires operator verification of the chosen provider/model's byte-level tokenizer bounds and `max_tokens` enforcement, backend secrets, and `AI_CAP_VERIFIED=true`. Unknown semantics must stay disabled. Token/request reservations are not a dollar cap. Local mode requires an installed model served on the backend host; it does not run on visitors' laptops.
- No Docker daemon, public host, TLS reverse proxy, independent security audit, real research study, multi-browser matrix, physical-device or screen-reader session was available. CI is provided but has not run on a remote host.
- The two check forms are matched by designed configuration, not psychometrically equated. Repeated forms/exposure are labeled. The probe is exploratory related presentation transfer. No independent untrained-family or psychometric assessment, learned RL, IQ, brain age or efficacy claim is shipped.
- SQLite supports one application instance. Restore accepts up to 2,000 unverified rows (browser file limit 20 MB, per-mutation body limit 1 MB, chunked imports); very large notebooks require operator backup tooling. Restored material remains segregated from owned live attempts/discussion privileges.
- Source code has automatic formal validation but no claim of independent human curriculum review. Optional future extensions in the original spec remain deliberately deferred.
- The environment's Node 22.22.0 emitted engine warnings for two transitive build utilities; actual tests/build passed. README/CI recommend Node 22.22.2+ / current Node 22. A Starlette test-client deprecation warning is present; it does not fail tests.

## Start and operate

Dependencies, migrated database and the verified bank are installed in this workspace. Run `make dev`, then open **http://localhost:5173**. Fresh checkout: `uv python install 3.12 && make setup && make dev`. Stop development services before browser tests, which own ports 8000 and 5173.

Create an owner only when desired: `make admin` prompts interactively; visit `/admin/login`. AI stays disabled until server-only configuration and an owner-issued guest grant are supplied. Docker path: `docker compose up --build`, opening localhost:8000 for local use. Public hosting additionally needs HTTPS/Secure cookies and `CONTAINER_PUBLIC_ORIGIN`. Exact backup/provider/production commands are in README; nothing has been externally deployed.

## Follow-up: local origin connection fix (2026-10-25)

Reproduced the reported guest-bootstrap failure: localhost:5173 returned 200 while 127.0.0.1:5173 and both loopback URLs on port 8000 returned `403 origin_rejected`. Development now accepts an explicit loopback allowlist on the two shipped ports and the configured local port. Hosted/custom origins and production remain exact; missing/unlisted origins, forged forwarding headers, cross-site Fetch Metadata and invalid CSRF are still rejected. PUBLIC_ORIGIN is normalized and validated; rejected requests now give an actionable configuration message. The running development backend automatically reloaded the fix; the user's services and guest data were preserved.

Verification: **83 backend tests passed**, production frontend type-check/build passed, and **8 additional Chromium regressions passed** (four local URLs at desktop and 360px mobile widths), exercising actual guest bootstrap and a CSRF-protected export against the running development services. These browser checks used isolated fresh contexts and did not submit graded attempts or invoke inference. The initial ten full browser flows above are the earlier implementation run, not a claim they were rerun in this follow-up.

The broader property-test run also exposed a pre-existing ambiguous induction candidate (level 4, seed 163) aborting issuance. The generator still rejects that candidate; the issuance loop now retries within its existing 200-candidate bound. Regression tests verify target agreement after retry and the hard retry limit. Property tests exercise the same verified issuance path used by the app.
