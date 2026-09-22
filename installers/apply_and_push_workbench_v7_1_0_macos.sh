#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.1.0"
TARGET="${1:-$HOME/Downloads/sustainable-catalyst-workbench}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "${SCWB_PATCH_DIR:-}" ]]; then PATCH_DIR="$SCWB_PATCH_DIR"; elif [[ -d "$SCRIPT_DIR/patch" ]]; then PATCH_DIR="$SCRIPT_DIR/patch"; else PATCH_DIR="$SCRIPT_DIR/../patch"; fi
REMOTE="${SCWB_GIT_REMOTE:-origin}"
BRANCH="${SCWB_GIT_BRANCH:-main}"
fail(){ echo "ERROR: $*" >&2; exit 1; }
command -v git >/dev/null || fail "git is required"
command -v rsync >/dev/null || fail "rsync is required"
[[ -d "$TARGET/.git" ]] || fail "Git repository not found: $TARGET"
[[ -d "$PATCH_DIR/backend" ]] || fail "Patch payload is incomplete: $PATCH_DIR"
DIRTY="$(git -C "$TARGET" status --porcelain)"; RESUME=0
if [[ -n "$DIRTY" ]]; then
 if [[ -f "$TARGET/backend/app/release.py" ]] && grep -q 'APP_VERSION = "7.1.0"' "$TARGET/backend/app/release.py" && [[ -f "$TARGET/backend/app/v710.py" ]] && [[ -f "$TARGET/scripts/test_v710_release.sh" ]]; then RESUME=1; echo "=== RESUMING PARTIALLY APPLIED WORKBENCH v$VERSION ==="
 elif [[ "${SCWB_ALLOW_DIRTY:-0}" == "1" ]]; then RESUME=1; echo "=== DIRTY TREE OVERRIDE ENABLED ==="
 else fail "Target repository has unrelated uncommitted changes. Commit/stash them first, or set SCWB_ALLOW_DIRTY=1 intentionally."; fi
fi
if [[ "$RESUME" == "0" ]]; then
 echo "=== SYNCHRONIZING $BRANCH ==="; git -C "$TARGET" checkout "$BRANCH"; git -C "$TARGET" pull --ff-only "$REMOTE" "$BRANCH"
else
 CURRENT_BRANCH="$(git -C "$TARGET" branch --show-current)"; [[ "$CURRENT_BRANCH" == "$BRANCH" ]] || fail "Resume requires branch '$BRANCH' (current: '$CURRENT_BRANCH')"
fi
echo "=== APPLYING WORKBENCH v$VERSION ==="
rsync -a "$PATCH_DIR/" "$TARGET/"
chmod +x "$TARGET/scripts/test_v710_release.sh" "$TARGET/deploy/contabo/upgrade_workbench_backend_v7_1_0_contabo.sh" "$TARGET/installers/apply_and_push_workbench_v7_1_0_macos.sh"
TEST_PYTHON="${SCWB_TEST_PYTHON:-python3}"; VENV_DIR="${TMPDIR:-/tmp}/scwb-v710-release-venv"
check_test_python(){ "$1" - <<'PYCHK' >/dev/null 2>&1
import fastapi,pydantic,pytest,httpx2,numpy,scipy,sympy,pint
from fastapi.testclient import TestClient
PYCHK
}
if ! check_test_python "$TEST_PYTHON"; then
 if [[ -x "$VENV_DIR/bin/python" ]] && check_test_python "$VENV_DIR/bin/python"; then echo "=== REUSING ISOLATED RELEASE TEST ENVIRONMENT ==="; TEST_PYTHON="$VENV_DIR/bin/python"
 else echo "=== BOOTSTRAPPING ISOLATED RELEASE TEST ENVIRONMENT ==="; command -v python3 >/dev/null || fail "python3 is required"; rm -rf "$VENV_DIR"; python3 -m venv "$VENV_DIR"; "$VENV_DIR/bin/python" -m pip install --upgrade pip; "$VENV_DIR/bin/python" -m pip install -r "$TARGET/backend/requirements.txt"; TEST_PYTHON="$VENV_DIR/bin/python"; fi
fi
echo "=== VALIDATING RELEASE ==="
SCWB_TEST_PYTHON="$TEST_PYTHON" "$TARGET/scripts/test_v710_release.sh"
echo "=== COMMITTING RELEASE ==="
while IFS= read -r rel; do git -C "$TARGET" add -- "$rel"; done < <(cd "$PATCH_DIR" && find . -type f -print | sed 's#^./##' | sort)
if git -C "$TARGET" diff --cached --quiet; then echo "No new changes to commit; v$VERSION patch may already be committed."; else git -C "$TARGET" commit -m "Workbench v7.1.0 Unified Execution Object Model"; fi
echo "=== PUSHING $BRANCH ==="; git -C "$TARGET" push "$REMOTE" "$BRANCH"
if git -C "$TARGET" rev-parse "v$VERSION" >/dev/null 2>&1; then echo "Tag v$VERSION already exists; leaving it unchanged."; else git -C "$TARGET" tag -a "v$VERSION" -m "Workbench v$VERSION — Unified Execution Object Model"; fi
git -C "$TARGET" push "$REMOTE" "v$VERSION"
echo "PASS: Workbench v$VERSION applied, validated, committed, pushed, and tagged."
