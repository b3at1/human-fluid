# Human Fluid — autonomous implementation specification

**Purpose:** Paste this entire document into a coding agent working inside the intended new repository. It is both the product design and the implementation brief.

**Decisions confirmed by the owner:** Public hackathon website; immediate guest access; Python backend; Vue.js frontend; minimal monospaced yellow-and-white design; transparent rule-based adaptation first, with an interface for future RL; optional cloud/local AI discussion; only owner-approved visitors may use the project’s model connection.

**Product name:** Human Fluid  
**Tagline:** Train strategies. Test transfer.  
**One-line description:** Fluid intelligence training for humans, inspired by reinforcement learning.

---

## 0. Instructions to the implementing agent

Build the working application in this repository. Do not stop at a plan, mockup, scaffold, or collection of disconnected exercises. Read existing repository instructions first, preserve unrelated work, and make reasonable implementation decisions where this specification leaves choices open.

Implement and test the complete MVP below. Use official documentation to resolve actual library APIs and choose mutually compatible, stable versions at implementation time. Lock dependencies. Do not invent APIs, silently replace real integrations with fabricated responses, or claim that a mocked integration was verified live.

The core app must work without a model key or internet connection once dependencies and assets are installed. AI is an optional post-attempt teaching feature; deterministic instruction is the backbone of the product.

Do not wait for credentials to implement the rest. If credentials are missing, finish the provider interface, secure access, error states, and deterministic teaching; document exactly what activation requires. Never solicit secrets through a chat message or commit them to the repository. Avoid provisioning paid services or publishing externally unless separately authorized by the owner or the repository’s deployment instructions.

Build the product described here rather than reproducing an older prototype. In particular: never ship answer keys in public task payloads; never represent new random seeds as evidence of far transfer; never label a rule-based scheduler as learned reinforcement learning.

Create `docs/IMPLEMENTATION_STATUS.md` with a requirement checklist, actual verification performed, known limits, and any deferred work. Update it as implementation progresses. End with startup commands, test results, and any remaining activation steps. Do not invent performance or cognitive-gain numbers.

## 1. Product objective and scientific boundary

Human Fluid is a reasoning-training application designed to help people develop strategies for solving unfamiliar problems. Its longer-term research ambition is improvement in fluid reasoning and transfer beyond the practiced exercise.

The training hypothesis is that varied, solver-verified practice, explicit strategy instruction, fading assistance, and delayed retrieval can improve independent reasoning. The MVP must support evaluating that hypothesis; it must not assume that the hypothesis is already established.

Distinguish these outcomes in code, analytics, and copy:

1. Better performance on practiced task formats.
2. Retention on delayed, unassisted instances.
3. Transfer to reserved structures or presentations.
4. Performance on an entirely untrained task family.
5. Change on an independent, psychometrically supported reasoning assessment.

The first three are feasible MVP outcomes. None alone establishes a change in latent Gf or general intelligence, g. Do not calculate IQ, an invented Gf score, or a composite “brain age.” Educational strategy categories are not independent CHC factors.

Relevant research context: a 2024 meta-analysis found small working-memory improvements but no significant average fluid-intelligence improvement from cognitive training. Callaway’s work motivates modeling and teaching cognitive actions, but does not validate this new app. See the references at the end.

Allowed prominent copy: “Practice reasoning strategies. See what transfers.” Put a short evidence note in About/Research, not a disclaimer interrupting every exercise.

## 2. MVP scope and priorities

### Must ship

- Guest-first practice: begin within two clicks, no registration, payment, or AI setup.
- Five polished task families, with a real Reasoning Gym integration for two of them.
- Structured diagrams, tables, and interactions; no raw Python tuple lists presented as the exercise UI.
- Guided first exposure, independent attempts, progressive hints, deterministic worked explanations, and mistake review.
- Mixed sessions, focused practice, resumable sessions, and a scratchpad.
- Rule-based adaptation using independent performance and delayed review.
- Separate fixed-difficulty checks and explicitly labeled transfer probes.
- Persistent guest progress, export, restore, and deletion.
- Post-attempt AI discussion when the visitor has an active owner-issued grant and a provider is configured.
- Server-side grading, access control, quotas, and secret handling.
- Responsive desktop/mobile experience and keyboard-accessible controls.
- A reproducible local startup path and a containerized production path.
- Meaningful tests for generators, state transitions, evaluation isolation, and security.

### Explicitly defer

Learned RL policies, clinical claims, full CHC assessment, paid public AI access, social leaderboards, billing, full account registration, email delivery, native mobile apps, microservices, vector databases, and on-demand generation by an unconstrained LLM.

An external reasoning assessment integration may be documented as a future adapter. Do not create fake MaRs-IB, ICAR, or ARC results to fill a dashboard.

## 3. Technology and repository layout

Use:

- Python 3.12 as the initial compatibility target; change only if a necessary dependency requires it and document why.
- FastAPI, Pydantic, SQLAlchemy, Alembic, SQLite for the single-instance MVP, and pytest/Hypothesis.
- Vue 3, TypeScript, Vite, Vue Router, and Pinia. Prefer Composition API and single-file components.
- Native SVG for graphs and diagrams; ordinary semantic HTML for lists/tables.
- Vitest and Vue Test Utils for component logic; Playwright for critical browser flows.
- An optional Python provider adapter for cloud or server-local OpenAI-compatible model services.
- CSS design tokens and small custom components. Do not pull in a large visual component library merely for cards and buttons.

SQLite must live in a persistent data directory. Use WAL, a sensible busy timeout, foreign keys, and transactional quota enforcement. Document a single application instance as the supported production topology. Do not claim horizontal scalability with a SQLite file or in-memory rate limits. PostgreSQL migration is future work.

Suggested layout; small deviations are fine:

