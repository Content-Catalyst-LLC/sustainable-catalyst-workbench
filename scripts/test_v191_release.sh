#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"

for file in "$ROOT"/wordpress-plugin/sustainable-catalyst-workbench/assets/sc-workbench.js \
            "$ROOT"/wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/*.js \
            "$ROOT"/wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/workers/*.js; do
  node --check "$file"
done

(
  cd "$ROOT/backend"
  PYTHONPATH=. pytest -q
)

(
  cd "$ROOT/tests/frontend"
  node test_code_studio_foundation.js
  node test_javascript_runtime_worker.js
  node test_editor_first_contract.js
)

php "$ROOT/tests/php/test_code_studio_shortcodes.php"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
required = [
    root / 'wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/workers/javascript-worker.js',
    root / 'wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/workers/python-worker.js',
    root / 'wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/runtime-r.js',
    root / 'wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/runtime-sql.js',
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit('Missing runtime files: ' + ', '.join(missing))
print('Runtime asset presence checks passed.')
PY

echo "Workbench v1.9.1 release checks passed."
