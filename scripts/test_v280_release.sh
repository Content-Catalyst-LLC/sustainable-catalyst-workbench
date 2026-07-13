#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required=(
  "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v280-experiment-automation.php"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v280.css"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v280.js"
  "backend/app/v280.py"
  "tests/test_v280_foundation.py"
  "docs/V280_RELEASE_NOTES.md"
  "runner-go/internal/runner/version.go"
)
for path in "${required[@]}"; do
  test -f "$path" || { echo "Missing: $path" >&2; exit 1; }
done

command -v php >/dev/null && php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
command -v php >/dev/null && php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v280-experiment-automation.php >/dev/null
command -v node >/dev/null && node --check wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v280.js
python3 -m py_compile backend/app/v280.py tests/test_v280_foundation.py
python3 -m pytest -q tests/test_v280_foundation.py
(
  cd runner-go
  go test ./...
  go vet ./...
  test "$(go run ./cmd/workbench-runner version)" = "2.8.0"
  go run ./cmd/workbench-runner experiment-tools >/tmp/scwb-v280-experiment-tools.json
  grep -q 'experiment-python' /tmp/scwb-v280-experiment-tools.json
)
grep -q "Version: 2.8.0" wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php
grep -q "v280_router" backend/app/main.py
grep -q "sc_workbench_experiment_automation" wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v280-experiment-automation.php

if grep -RInE --exclude-dir=.git --exclude='*.zip' --exclude='*.pyc' '(-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{20,})' .; then
  echo "Potential secret detected" >&2
  exit 1
fi

echo "Workbench v2.8.0 release checks passed."
