#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.5.0"; TARGET="${1:?Usage: $0 /path/to/sustainable-catalyst-workbench}"; REMOTE="${SCWB_GIT_REMOTE:-origin}"; BRANCH="${SCWB_GIT_BRANCH:-main}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PAYLOAD="$HERE/payload"
[[ -d "$PAYLOAD" ]] || { echo "ERROR: payload directory missing: $PAYLOAD" >&2; exit 1; }
cd "$TARGET"; git rev-parse --is-inside-work-tree >/dev/null
if [[ -n "$(git status --porcelain)" ]]; then echo "=== RESUMING PARTIALLY APPLIED WORKBENCH v$VERSION ==="; else echo "=== SYNCHRONIZING $BRANCH ==="; git switch "$BRANCH"; git pull --ff-only "$REMOTE" "$BRANCH"; fi
echo "=== APPLYING WORKBENCH v$VERSION ==="; rsync -a --exclude='.git/' --exclude='data/' "$PAYLOAD/" "$TARGET/"
chmod +x "$TARGET/scripts/test_v850_release.sh" "$TARGET/deploy/contabo/upgrade_workbench_backend_v8_5_0_contabo.sh" "$TARGET/installers/apply_and_push_workbench_v8_5_0_macos.sh"
TEST_PYTHON="${SCWB_TEST_PYTHON:-}"
if [[ -z "$TEST_PYTHON" ]]; then
  if python3 - <<'PYCHECK' >/dev/null 2>&1
import fastapi, pytest, httpx2, pint, scipy, numpy, sympy
PYCHECK
  then TEST_PYTHON=python3
  else VENV="${TMPDIR:-/tmp}/scwb-v850-release-venv"; echo "=== BOOTSTRAPPING ISOLATED RELEASE TEST ENVIRONMENT ==="; rm -rf "$VENV"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install -U pip; "$VENV/bin/python" -m pip install -r "$TARGET/backend/requirements.txt"; TEST_PYTHON="$VENV/bin/python"; fi
fi
echo "=== VALIDATING RELEASE ==="; SCWB_TEST_PYTHON="$TEST_PYTHON" "$TARGET/scripts/test_v850_release.sh"
git add -A
if git diff --cached --quiet; then echo "No new changes to commit; v$VERSION patch may already be committed."; else git commit -m "Workbench v8.5.0 Research Timeline & Run History"; fi
echo "=== PUSHING $BRANCH ==="; git push "$REMOTE" "$BRANCH"
if git rev-parse "v$VERSION" >/dev/null 2>&1; then echo "Tag v$VERSION already exists locally."; else git tag -a "v$VERSION" -m "Workbench v$VERSION — Research Timeline & Run History"; fi
git push "$REMOTE" "v$VERSION"
[[ -z "$(git status --porcelain)" ]] || { git status --short; echo "ERROR: working tree is not clean" >&2; exit 1; }
echo "PASS: Workbench v$VERSION applied, validated, committed, pushed, and tagged."