```text
human-fluid/
  backend/
    app/
      main.py
      config.py
      api/                 # guests, sessions, attempts, checks, discussion, admin
      auth/                # guest sessions, admin, approval grants, CSRF
      db/                  # models, migrations, repositories
      tasks/
        contracts.py
        registry.py
        adapters/          # Reasoning Gym and native families
        solvers/
        explanations/
        validation.py
      curriculum/          # strategy tags, scheduler, review, learner state
      evaluation/          # manifests, split enforcement, summaries
      tutoring/            # provider interface, context construction, quotas
      services/
    tests/
    pyproject.toml
    uv.lock
  frontend/
    src/
      components/
      task-renderers/
      views/
      stores/
      api/
      styles/
      types/
    tests/
    package.json
    package-lock.json
  content/                 # reviewed lessons and task-family definitions
  scripts/                 # bank generation, verification, admin CLI
  docs/
    ARCHITECTURE.md
    CONTENT_PROVENANCE.md
    SECURITY.md
    EVALUATION.md
    IMPLEMENTATION_STATUS.md
    DEMO.md
  .env.example
  .gitignore
  compose.yaml
  Dockerfile
  README.md
```

Use `uv` and npm unless existing repository conventions specify compatible alternatives. Avoid dependency duplication. Generate typed frontend API contracts from OpenAPI, or maintain and test a small explicit contract layer.

Production: build the Vue SPA and serve it from FastAPI or a same-origin reverse proxy. Mount `/api` before SPA fallback, preserve true API 404s, and never serve the SPA in response to a missing API endpoint. Development: Vite proxies `/api` to FastAPI. No runtime frontend secret variables.

## 4. Visual and interaction design

### Visual identity

Minimal, editorial, monospaced, primarily white and yellow. Think of a precise personal research notebook rather than a gaming dashboard or a simulated terminal.

```css
:root {
  --page: #fffef7;
  --surface: #ffffff;
  --ink: #191b16;
  --muted: #606256;
  --line: #dedfd2;
  --yellow: #f4d83b;
  --yellow-soft: #fff5ba;
  --success: #286342;
  --error: #943c2c;
  --font-mono: 'IBM Plex Mono', 'JetBrains Mono', ui-monospace, monospace;
}
```

Use a self-hosted licensed font with a system fallback; include its license. All interface typography is monospaced. Main text is 14–16px with generous line height; headings may be 28–42px with moderate weight. Use black text on yellow buttons, not white text on yellow. Most surfaces stay white. Yellow marks the current focus, primary actions, selected controls, and diagram highlights. Use thin borders, modest 4–8px radii, and little or no shadow.

Avoid gradients, neon glows, glass effects, oversized hero artwork, fake command lines, dense badges, celebratory confetti, and arbitrary dashboard gauges. Display real data only. Empty states should explain the next useful action.

### Layout

Desktop: a narrow left rail, a comfortable main column, and an optional scratchpad/strategy column during exercises. Mobile: compact top navigation, single-column tasks, collapsible secondary information. Work at 360px width without page-level horizontal scrolling.

Navigation: `Train`, `Review`, `Progress`, `About`. Put `AI access` in settings; show `Admin` only to a valid admin session.

Every graphical problem must have an equivalent text representation. Use labeled controls, visible focus, adequate touch targets, reduced-motion support, and no color-only feedback. Screen-reader announcements should describe feedback and loading without reading the entire screen repeatedly.

The exercise is the main event. Do not show library names, seeds, generator versions, API terminology, or research instrumentation in the normal solving flow. Put provenance in an expandable details section.

## 5. Task families and verified content

### Common principles

Each family must have: an explicit formal model; a generator or vetted source; a solver independent enough to catch source mistakes; a structured response type; a safe renderer; three ordered hints; and a worked explanation tied to the actual instance.

Use four designed difficulty levels. Levels are curriculum settings, not psychometric estimates. Increase relational complexity, rule interactions, or hypothesis ambiguity; do not merely enlarge arithmetic or text length. Keep premises visible and allow a scratchpad. No forced speed races.

### A. Dependency reasoning — Reasoning Gym adapter

Reference the `course_schedule` generator in the pinned Reasoning Gym version. Inspect actual APIs instead of assuming a configuration signature.

Model: courses and prerequisite edges. `(a, b)` means course b must precede course a. The UI uses arrows **b → a**. Ask whether all courses can be completed.

Render an SVG graph and a readable list such as “Course 2 requires Course 3.” Include isolated courses. Handle reverse edges and cycles without overlapping arrowheads. Do not color a cycle before submission; that would reveal the answer.

Independent verification: directed-cycle detection and a topological ordering for acyclic cases. Explanations show a concrete cycle or a valid course order. Make arrow direction consistent between problem, legend, hints, and explanation.

Example regression case: `[(2,3),(1,3),(0,3)]` renders Course 3 pointing to Courses 2, 1, and 0. The answer is that completion is possible; Course 3 can be taken first.

### B. Logical consistency — Reasoning Gym adapter

Reference `knights_knaves`. Present each speaker and statement in a separate block. State clearly who always tells the truth and who always lies. The answer is a structured mapping from person IDs to roles, not a brittle string.

Independent verification: enumerate assignments for bounded small populations and evaluate the complete statement under each. Accept an instance only when the intended task has exactly one consistent answer. Handle conjunction, inclusive disjunction, negation, implication, and equivalence correctly. A liar’s whole statement must be false; its every subclause need not be false.

Post-attempt explanations must explain why the assignment works and show a contradiction for at least one rejected alternative. Include an expandable truth table. Synonyms in source text must map to stable role IDs.

### C. Relational ordering — native generator

Generate a small partial order. Ask whether a proposed relationship is necessarily true, necessarily false, or undetermined. Keep those three meanings visible in the response controls.

Solver: transitive reachability in each direction. For undetermined answers, construct two valid complete orderings giving opposite answers. At generation time, validate these witnesses. At small sizes, compare the solver against exhaustive permutation enumeration.

Use neutral abstract labels and a separate scheduling presentation. Changing the labels alone does not constitute transfer; preserve structure metadata so the evaluation can distinguish cosmetic changes from new structures.

### D. Rule induction — native, bounded candidate grammar

Show several input–output examples and ask for the output on a new input. Use an explicit candidate set or a small documented rule grammar. Do not assume finite examples uniquely identify a rule among all possible functions.

Start with simple functions and list transformations: affine transforms, bounded square transforms, reversal, filtering, and ordering. Use small values and short lists. Add composition only after individual operations are learned.

Generate examples that eliminate competing candidates, or ensure all surviving candidates agree on the queried output. Reject ambiguous items. The explanation displays the rule and applies it to every shown example and the target input.

The candidate set is visible in introductory items. Removing it later is a different item configuration with a clearly stated grammar, not permission to use arbitrary hidden rules.

