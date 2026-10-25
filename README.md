# Human Fluid

**Train strategies. Test transfer.** A guest-first reasoning notebook with five solver-verified task families, transparent adaptive practice, delayed review, fixed checks, and optional owner-approved AI discussion. Python 3.12 / FastAPI / SQLite + Vue 3 / TypeScript.

## Start locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22.22.2+ and npm. There are no required model credentials or cloud services. Installation downloads dependencies; core runtime works offline afterward.

```bash
uv python install 3.12
make setup
make dev
```

Open **http://localhost:5173** or **http://127.0.0.1:5173**. Ctrl+C stops both services. Development also accepts the built SPA on localhost/127.0.0.1:8000; this requires `make build` first. These fixed loopback aliases are available only in development when `PUBLIC_ORIGIN` is itself a local HTTP address. Production accepts only its configured origin. No `.env` is required. To customize settings, copy `.env.example` to `.env` and keep it private.

If a forwarded or hosted URL reports an origin error, set `PUBLIC_ORIGIN` in `.env` to that URL's scheme, hostname, and port (without a path), then restart `make dev`. Compose uses `CONTAINER_PUBLIC_ORIGIN` instead. Do not disable origin or CSRF checks.

Without Make:

```bash
uv sync --project backend --frozen
npm --prefix frontend ci
cd backend
.venv/bin/python -m app.cli migrate
.venv/bin/python -m app.cli bank
.venv/bin/python -m app.cli verify-bank
cd ..
python3 scripts/dev.py
```

On Windows use `.venv\Scripts\python.exe` instead of `.venv/bin/python`. The development launcher selects the platform-specific executable. Bank setup is bounded and idempotent, generating 520 accepted imported items: 50 practice + 15 check per family/level. No LLM generates or grades the core tasks.

## Verify

```bash
make test
make build
make bank
cd frontend
npx playwright install chromium
npm run test:e2e
```

Playwright starts isolated backend/frontend servers on ports 8000/5173; stop `make dev` first. Browser-test history is temporary and the test provider is explicitly synthetic. To use an installed Chromium, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable. Screenshots are written to ignored `frontend/test-results/`.

The initial implementation's actual checks and remaining verification limits are in [IMPLEMENTATION_STATUS](docs/IMPLEMENTATION_STATUS.md).

## Production container

```bash
docker compose up --build
```

Open **http://localhost:8000** for local container use. A named volume stores `/data/human-fluid.db`; startup migrates and generates/verifies required content. The image builds the SPA, serves it from FastAPI, runs one worker as UID 10001 and includes a readiness health check. No Docker daemon was available in the implementation environment, so a container build/run has not been verified there.

For an actual public host, terminate HTTPS at a reverse proxy and set `APP_ENV=production`, `COOKIE_SECURE=true`, and `CONTAINER_PUBLIC_ORIGIN=https://your-real-host` in the private environment. The app fails startup if production cookies/origin are insecure. Keep a **single** application instance against SQLite. Binding defaults to loopback; configure your reverse proxy deliberately. No publishing or paid provisioning is performed by these setup commands.

## Owner and optional AI

```bash
make admin
# Or: cd backend && .venv/bin/python -m app.cli admin --username owner
```

The CLI prompts for and hashes a password; there is no default account. Visit `/admin/login`. In a running container:

```bash
docker compose exec app python -m app.cli admin --username owner
```

Core practice needs no AI. To activate discussion, configure only backend settings in ignored `.env`/runtime secrets: provider (`local` or `cloud`), enable flag, base URL, and model. Local Ollama-compatible example: `AI_PROVIDER=local`, `AI_ENABLED=true`, `AI_BASE_URL=http://localhost:11434/v1`, and a model you have installed locally. In containers use an explicitly configured `ollama` service or `host.docker.internal` where supported; container localhost is the container itself. Local mode rejects funded keys.

Cloud mode additionally requires `AI_API_KEY`, HTTPS and explicit `AI_CAP_VERIFIED=true` after the owner verifies their provider/model's byte-level token bounds and chat `max_tokens` enforcement. Unknown compatibility must remain disabled. No funded call was performed during implementation. Request/token reservations are not a dollar cap; see [SECURITY](docs/SECURITY.md). After restarting with server configuration, sign in as owner, issue an expiring single-use invitation, and deliver it out of band. A guest redeems it under Settings. Only explicit Send triggers inference; no browser API-key form exists.

## Back up and restore

Guest JSON export/restore/deletion are in Settings. Restored results stay unverified and cannot grant privileges or fabricate measured gains. For consistent operational backups:

```bash
backend/.venv/bin/python scripts/backup.py backup /private/path/fluid-backup.sqlite
# Stop make dev / the application before replacing the live database:
backend/.venv/bin/python scripts/backup.py restore /private/path/fluid-backup.sqlite --confirm-replace
```

Keep backups outside the repository and restrict access. For a container, stop writes and use SQLite's backup API inside the container or copy the entire volume while the application is stopped; never copy only a live WAL database file. Restore the volume while stopped and retain its UID 10001 write permissions.

## Design and evidence

[Architecture](docs/ARCHITECTURE.md) · [Content provenance and licenses](docs/CONTENT_PROVENANCE.md) · [Evaluation](docs/EVALUATION.md) · [Security](docs/SECURITY.md) · [Three-minute demo](docs/DEMO.md) · [API schema](docs/openapi.json)

Dependency and logic tasks use actual Reasoning Gym 0.1.25 generators with independent verification. Ordering, induction and active hypothesis testing use native bounded models. The scheduler is **rule-based and RL-inspired**, not a learned tutor. The built-in probe measures exploratory related-task presentation transfer. Human Fluid does not calculate IQ or claim established gains in fluid/general intelligence.
