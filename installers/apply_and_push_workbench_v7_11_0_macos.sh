#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.11.0"; BRANCH="${SCWB_BRANCH:-main}"; REMOTE="${SCWB_REMOTE:-origin}"; TARGET="${1:-$HOME/Downloads/sustainable-catalyst-workbench}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PAYLOAD="$PATCH_DIR/payload"
if [[ ! -d "$PAYLOAD" ]]; then PAYLOAD="$(cd "$PATCH_DIR/.." && pwd)"; fi
[[ -d "$TARGET/.git" ]] || { echo "ERROR: target is not a Git repository: $TARGET" >&2; exit 1; }
[[ -d "$PAYLOAD" ]] || { echo "ERROR: payload directory missing: $PAYLOAD" >&2; exit 1; }
cd "$TARGET"
if [[ -f "$TARGET/backend/app/release.py" ]] && grep -q 'APP_VERSION = "7.11.0"' "$TARGET/backend/app/release.py" && [[ -f "$TARGET/backend/app/v7110.py" ]] && [[ -f "$TARGET/scripts/test_v7110_release.sh" ]]; then echo "=== RESUMING PARTIALLY APPLIED WORKBENCH v$VERSION ==="
else echo "=== SYNCHRONIZING $BRANCH ==="; git switch "$BRANCH"; git pull --ff-only "$REMOTE" "$BRANCH"; fi
echo "=== APPLYING WORKBENCH v$VERSION ==="; rsync -a --exclude='.git/' "$PAYLOAD/" "$TARGET/"
chmod +x "$TARGET/scripts/test_v7110_release.sh" "$TARGET/deploy/contabo/upgrade_workbench_backend_v7_11_0_contabo.sh" "$TARGET/installers/apply_and_push_workbench_v7_11_0_macos.sh"
TEST_PYTHON="${SCWB_TEST_PYTHON:-}"
if [[ -z "$TEST_PYTHON" ]]; then
  if python3 - <<'PYCHECK' >/dev/null 2>&1
import fastapi, pytest, httpx2, pint, scipy, numpy, sympy
PYCHECK
  then TEST_PYTHON=python3
  else VENV="${TMPDIR:-/tmp}/scwb-v7110-release-venv"; echo "=== BOOTSTRAPPING ISOLATED RELEASE TEST ENVIRONMENT ==="; rm -rf "$VENV"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install -U pip; "$VENV/bin/python" -m pip install -r "$TARGET/backend/requirements.txt"; TEST_PYTHON="$VENV/bin/python"; fi
fi
echo "=== VALIDATING RELEASE ==="; SCWB_TEST_PYTHON="$TEST_PYTHON" "$TARGET/scripts/test_v7110_release.sh"
git add -A
if git diff --cached --quiet; then echo "No new changes to commit; v$VERSION patch may already be committed."; else git commit -m "Workbench v7.11.0 Visual Scientific Computing Workspace"; fi
echo "=== PUSHING $BRANCH ==="; git push "$REMOTE" "$BRANCH"
if git rev-parse "v$VERSION" >/dev/null 2>&1; then echo "Tag v$VERSION already exists locally."; else git tag -a "v$VERSION" -m "Workbench v$VERSION — Visual Scientific Computing Workspace"; fi
git push "$REMOTE" "v$VERSION"
[[ -z "$(git status --porcelain)" ]] || { git status --short; echo "ERROR: working tree is not clean" >&2; exit 1; }
echo "PASS: Workbench v$VERSION applied, validated, committed, pushed, and tagged."
