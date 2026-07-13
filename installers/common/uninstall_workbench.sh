#!/usr/bin/env bash
set -euo pipefail
TARGET="${SCWB_INSTALL_ROOT:-}"
[[ -n "$TARGET" ]] || { echo "Set SCWB_INSTALL_ROOT to the installation directory." >&2; exit 1; }
[[ -f "$TARGET/installation.json" ]] || { echo "Refusing to remove an unrecognized directory: $TARGET" >&2; exit 1; }
echo "Project data will be preserved at: $TARGET/data"
rm -rf "$TARGET/releases" "$TARGET/current"
echo "Workbench application files removed. Project data was not deleted."
