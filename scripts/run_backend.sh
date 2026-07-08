#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8088
