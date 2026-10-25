#!/bin/sh
set -eu
python -m app.cli migrate
python -m app.cli bank
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