### E. Active hypothesis testing — native interactive environment

A hidden deterministic rule is selected from a visible finite set. The learner chooses queries, sees outputs, and finally identifies the rule. Every query is recorded. Querying is part of the task, not a hint.

Use the same small rule grammar as induction, but log this shared structure: transfer between these two families is related-task transfer, not independent evidence of broad Gf improvement.

The server maintains the hidden rule and returns only observed outputs. Compute the surviving hypotheses and expected information from a proposed query under a disclosed uniform prior. Return that analysis only after submission or as an explicitly assisted hint.

After submission, show how the chosen queries partitioned the hypotheses and compare with an informative alternative. Do not reward unnecessary guessing or penalize a correct early stop when one hypothesis remains. This formal information-gain score is an instructional metric, not a validated intelligence score.

### Source integration and generation safeguards

Use actual Reasoning Gym generators behind an adapter, not an imitation carrying its name. Pin the version/commit and record provenance. The project is published under Apache-2.0; verify the pinned license and notices and inspect any third-party material before redistribution.

Generate a bounded vetted bank for the two imported families during setup. A good initial target is 50 valid practice items and 15 valid check items per family per level. Continue until the requested accepted count is reached or a documented maximum number of generation attempts is hit. Never loop forever. Surface a clear failure if a required family lacks content.

Native families may generate deterministically on demand, but must pass validation before issuance. Use bounded retries. Exclude invalid, ambiguous, duplicate, or source/solver-disagreeing instances and record rejection reasons. No LLM is the sole answer authority.

If a source dependency breaks, isolate the failure, preserve working native families, and report the unavailable adapter accurately. Do not silently substitute toy items while claiming full source integration.

## 6. Content contracts: private truth, public interaction

Use a backend task protocol roughly equivalent to:

```python
class TaskAdapter(Protocol):
    def generate(self, config, seed) -> InternalTask: ...
    def validate(self, task) -> ValidationResult: ...
    def public_payload(self, task, phase) -> dict: ...
    def grade(self, task, structured_answer) -> GradeResult: ...
    def hint(self, task, index, observed_state) -> Hint: ...
    def explain(self, task, answer, observed_state) -> Explanation: ...
```

`InternalTask` includes generator ID/version, seed, config, split assignment, structure fingerprint, formal model, solution, validation result, reviewed lesson references, and provenance. These remain server-side.

`PublicTask` includes an opaque instance ID, family, designed difficulty, concise instructions, safe rendering data, response schema, permitted actions, and the current public interaction state. It must not contain hidden rules, solution assignments, oracle traces, answer keys, future query outputs, or assessment seeds.

Example public dependency task:

```json
{
  "instance_id": "opaque-id",
  "family": "dependencies",
  "difficulty": 1,
  "instructions": "Can you complete every course while respecting the prerequisites?",
  "render": {
    "kind": "dependency_graph",
    "courses": [0, 1, 2, 3],
    "edges": [
      {"prerequisite": 3, "course": 2},
      {"prerequisite": 3, "course": 1},
      {"prerequisite": 3, "course": 0}
    ]
  },
  "response_schema": {"kind": "boolean_choice"}
}
```

A grade result contains correctness, assistance status, permitted feedback, and a stable attempt ID. Incorrect answer is an outcome; invalid response shape is a validation error. Store them differently. Equivalent structured answers must grade identically.

All generation and grading are server-side. An instance ID is not authorization. Each instance belongs to one guest session or an expressly authorized evaluation session. Do not accept a client-supplied solution, difficulty, ownership ID, provider URL, or score.

For imported tasks, preserve raw source content privately for inspection. Build a structured renderer from validated metadata or an explicit adapter; avoid brittle generic regex rewriting of arbitrary source prompts.

## 7. Learning experience

### First visit

The landing screen shows the name, tagline, a short explanation, and `Start training`. Offer `Take a baseline` as a secondary action. Do not force a baseline or an account before a useful experience.

On first use of a family, give a short plain-language orientation and one explicitly marked worked example outside all evaluation pools. Show what a response means. Users may skip this introduction, and may reopen instructions while practicing.

### Session flow

Default mixed session: eight problems, with an estimated duration presented as approximate rather than a timer. Focus mode: six problems from one chosen family. Allow pause/resume, navigation to the journal, and an explicit abandon action. The scheduler chooses the next item after the previous attempt is processed; do not precompute all session difficulty changes and then pretend adaptation occurred.

The trainer shows:

1. Clear instructions and the structured problem.
2. Optional scratchpad, saved as a draft.
3. Structured answer controls with an explicit submit button.
4. Optional confidence: “How likely is your answer to be correct?” Confidence can be omitted; do not silently invent a value.
5. Three progressive hints in practice only.
6. After submission: correctness, the actual worked explanation, and an invitation to discuss the problem.
7. One optional reflection: missing constraint, untested alternative, wrong rule, execution mistake, unclear instruction, or other.

Capture first submitted answer once. Additional exploration after feedback is review, not a new first attempt. No duplicate grading when a user double-clicks, retries after a timeout, or resumes a submitted item.

Hints are meaningful instance-specific scaffolding:

- Level 1: remind the learner of a relevant principle.
- Level 2: identify a useful subproblem or contradiction to examine.
- Level 3: demonstrate a partial inference while leaving a remaining step.

Assistance usage is recorded on the server before the hint is returned. A request retry must not increment the count twice. A failed hint request must not leave an unexplained assistance flag. Distinguish reopening generic instructions from revealing an instance-specific hint.

### Retention and review

Maintain due-review entries for errors and heavily assisted answers. Initial heuristic intervals: a fresh parallel item next session or after roughly one day, then three days, then seven days following independent success. This is a design heuristic, not an empirically optimal Gf schedule.

During review, do not merely ask the user to remember the exact prior answer. Link the original attempt to a fresh instance sharing the relevant structural feature. Show the original solution in the journal, with a `Try a fresh example` action.

A session should mix targeted review, frontier difficulty, and variation. Reward completed work and independent understanding; do not impose streak loss, public ranking, or speed-based pressure.

## 8. Transparent adaptation and the future RL boundary

### Learner state

Track per family and level:

