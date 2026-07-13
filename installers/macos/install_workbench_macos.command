#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET="${SCWB_INSTALL_ROOT:-$HOME/Library/Application Support/Sustainable Catalyst Workbench}"
LAUNCHER="${SCWB_LAUNCHER_PATH:-$HOME/Applications/Sustainable Catalyst Workbench.command}"
exec "$ROOT/installers/common/install_workbench_common.sh" macos "$ROOT" "$TARGET" "$LAUNCHER"
