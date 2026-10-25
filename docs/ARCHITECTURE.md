# Architecture

One FastAPI instance serves a Vue 3 SPA and `/api/v1`. Development uses Vite's same-origin API proxy. Production mounts API routes before the SPA fallback; missing API routes return JSON 404. All application data lives in a durable SQLite directory. WAL, foreign keys, a 20-second busy timeout, and `BEGIN IMMEDIATE` protect read-modify-write operations. A provider reservation commits before the network call; no database write lock spans inference.

## Learning and content

`app/tasks/engine.py` implements generation, public projection, strict structured grading, hints and instance-specific explanations. `solvers.py` independently verifies graph direction/cycles, logical truth assignments and order witnesses. `rules.py` is a bounded scalar/list grammar shared by induction and hypothesis testing. All native generation uses bounded retries and target-consistency checks. Imported content is generated offline into the database using actual pinned Reasoning Gym APIs; it is not fetched during play.

Private task records retain source/configuration/seed/adapter version/raw source/formal model/solution/fingerprint. Public projection includes only instructions, structured rendering data, response kind, opaque instance ID and permitted interaction state. A query exposes only its observed output. Worked proofs and oracle information are generated only for feedback-permitted owned attempts.

## State and policy

Guest sessions use 256-bit opaque tokens; only SHA-256 token hashes are stored. CSRF tokens are session-bound. Attempts have a unique issued-item foreign key; first submissions cannot be rewritten. Queries use principal/key/body-hash replay records. Hints use an explicit index so retry cannot escalate assistance. SQLite write serialization makes single-use grants and quota reservations atomic across threads and restarts.

Sessions issue the next item only after the preceding attempt. Policy version `rules-1` honors focus, caps due review near half a session, covers least-exposed families, and adapts practice levels from six independent samples with five correct and multiple structural fingerprints. Five independent samples with at most two correct reduce by at most one level. Manual levels are logged separately. Due review uses fresh instances, then heuristic 1/3/7-day intervals; next-session review is eligible before the first calendar deadline. Delayed-retention aggregates require an actual elapsed day. Policy logs contain eligible actions, selected action, rationale, outcome, and null propensity. `TeachingPolicy` is the extension seam for a future policy, not a claim of learned RL.

Assessments freeze concrete private tasks and versions when created. The policy cannot choose evaluation items for practice. Checks use two matched configuration forms; repeated forms and prior solution releases are flagged. Completed aggregate results are available separately from practice. Per-item correctness, worked solutions and discussion stay sealed until explicit completion/release. Every journal/export/discussion endpoint shares the permission check.

## Frontend

Vue Composition API components render safe data using text interpolation, native SVG, semantic forms and tables. Pinia holds guest capabilities and CSRF state; cookies remain HttpOnly. Server drafts persist scratchpad, structured answers and confidence. Local storage contains onboarding preferences and temporary unsent numeric text, never identity or grants. Exercise navigation saves drafts; server state is authoritative after refresh. Native radios/selects/buttons support keyboard operation. Every diagram has an equivalent list. Reduced-motion CSS disables transitions.

## Contracts and extension points

The deliberately small explicit TypeScript contract lives in `frontend/src/types/index.ts`, with typed API calls. `docs/openapi.json` is a generated schema snapshot checked against FastAPI in backend tests. Public renderer fields, graph direction, structured booleans and input parsers have contract/component tests. API return types are maintained explicitly rather than a generated full SDK; when changing an endpoint, update its frontend type and the corresponding API/browser tests.

Provider adapters are tool-free server-only chat-completions transports. Disabled is the default. Local addresses are restricted to backend-host allowlisted names. Cloud activation requires explicit operator validation of byte-level token bounds and `max_tokens` enforcement. Request/token budgets include pending and uncertain calls. No pricing or dollar-cap claim is made. An external independent assessment adapter should import independently licensed measures and preserve assessment version/interpretation; none is currently implemented.

## Supported deployment

A single application instance and one SQLite volume. No horizontal-scale claim, anonymous model proxy, external analytics, account registration, distributed queue, or paid service provisioning. The full test provider and solution helpers exist only in `scripts/e2e_server.py`; production never imports that module and the Docker image does not include it.