- Independent first-attempt outcomes.
- Assisted outcomes and hint level.
- Recent sample count.
- Delayed unaided outcomes.
- Presentation/structure exposure.
- Review due dates.
- Confidence calibration where supplied.

Use conservative Beta(1,1) smoothing for binary independent outcomes if useful; describe it as a scheduling estimate, not a latent intelligence model. Do not update independent success from assisted completions, worked examples, discarded attempts, or AI-assisted review.

### Initial scheduler

Implement a deterministic, testable policy with a random seed only for tie-breaking:

1. Honor the chosen focus and any evaluation plan.
2. In mixed practice, select a due review item when appropriate, but cap review at approximately half a normal session.
3. Ensure broad coverage: do not repeatedly select the most comfortable family just because its accuracy is high.
4. Select practice at the current family level; introduce an alternate presentation periodically after basic understanding.
5. Advance a family after at least six recent independent attempts at the current level, at least five correct, and evidence from more than one structural configuration.
6. After at least five independent attempts with two or fewer correct, offer a simpler worked bridge and reduce subsequent practice by at most one level. Do not silently demote the user after one error.
7. Manual level selection remains available and logged. It does not alter fixed evaluation difficulty or erase prior outcomes.

Record the policy decision and a short rationale, such as “Due review: missed circular dependency last session.” Keep statistical internals out of the normal product flow.

### RL-ready interface, not fake RL

Create a policy interface such as `select_next(observation, eligible_actions) -> TeachingAction` and persist policy versions. Candidate actions include family, level, presentation, worked-example offer, and assistance schedule. Log the eligible action set, selected action, rationale, and eventual observable learning outcomes.

The rule-based MVP has no meaningful learned-policy probability distribution. Store action probability as null, not a fabricated propensity. Logs alone do not make valid off-policy RL evaluation possible. Future policy learning will require sufficient data, exploration design, outcome definitions, and safeguards against optimizing immediate assisted accuracy.

Describe the MVP as “RL-inspired.” It reuses verified training environments and reward/feedback ideas; it is not training a reinforcement-learning agent to teach people yet.

## 9. Evaluation and transfer design

### Three built-in measurement modes

| Mode | What changes | Interpretation |
|---|---|---|
| Practice | Curriculum adapts; hints allowed | Exercise learning |
| Unaided check | Fixed family mix and difficulty; no hints or tutor | Independent performance on familiar task families |
| Transfer probe | Predeclared reserved structure/presentation or task family | A specified type of generalization, labeled narrowly |

Freeze evaluation manifests before a training block. Record item and generator versions, difficulty configuration, form assignment, and planned feedback-release policy. The scheduler must never train directly on evaluation items.

Splits have more than different seeds:

- Exact item IDs are disjoint.
- Structure fingerprints distinguish isomorphic dependency graphs and role-renamings.
- Related renderings of one structure stay together unless the purpose is an explicitly labeled presentation-transfer probe.
- Reserve selected rule compositions or structural patterns for generalization probes.
- A genuinely untrained task family must not quietly appear in onboarding or mixed practice.

Do not claim mathematical independence between related tasks. A named transfer type must describe exactly what was withheld. More difficult versions of a trained task are difficulty generalization; relabeled versions are presentation generalization.

### Assessment behavior

Default check: ten balanced items at a fixed configuration. An introductory and follow-up form must be different but matched by the designed configurations; do not call them psychometrically equated unless validated.

During a check, suppress hints, strategy cards, worked explanations, and AI discussion. Premises remain visible; scratchpad policy remains consistent. Journal endpoints and exports must enforce the same feedback embargo as the task view. A hidden button is not sufficient.

Release aggregate results at completion. Keep item solutions sealed until the configured evaluation block ends or the learner explicitly releases them with a clear “this will expose assessment content” action. Log releases and mark subsequent related probes as exposed. The ordinary practice journal is fully reviewable immediately.

A transfer probe may use a different instructional wrapper, but must explain its controls without teaching the target strategy. Record prior exposure. Show “exploratory probe” when a task family or matching quality has not been validated.

### Progress display

Show sample counts and assistance status. Provide:

- Completed sessions and independent attempts.
- Independent practice accuracy by family and designed level.
- Hint dependence over time, with changing difficulty acknowledged.
- Delayed-review outcomes.
- Check history grouped by fixed manifest/version.
- Transfer-probe results by transfer type.
- Optional confidence Brier score: mean `(confidence_probability - outcome)^2`, with sample count and a plain explanation that lower is better.

Do not subtract two noisy percentages and label it an intelligence gain. Do not aggregate unequal difficulty distributions into an apparently comparable trend. No leaderboard or normative percentile without suitable reference data.

An external assessment adapter can be a documented extension point, not a production stub reporting invented results. MaRs-IB and ICAR are potential sources to investigate under their exact terms; neither automatically supplies a complete Gf measurement design.

## 10. Optional AI discussion

### User experience

After an ordinary attempt is submitted, show `Discuss this problem`. The same action is available in the journal. For assessments, enforce the configured release rules on the server before discussion is allowed.

The discussion screen contains the rendered problem, the learner’s answer, an expandable deterministic solution, relevant observations, and a conversational panel. Suggested messages:

- “Explain what the question is asking.”
- “Why is my answer correct or incorrect?”
- “Show me a concrete example.”
- “Here is how I reasoned about it…”

Only an explicit Send action or explicit suggested-question click triggers inference. Opening the page, mounting a component, typing, refreshing, or viewing the journal must not call a model. Prevent duplicate submission and preserve the text after errors. Do not change the original score because of discussion.

Unapproved visitors see a clear locked state and can still read the deterministic explanation. Approved visitors see provider availability and remaining allowances. If the provider is disabled or unavailable, retain a fully functional core app; do not impersonate an AI with canned replies.

### Provider interface

Define `TutorProvider` with capabilities, configuration validation, request token estimation/bounding, response generation, usage parsing, and redacted errors. Implement:

1. A disabled provider used by default.
2. A cloud adapter for an explicitly configured model endpoint.
3. An OpenAI-compatible server-local adapter, suitable for an operator-configured Ollama or compatible service.

Compatibility is a subset, not a promise that every provider supports every option. Consult actual provider documentation, test parameter handling, and require enforceable output caps. Local inference runs on the backend host, not automatically on a website visitor’s laptop. Do not fetch `localhost` from the visitor’s browser and claim server-local inference is supported.

