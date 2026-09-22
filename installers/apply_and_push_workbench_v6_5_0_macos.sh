#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="6.5.0"
TARGET="${1:-$HOME/Downloads/sustainable-catalyst-workbench}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "${SCWB_PATCH_DIR:-}" ]]; then
  PATCH_DIR="$SCWB_PATCH_DIR"
elif [[ -d "$SCRIPT_DIR/patch" ]]; then
  PATCH_DIR="$SCRIPT_DIR/patch"
else
  PATCH_DIR="$SCRIPT_DIR/../patch"
fi
REMOTE="${SCWB_GIT_REMOTE:-origin}"
BRANCH="${SCWB_GIT_BRANCH:-main}"

fail(){ echo "ERROR: $*" >&2; exit 1; }
command -v git >/dev/null || fail "git is required"
command -v rsync >/dev/null || fail "rsync is required"
[[ -d "$TARGET/.git" ]] || fail "Git repository not found: $TARGET"
[[ -d "$PATCH_DIR/backend" ]] || fail "Patch payload is incomplete: $PATCH_DIR"

DIRTY="$(git -C "$TARGET" status --porcelain)"
RESUME=0
if [[ -n "$DIRTY" ]]; then
  if [[ -f "$TARGET/backend/app/release.py" ]] \
     && grep -q 'APP_VERSION = "6.5.0"' "$TARGET/backend/app/release.py" \
     && [[ -f "$TARGET/backend/app/v650.py" ]] \
     && [[ -f "$TARGET/scripts/test_v650_release.sh" ]]; then
    RESUME=1
    echo "=== RESUMING PARTIALLY APPLIED WORKBENCH v$VERSION ==="
  elif [[ "${SCWB_ALLOW_DIRTY:-0}" == "1" ]]; then
    RESUME=1
    echo "=== DIRTY TREE OVERRIDE ENABLED ==="
  else
    fail "Target repository has unrelated uncommitted changes. Commit/stash them first, or set SCWB_ALLOW_DIRTY=1 intentionally."
  fi
fi

if [[ "$RESUME" == "0" ]]; then
  echo "=== SYNCHRONIZING $BRANCH ==="
  git -C "$TARGET" checkout "$BRANCH"
  git -C "$TARGET" pull --ff-only "$REMOTE" "$BRANCH"
else
  CURRENT_BRANCH="$(git -C "$TARGET" branch --show-current)"
  [[ "$CURRENT_BRANCH" == "$BRANCH" ]] || fail "Resume requires branch '$BRANCH' (current: '$CURRENT_BRANCH')"
fi

echo "=== APPLYING WORKBENCH v$VERSION ==="
rsync -a "$PATCH_DIR/" "$TARGET/"
chmod +x \
  "$TARGET/scripts/test_v650_release.sh" \
  "$TARGET/deploy/contabo/upgrade_workbench_backend_v6_5_0_contabo.sh"

TEST_PYTHON="${SCWB_TEST_PYTHON:-python3}"
VENV_DIR="${TMPDIR:-/tmp}/scwb-v650-release-venv"
check_test_python() {
  "$1" - <<'PY' >/dev/null 2>&1
import fastapi, pydantic, pytest, httpx2
from fastapi.testclient import TestClient
PY
}
if ! check_test_python "$TEST_PYTHON"; then
  if [[ -x "$VENV_DIR/bin/python" ]] && check_test_python "$VENV_DIR/bin/python"; then
    echo "=== REUSING ISOLATED RELEASE TEST ENVIRONMENT ==="
    TEST_PYTHON="$VENV_DIR/bin/python"
  else
    echo "=== BOOTSTRAPPING ISOLATED RELEASE TEST ENVIRONMENT ==="
    command -v python3 >/dev/null || fail "python3 is required"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install -r "$TARGET/backend/requirements.txt"
    TEST_PYTHON="$VENV_DIR/bin/python"
  fi
fi

echo "=== VALIDATING RELEASE ==="
SCWB_TEST_PYTHON="$TEST_PYTHON" "$TARGET/scripts/test_v650_release.sh"

echo "=== COMMITTING RELEASE ==="
git -C "$TARGET" add \
  README.md \
  RELEASE_NOTES_6.5.0_UNIFIED_RUNTIME_CONTRACT_ADAPTER.md \
  WORKBENCH_V650_TERMINAL_COMMANDS.txt \
  BUILD_VALIDATION_6.5.0.txt \
  workbench-v6.5.0.env.example \
  compose.yml \
  backend/requirements.txt \
  backend/app/main.py backend/app/release.py backend/app/v640.py backend/app/v650.py \
  backend/tests/test_platform_core_connectivity_v640.py backend/tests/test_unified_runtime_contract_adapter_v650.py \
  deploy/contabo/upgrade_workbench_backend_v6_5_0_contabo.sh \
  docs/V650_UNIFIED_RUNTIME_CONTRACT_ADAPTER.md docs/V650_CORE_RUNTIME_ADAPTER_SECURITY.md \
  scripts/test_v650_release.sh \
  tests/test_v540_static.py tests/test_v550_static.py tests/test_v560_static.py tests/test_v570_static.py \
  tests/test_v580_static.py tests/test_v590_static.py tests/test_v600_static.py tests/test_v601_static.py \
  tests/test_v640_static.py tests/test_v650_static.py \
  wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php \
  wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v650-unified-runtime-contract-adapter.php \
  installers/apply_and_push_workbench_v6_5_0_macos.sh

if git -C "$TARGET" diff --cached --quiet; then
  echo "No new changes to commit; v$VERSION patch may already be committed."
else
  git -C "$TARGET" commit -m "Workbench v6.5.0 unified runtime contract adapter"
fi

echo "=== PUSHING $BRANCH ==="
git -C "$TARGET" push "$REMOTE" "$BRANCH"

if git -C "$TARGET" rev-parse "v$VERSION" >/dev/null 2>&1; then
  echo "Tag v$VERSION already exists; leaving it unchanged."
else
  git -C "$TARGET" tag -a "v$VERSION" -m "Workbench v$VERSION — Unified Runtime Contract Adapter"
fi
git -C "$TARGET" push "$REMOTE" "v$VERSION"

echo "PASS: Workbench v$VERSION applied, validated, committed, pushed, and tagged."
