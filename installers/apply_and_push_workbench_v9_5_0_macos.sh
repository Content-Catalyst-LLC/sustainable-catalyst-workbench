#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="9.5.0"
TARGET="${1:?Usage: $0 /path/to/sustainable-catalyst-workbench}"
REMOTE="${SCWB_GIT_REMOTE:-origin}"
BRANCH="${SCWB_GIT_BRANCH:-main}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$HERE/payload"
[[ -d "$PAYLOAD" ]] || { echo "ERROR: payload directory missing: $PAYLOAD" >&2; exit 1; }
cd "$TARGET"
git rev-parse --is-inside-work-tree >/dev/null
if [[ -n "$(git status --porcelain)" ]]; then
  echo "=== RESUMING PARTIALLY APPLIED WORKBENCH v$VERSION ==="
else
  echo "=== SYNCHRONIZING $BRANCH ==="
  git switch "$BRANCH"
  git pull --ff-only "$REMOTE" "$BRANCH"
fi

echo "=== APPLYING WORKBENCH v$VERSION ==="
rsync -a --checksum --exclude='.git/' --exclude='data/' "$PAYLOAD/" "$TARGET/"
find "$TARGET/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find "$TARGET/backend" -type f -name '*.pyc' -delete 2>/dev/null || true
chmod +x "$TARGET/scripts/test_v950_release.sh" "$TARGET/deploy/contabo/upgrade_workbench_backend_v9_5_0_contabo.sh" "$TARGET/installers/apply_and_push_workbench_v9_5_0_macos.sh"
TEST_PYTHON="${SCWB_TEST_PYTHON:-}"
if [[ -z "$TEST_PYTHON" ]]; then
  if PYTHONPATH="$TARGET/backend" python3 - <<'PYCHECK' >/dev/null 2>&1
import fastapi,pytest,httpx,pint,scipy,numpy,sympy
PYCHECK
  then TEST_PYTHON=python3
  else
    VENV="${TMPDIR:-/tmp}/scwb-v950-release-venv"; echo "=== BOOTSTRAPPING ISOLATED RELEASE TEST ENVIRONMENT ==="; rm -rf "$VENV"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install -U pip; "$VENV/bin/python" -m pip install -r "$TARGET/backend/requirements.txt"; TEST_PYTHON="$VENV/bin/python"
  fi
fi
echo "=== VERIFYING CANONICAL v9.5.0 IDENTITY BEFORE TESTS ==="
PYTHONPATH="$TARGET/backend" "$TEST_PYTHON" - <<'PYIDENT'
import app.release as r
print('release module:',r.__file__); print('APP_VERSION:',r.APP_VERSION); assert r.APP_VERSION=='9.5.0'
PYIDENT
echo "=== VALIDATING RELEASE ==="
SCWB_TEST_PYTHON="$TEST_PYTHON" "$TARGET/scripts/test_v950_release.sh"
find "$TARGET/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find "$TARGET" -type d -name '.pytest_cache' -prune -exec rm -rf {} + 2>/dev/null || true
find "$TARGET" -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if git diff --cached --quiet; then echo "No new changes to commit; v$VERSION patch may already be committed."; else git commit -m "Workbench v9.5.0 Model Calibration & Parameter Estimation"; fi
echo "=== PUSHING $BRANCH ==="; git push "$REMOTE" "$BRANCH"
if git rev-parse "v$VERSION" >/dev/null 2>&1; then echo "Tag v$VERSION already exists locally."; else git tag -a "v$VERSION" -m "Workbench v$VERSION — Model Calibration & Parameter Estimation"; fi
git push "$REMOTE" "v$VERSION"
[[ -z "$(git status --porcelain)" ]] || { git status --short; echo "ERROR: working tree is not clean" >&2; exit 1; }
echo "PASS: Workbench v$VERSION applied, validated, committed, pushed, and tagged."