All endpoint URLs and model IDs are server-configured. Visitors cannot choose arbitrary URLs, override system instructions, select more expensive models, or supply a key in a browser form. Never put cloud credentials in `VITE_*` variables.

The application’s provider interface is independent of any particular coding-agent plugin. Do not make the generated project require ChatGPT Sites or OpenAI Developers plugins to run. Use normal deployment secrets or ignored environment files.

### Context construction

Construct context on the backend from the owned attempt and canonical task:

- Plain-language task instructions.
- Structured premises, diagrams, example pairs, candidate grammar, and observed queries.
- The submitted answer and solver result.
- A concise deterministic worked explanation.
- Optional learner scratchpad, disclosed before the first send.
- Bounded discussion history.

Do not send API keys, approval codes, session cookies, admin data, unrelated attempts, hidden future assessments, or a private corpus dump. Do not accept the browser’s submitted reference solution as truth.

Tutor behavior: explain plainly, answer the specific question, distinguish instructions from inference, use short concrete examples, and ask about the learner’s reasoning when necessary. Do not assume an incorrect response reveals a particular misconception. If a genuine ambiguity or source error appears, flag it rather than insisting that the oracle must be right. Let the learner report the item. The tutor cannot edit grades, grant access, execute arbitrary code, browse the web, or perform administrative actions.

Generate teaching explanations, not demands for a private chain-of-thought transcript. An optional brief user explanation is enough. Do not require lengthy reasoning text for every task.

Use ordinary safe text rendering, or sanitized Markdown with raw HTML disabled. Treat problem data and user notes as untrusted content in the model context. Prompt injection must not confer tools, secrets, grading authority, or provider control.

## 11. Guest identity and owner-approved model access

### Guest practice

On first use, create a cryptographically random opaque guest session and set an HttpOnly cookie. Store only a hash of its token in the database. The frontend does not generate an authoritative user ID and cannot select another user’s ID in a request.

Persist attempts and sessions in the server database. Browser storage may cache drafts and non-sensitive UI preferences, but it is not the source of authorization or grading truth. Explain that clearing the cookie loses automatic access to that guest profile, and offer export/restore. No fingerprinting or unnecessary personal information is needed.

### Admin and AI grants

Implement a small admin login for this MVP; no public account-registration system. Bootstrap an admin through an interactive CLI with a password prompt, hash it with Argon2id, and store no known default password. Use separate server sessions with role checks and a short admin-session lifetime. Rate-limit login and require CSRF protection.

The admin can:

- Enable or disable inference globally.
- Issue an expiring, single-use AI approval code with a human-readable label and quotas.
- Review active grants and recent request counts.
- Revoke a grant immediately.
- Inspect non-secret provider configuration status and quota state.

Approval codes are high-entropy random credentials, stored hashed and displayed once. The owner delivers them out of band. Do not put codes in query strings, analytics, or access logs. A visitor redeems a code through a POST form, binding the grant to the current server-controlled guest session and rotating the session token. Redemption must be atomic, single-use, and expiry-checked.

This is permission by possession of an owner-issued invitation, not verified-email identity. Document that a user who shares their unused code delegates their invitation. Do not claim that a label or typed email proves identity. Supporting another device requires a new grant or a future authenticated account feature.

Every inference request must recheck the session, grant validity, expiry, revocation, assessment release state, and quotas. Issuing a public guest session does not authorize AI. Hiding a button is not authorization. Restoring a backup must never create a grant or admin role.

### Secret and spending controls

- Model keys live only in backend runtime secrets/ignored environment files. They never enter public responses, source maps, prompts, browser storage, downloadable exports, frontend bundles, or logs.
- Exclude environment files, real databases, private logs, and credentials from Git and container build contexts. Commit `.env.example` with names and placeholders only.
- Production cookies use Secure, HttpOnly, SameSite=Lax or stricter, and bounded lifetime. Development exceptions must be explicit.
- Require same-origin JSON POSTs plus a session-bound CSRF token for mutations. Configure exact development origins if needed; no credentialed wildcard CORS.
- Enforce body and message-size limits before materializing unlimited input. Validate all IDs and ownership on every resource route.
- The inference service has no arbitrary proxy or model-execution tools. Restrict outgoing model traffic to the configured provider. The local adapter’s private address is operator-configured and unavailable as a user-controlled SSRF target.
- Never expose raw provider errors or stack traces to clients. Logs contain request IDs, timings, coarse outcomes, and usage, not credentials or full conversations by default.

Initial configurable limits: 4 requests per minute and 30 per UTC day per grant; 100 requests per UTC day globally; at most 6,000 input tokens and 1,500 output tokens per request; no parallel inference for one grant. These are operator defaults, not scientific parameters.

Implement limits in the persistent database with atomic transactions. Reserve capacity before a provider call, including a conservative worst-case input/output token allowance. Prevent concurrent requests from passing the same remaining budget. Require a provider-specific tokenizer/estimator and verified cap semantics for funded cloud mode; if safe bounds cannot be established, fail closed rather than silently disabling limits. Local mode still has request/concurrency controls.

Use idempotency keys bound to principal and request-body hash. Repeated identical requests must not call the provider twice. Reusing an idempotency key for different content returns a conflict. Persist request state: reserved, completed, failed, or outcome-unknown. On uncertain provider timeouts, retain the conservative reservation; do not automatically retry or falsely claim no charge occurred. Reconcile usage only when trustworthy usage is returned. Budget reservations must include pending requests and survive restarts.

Call/token allowances are not a guaranteed dollar cap. If the operator wants a monetary cap, require explicit current per-model pricing and reserve worst-case priced usage, or use a provider-enforced hard limit when available. Never label a provider’s alert-only budget as a hard spending stop.

No live funded call during autonomous implementation unless the owner explicitly authorizes the credential and test. Stub-provider tests are required; real-provider verification must be reported separately.

## 12. API contracts and state transitions

Use `/api/v1`. Routes may be organized differently if behavior stays equivalent. Generate OpenAPI and typed client contracts. Responses must have consistent errors with a stable code, safe message, and request ID.

