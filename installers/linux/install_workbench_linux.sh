#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET="${SCWB_INSTALL_ROOT:-$HOME/.local/share/sustainable-catalyst-workbench}"
BIN_DIR="${SCWB_BIN_DIR:-$HOME/.local/bin}"
LAUNCHER="$BIN_DIR/sustainable-catalyst-workbench"
mkdir -p "$BIN_DIR"
"$ROOT/installers/common/install_workbench_common.sh" linux "$ROOT" "$TARGET" "$LAUNCHER"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/sustainable-catalyst-workbench.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sustainable Catalyst Workbench
Comment=Offline Sustainable Catalyst Workbench v4.4.0
Exec=$LAUNCHER
Terminal=true
Categories=Development;Science;Education;
EOF
chmod +x "$DESKTOP_DIR/sustainable-catalyst-workbench.desktop"
