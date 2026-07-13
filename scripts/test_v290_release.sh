#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required=(
  "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v290-documentation-dossier.php"
  "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v290.css"
  "wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v290.js"
  "backend/app/v290.py"
  "tests/test_v290_foundation.py"
  "docs/V290_RELEASE_NOTES.md"
  "runner-go/internal/runner/version.go"
)
for path in "${required[@]}"; do
  test -f "$path" || { echo "Missing: $path" >&2; exit 1; }
done

if command -v php >/dev/null; then
  php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
  php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v290-documentation-dossier.php >/dev/null
  php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php >/dev/null
fi
if command -v node >/dev/null; then
  node --check wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v290.js
fi
python3 -m py_compile backend/app/v290.py tests/test_v290_foundation.py
python3 -m pytest -q tests/test_v290_foundation.py
(
  cd runner-go
  go test ./...
  go vet ./...
  test "$(go run ./cmd/workbench-runner version)" = "2.9.0"
  go run ./cmd/workbench-runner documentation-tools >/tmp/scwb-v290-documentation-tools.json
  grep -q 'documentation-git' /tmp/scwb-v290-documentation-tools.json
)
grep -q "Version: 2.9.0" wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php
grep -q "v290_router" backend/app/main.py
grep -q "sc_workbench_documentation_dossier" wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v290-documentation-dossier.php
grep -q "Documentation & Dossiers" wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-primary-shortcode.php

if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.zip' --exclude='*.pyc' '(-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{20,})' .; then
  echo "Potential secret detected" >&2
  exit 1
fi

echo "Workbench v2.9.0 release checks passed."