| Method / route | Purpose |
|---|---|
| `POST /guest` | Establish guest identity and a CSRF mechanism |
| `GET /me` | Current role/capabilities, not raw credentials |
| `GET /families` | Available curriculum and safe lesson metadata |
| `POST /sessions` | Start mixed/focused/check/probe session |
| `GET /sessions/{id}` | Resume owned state without revealing sealed content |
| `POST /sessions/{id}/next` | Idempotently issue the next item |
| `GET /instances/{id}` | Retrieve the current owned public task |
| `POST /instances/{id}/queries` | Active experiment observation, server-recorded |
| `POST /instances/{id}/hints` | Reveal next permitted hint and mark assistance |
| `POST /instances/{id}/submit` | Grade once, create immutable first attempt |
| `PATCH /attempts/{id}/reflection` | Save notes/reflection, never correctness |
| `GET /attempts` | Paginated owned journal, respecting assessment embargo |
| `GET /attempts/{id}` | Owned attempt and permitted feedback |
| `GET /progress` | Honest aggregates with denominators/config versions |
| `GET /reviews/due` | Due review summary |
| `GET /ai/status` | Approval/configuration/quota state, no secret values |
| `POST /ai/redeem` | Redeem a single-use approval code |
| `POST /attempts/{id}/discussion` | Explicit bounded inference for an approved attempt |
| `GET /attempts/{id}/discussion` | Owned discussion history |
| `POST /export` | Download owned versioned progress data |
| `POST /restore` | Validate and restore progress into the current principal |
| `DELETE /me/data` | Explicit deletion flow for the current guest’s data |
| `/admin/...` | Authenticated grant and provider-status controls |
| `GET /healthz` | Liveness, no environment dump |
| `GET /readyz` | Core DB/content readiness; AI absence is not core failure |

Task state: issued → in progress → submitted → reviewed. Query and hint events occur only before submission unless an explicitly separate exploration mode is opened. Repeated submit returns the same stored result rather than a new attempt.

Session state: active → paused → active → completed, or abandoned. Pausing must not lose answer drafts, observations, scratchpad, hints, or already recorded submissions. A completed session cannot silently become active again. Changing modes cannot reset an item’s assistance history.

Mutations use idempotency where duplication would affect grading, queries, grants, or spending. Same principal + same key + same body returns the same logical result. Server timestamps determine ordering. Client active-duration telemetry is useful context but not trusted for authorization or scoring.

## 13. Persistent data model

Suggested tables:

- `guest_sessions`: hashed token, guest principal, creation, last seen, expiry.
- `admin_users`, `admin_sessions`: password hash and separately scoped sessions.
- `ai_invites`, `ai_grants`: hashed invite, label, expiry, redemption, principal binding, revocation, quotas.
- `task_templates`: source version, adapter version, family, config, license/provenance.
- `task_instances`: private formal model, validation, solution, split, fingerprint.
- `issued_items`: principal, task instance, session, state, assistance, query state.
- `sessions`: principal, mode, manifest version, timestamps, current position.
- `attempts`: issued item, first answer, result, optional confidence, timestamps, assistance snapshot.
- `events`: bounded query/hint/submission/review events with typed payloads.
- `reflections`: attempt-linked notes and user-attributed error category.
- `learner_states`: scheduler summaries, version, and exposure counters.
- `review_queue`: due date, target feature, previous attempt, interval state.
- `evaluation_manifests`, `evaluation_releases`: predefined splits/forms and exposure records.
- `discussion_messages`: owned thread, safe message content, timestamps.
- `inference_requests`, `quota_reservations`: idempotency, limits, pending usage, final outcome.
- `item_reports`: issue category, affected task version, reproduction metadata.

Use uniqueness constraints and foreign keys rather than relying on UI assumptions. Never merge independent attempts with post-feedback revisions. Keep source version and evaluation version attached to results so later generator changes do not reinterpret historical scores.

Exports include schema version, owned history, notes, provenance IDs, and permitted discussion; never secrets, session tokens, grants, admin roles, or sealed assessment solutions. Restore validates size, schema, enums, numerical bounds, content lengths, and row counts. It cannot import another principal’s identity, executable code, or provider configuration. Imported outcomes are marked restored/unverified for analytics; do not let editable JSON fabricate canonical assessment gains.

For deletion, explain what is removed, require an explicit confirmation, revoke associated AI grants, and clear the cookie. Do not reset other visitors’ data. Avoid third-party analytics in the MVP.

## 14. Frontend views and components

### Train

A compact welcome, current session/resume action, five family cards, due-review summary, and secondary check/probe actions. Before enough data exists, show “No attempts yet” rather than zeros implying measured ability. Start a mixed session immediately.

### Exercise

`TaskShell` owns the attempt lifecycle. Family-specific components render only safe `PublicTask` data:

- `DependencyGraph`: prerequisites-first arrows, node labels, equivalent list, responsive SVG.
- `SpeakerStatements`: speaker cards and structured role choices.
- `OrderingProblem`: premises, proposed claim, three clearly defined options.
- `RuleExamples`: aligned input/output pairs, readable candidates, structured numeric/list response.
- `HypothesisLab`: candidate rules, query controls, observed outputs, final rule selection.

Support keyboard operation, loading, network failure, retry without duplicate mutation, and refresh/resumption. Preserve input if the server rejects a malformed answer. Never animate new evidence into place in a way that obscures which query caused it.

`WorkedExplanation` renders explicit steps and witness data. In a graph explanation, highlight the particular cycle or ordering only after feedback becomes available. In an undetermined-order explanation, display the two counterexample orders side by side.

### Review

Filter independent mistakes, assisted outcomes, and family. Display the actual historical task and explanation. Let the user save a reflection, report a confusing item, open eligible discussion, or request a fresh related item. Do not leak embargoed assessment content through search previews or hidden DOM nodes.

### Progress

Small transparent charts/tables with source counts and mode labels. Keep practice trends separate from fixed-manifest checks. Use yellow/ink bars and explicit labels. Offer a data table for every chart. No fake smooth lines or unexplained ability percentages.

### Discussion

Problem context and conversation together on desktop, stacked on mobile. Saved history is specific to one attempt. Show a plain explanation of what is sent to the provider before first use, especially scratchpad content. Include `Clear discussion`, with confirmation, and distinguish clearing a thread from deleting the graded attempt.

### About / Research

Explain the learning hypothesis, the limits of transfer evidence, the RL-inspired versus learned-RL distinction, source provenance, and privacy. Provide links rather than reproducing entire papers. Keep this accurate and compact.

