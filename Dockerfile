FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.10.6 AS uv
FROM python:3.12-slim-bookworm AS backend
COPY --from=uv /uv /uvx /usr/local/bin/
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
COPY docs/licenses/ /app/docs/licenses/
COPY --from=frontend /build/dist/ /app/frontend/dist/
COPY scripts/container-start.sh /app/start.sh
RUN useradd --uid 10001 --create-home fluid && mkdir -p /data && chown fluid:fluid /data && chmod +x /app/start.sh
ENV DATABASE_URL=sqlite:////data/human-fluid.db MPLCONFIGDIR=/tmp/matplotlib PATH="/app/backend/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER fluid
EXPOSE 8000
HEALTHCHECK --interval=30s --start-period=120s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz',timeout=5)"
CMD ["/app/start.sh"]
