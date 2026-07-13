#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
required=(
  "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v300-unified-workbench.php"
  "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v300.css"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v300.js"
  "backend/app/v300.py" "tests/test_v300_foundation.py" "docs/V300_RELEASE_NOTES.md"
)
for path in "${required[@]}"; do test -f "$path" || { echo "Missing: $path" >&2; exit 1; }; done
if command -v php >/dev/null; then
  php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
  php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v300-unified-workbench.php >/dev/null
  php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php >/dev/null
fi
if command -v node >/dev/null; then node --check wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v300.js; fi
python3 -m py_compile backend/app/v300.py tests/test_v300_foundation.py
python3 -m pytest -q tests/test_v300_foundation.py
(
 cd runner-go
 go test ./...
 go vet ./...
 test "$(go run ./cmd/workbench-runner version)" = "3.0.0"
 go run ./cmd/workbench-runner unified-tools >/tmp/scwb-v300-unified-tools.json
 grep -q 'unified-git' /tmp/scwb-v300-unified-tools.json
)
grep -q "Version: 3.0.0" wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php
grep -q "v300_router" backend/app/main.py
grep -q "sc_workbench_unified" wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v300-unified-workbench.php
grep -q "Unified Project Hub" wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.zip' --exclude='*.pyc' '(-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{20,})' .; then echo "Potential secret detected" >&2; exit 1; fi
echo "Workbench v3.0.0 release checks passed."