### Settings / AI access / Admin

Guests can export, restore, manage drafts, delete their data, and redeem an invitation. Only admins can issue/revoke grants or control inference. No visitor-facing API key box. Provider status reports “configured / disabled / unreachable” and safe diagnostics, never secret values.

## 15. Quality gates and acceptance tests

### Formal correctness

- Dependency answers agree with an independent solver. Both valid orders and cycle witnesses are checked against all edges.
- Logical assignments satisfy all truth/lie constraints; non-unique items are excluded.
- Ordering classifications agree with exhaustive enumeration at small sizes; undetermined items have two valid opposite witnesses.
- Induction examples constrain the intended target output; ambiguous items are rejected.
- Interactive queries return the hidden rule’s actual output, are replayable, and do not reveal unqueried data.
- Reproducibility includes generator version, configuration, seed, and adapter version.
- Source/solver disagreement is quarantined and visible in validation reports.

### Learning lifecycle

- Start as a guest, complete a session, refresh, and resume without losing state.
- First-submit correctness is immutable; duplicate submit does not create attempts.
- Hints mark assistance server-side, including when requested from another tab.
- Confidence is captured before feedback or marked omitted.
- Due reviews select fresh relevant instances and do not erase the original error.
- Advancement is based on qualifying independent samples; manual level changes and assisted success cannot fake mastery.
- An unfinished check does not expose solutions through journal, export, discussion, or API routes.
- Evaluation manifests cannot be selected by the practice scheduler.
- Public payloads have no answer, hidden rule, assessment seed, or private solution trace.

### Security and cost

- Two guest sessions cannot read, mutate, export, delete, or discuss each other’s records by guessing IDs.
- Unapproved/expired/revoked grants produce no provider call.
- Restoring a backup cannot grant AI/admin access or set a provider endpoint.
- Two simultaneous redemptions cannot consume the same invite successfully.
- Same-origin/CSRF enforcement rejects cross-site mutations.
- Quotas and reservations remain correct under concurrent requests and across restarts.
- Duplicate inference does not call the provider twice; altered duplicate bodies conflict.
- Provider errors are redacted. Output/response logs cannot include runtime secrets.
- A synthetic canary secret is absent from public assets, API outputs, exported data, and model input.
- Local/disabled provider modes do not unexpectedly call a paid endpoint.
- Oversized bodies/history and invalid response types are rejected cleanly.

### UI and deployment

Use automated browser tests for guest start, at least one full session, graph direction, hint use, resume, journal review, fixed check completion, and discussion with a clearly identified test provider. Run at desktop and narrow mobile widths.

Inspect screenshots where tooling permits: homepage, dependency exercise, explanation, discussion, and mobile exercise. Verify readable diagrams, contrast, focus, labels, and overflow. If actual browser QA is unavailable, say so; do not claim screenshots were inspected.

Run backend tests, frontend type checks, targeted frontend tests, production build, migration/setup smoke checks, and the core browser flow. Do not demand a paid provider to pass CI. Keep synthetic test histories clearly segregated from real user data.

CI should run tests and build on pull requests without deployment secrets. A missing optional AI key must not fail core startup. Production readiness must fail on an unusable database, missing required content, or invalid security configuration.

## 16. Implementation sequence and completion gates

### Gate 1: Reproducible foundation

Scaffold Python/Vue in the target repo, configure dev proxy/same-origin production, add migrations and guest identity, establish design tokens, and ship a real vertical slice: generate → render → answer → verify → explain → persist.

Acceptance: one command starts a core app that works without an API key. No fake data is necessary for the core flow.

### Gate 2: Content and teaching

Integrate the two actual Reasoning Gym adapters, add the three native families, solver witnesses, curated lessons, hints, and structured renderers. Generate and validate the initial bank. Add item reporting.

Acceptance: all five families are playable with correct worked feedback and provenance. Source failures are reported, not concealed.

### Gate 3: Persistent curriculum and evaluation

Implement resumable sessions, journal, due reviews, adaptive levels, frozen check manifests, transfer labels, and honest progress summaries. Enforce release rules on every route.

Acceptance: a guest can complete a practice block and compare eligible checks without exposing solutions early or confusing practice with transfer.

### Gate 4: Approved discussion

Implement admin bootstrap, single-use invitations, grants, provider adapters, request reservations, and per-attempt chat. Ship complete disabled/unconfigured states and provider-stub tests.

Acceptance: only an active approved guest can invoke the configured model; secrets and spending controls pass tests; deterministic instruction is unaffected when inference is off.

### Gate 5: Hackathon polish

Finish mobile layout, accessible controls, errors, restore/export/deletion, deployment docs, and a short demo script. Run all relevant checks. Inspect actual screenshots when possible. Fix misleading copy and remove scaffold placeholders.

Acceptance: a stranger can start immediately, understand one unfamiliar exercise, learn from a mistake, and find their saved progress. An owner can configure AI safely without editing frontend code.

Implement required gates in order, but keep each vertical slice functional. Do not spend the whole task perfecting infrastructure while leaving the training flow empty. If time is constrained, defer extras—not formal correctness, ownership checks, solution privacy, or honest reporting.

## 17. Startup, operational defaults, and documentation

Provide exact working commands in README for:

1. Installing pinned backend/frontend dependencies.
2. Migrating the database.
3. Generating/verifying content banks.
4. Starting both development services.
5. Creating an admin securely with an interactive password prompt.
6. Running unit/integration/browser tests.
7. Building and starting the production container.
8. Configuring an optional model provider through server-only secrets.
9. Backing up and restoring the persistent database.

Provide a single documented entry point such as `make dev` or an equivalent cross-platform script. Support `docker compose up --build` with a durable volume and health checks. Container runs as a non-root user with a writable data directory. Do not require Ollama or a cloud account for the standard startup path.

`.env.example` should document these concepts with placeholders only; choose consistent actual names in code:

