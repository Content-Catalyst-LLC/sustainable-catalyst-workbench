#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"

for file in "$ROOT"/wordpress-plugin/sustainable-catalyst-workbench/assets/sc-workbench.js \
            "$ROOT"/wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/*.js; do
  node --check "$file"
done

(
  cd "$ROOT/backend"
  PYTHONPATH=. pytest -q
)

(
  cd "$ROOT/tests/frontend"
  node test_code_studio_foundation.js
)

php "$ROOT/tests/php/test_code_studio_shortcodes.php"

echo "Workbench v1.8.0 release checks passed."