```dotenv
APP_ENV=development
PUBLIC_ORIGIN=http://localhost:5173
DATABASE_URL=sqlite:///./data/human-fluid.db
COOKIE_SECURE=false
AI_PROVIDER=disabled
AI_ENABLED=false
AI_BASE_URL=
AI_MODEL=
AI_API_KEY=
AI_MAX_INPUT_TOKENS=6000
AI_MAX_OUTPUT_TOKENS=1500
AI_GRANT_REQUESTS_PER_MINUTE=4
AI_GRANT_REQUESTS_PER_DAY=30
AI_GLOBAL_REQUESTS_PER_DAY=100
```

Additional token-budget, session-lifetime, admin, and signing settings should be documented. Generate necessary session/signing secrets securely during explicit setup or require them in production; never embed a development fallback that remains valid when production mode is selected.

No anonymous endpoint should reveal complete configuration, environment variables, arbitrary file content, a database browser, or full exception details. Health routes return minimal status.

## 18. Hackathon demonstration

Write `docs/DEMO.md` for a roughly three-minute live demonstration:

1. Open the white/yellow monospaced homepage and start immediately as a guest.
2. See a dependency graph instead of a raw tuple list.
3. Submit an answer, inspect a concrete proof, and try a fresh related problem.
4. Show active hypothesis testing: choose a query, observe its result, and see why it was informative after submitting.
5. Show a mixed session adapting with an inspectable rationale.
6. Open a completed attempt and discuss a confusing point if the model is configured and the guest is approved; otherwise show the honest unconfigured state.
7. Show independent check results separately from practice, with sample counts.
8. Explain that the project is RL-inspired and designed to test transfer, not evidence that all users’ Gf has increased.

If deterministic demo data is needed, provide a separate local demo profile and clearly mark synthetic history. Never present simulated longitudinal improvement as a real experiment.

## 19. Future extensions, after a working MVP

- A real contextual-bandit scheduler with randomized exploration, meaningful delayed outcomes, and a rule-based baseline.
- Stronger learning experiments with an active control, predefined outcomes, and delayed independent assessments.
- Additional planning environments modeled after the cognitive-tutor literature.
- Independently licensed/calibrated reasoning assessments with appropriate alternate forms and score interpretation.
- Accounts for cross-device history and a PostgreSQL deployment.
- Automated content-quality reports and human-reviewed explanation improvements.

Do not implement these as empty screens or fake “coming soon” metrics in the MVP. Document extension points where they are useful.

## 20. References and how to use them

These sources were checked while preparing this specification. Their presence establishes provenance or design motivation, not validation of Human Fluid. Verify the selected version, API, availability, and license at build time.

### Code and data

1. **Reasoning Gym — primary content dependency**  
   https://github.com/open-thought/reasoning-gym  
   Gallery: https://github.com/open-thought/reasoning-gym/blob/main/GALLERY.md  
   Use its procedural generation and verification infrastructure behind adapters. It was developed for model reasoning training/evaluation; it is not a validated human Gf curriculum. Pin a release/commit, preserve notices, and validate selected task semantics independently.

2. **AI for improving human planning — instructional research reference**  
   https://github.com/fredcallaway/ai-for-improving-human-planning  
   Contains experiment demonstration material, human data, and analyses for the planning-tutor work. Inspect for teaching mechanisms and evaluation patterns. Do not assume every research repository or dataset has the same reuse terms.

3. **Mouselab-MDP — optional planning-interface reference**  
   https://github.com/RationalityEnhancement/Mouselab-MDP  
   A research interface for making information-acquisition actions observable. Optional; do not make MVP completion depend on an old JavaScript plugin being directly compatible with Vue.

4. **Optimal nudging — computational-model reference**  
   https://github.com/fredcallaway/optimal-nudging  
   Reference for modeling how information presentation changes decisions. Reproducing that optimizer is outside the MVP; a simple hint is not automatically an optimal nudge.

5. **MaRs-IB analysis and calibration material — future measurement reference**  
   https://github.com/ndawlab/mars-irt  
   Stimuli: https://osf.io/g96f4/  
   The analysis repository and the stimuli are distinct resources; check both terms before redistribution. This measures matrix reasoning and is not, by itself, a complete Gf assessment.

6. **ICAR — future cognitive-assessment reference**  
   https://github.com/frenchja/icar  
   https://www.psychometrics.cam.ac.uk/research/the-international-cognitive-ability-resource-icar  
   Optional assessment source, not a required MVP training dependency.

7. **ARC — optional unfamiliar-task probe reference**  
   https://github.com/fchollet/ARC-AGI  
   Useful as a separate puzzle/benchmark resource. Do not make it the principal day-to-day curriculum or call a score change a human intelligence increase. Check the exact version and terms.

### Research

8. Rodas, Asimakopoulou, and Greene (2024), **Can we enhance working memory? Bias and effectiveness in cognitive training studies.**  
   https://doi.org/10.3758/s13423-024-02466-8  
   Motivation for separating training-specific gains from broad reasoning outcomes.

9. Callaway and colleagues (2022), **Leveraging artificial intelligence to improve people’s planning strategies.**  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8944825/  
   Motivation for feedback on cognitive strategies and evaluation of retention/transfer. Do not generalize its findings to arbitrary minigames.

10. Callaway, Hardy, and Griffiths (2023), **Optimal nudging for cognitively bounded agents.**  
    https://fredcallaway.com/pdfs/callaway2023nudging.pdf  
    Alternative copy: https://cocosci.princeton.edu/papers/callaway2023nudging.pdf  
    Motivation for modeling deliberation and information accessibility. Improved assisted choices do not by themselves demonstrate durable learning.

### Official implementation documentation

- FastAPI: https://fastapi.tiangolo.com/
- Vue: https://vuejs.org/guide/introduction.html
- Pinia: https://pinia.vuejs.org/
- Vue Router: https://router.vuejs.org/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Hypothesis: https://hypothesis.readthedocs.io/
- Playwright: https://playwright.dev/
- Ollama OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
- OpenAI API documentation, if that adapter is enabled: https://developers.openai.com/api/docs/

Consult current official provider documentation before implementing inference. This specification intentionally does not hard-code a model name, price, or an assumption that all OpenAI-compatible services implement the same controls.

---

## Final instruction

Proceed autonomously to create the working Human Fluid MVP in the current repository. The deliverable is a functioning, tested Python/Vue application with real verified exercises, meaningful teaching, inspectable adaptation, responsible transfer measurement, and optional securely approved AI discussion. Complete the implementation, not merely the scaffolding. Report what actually works and what was actually tested.
