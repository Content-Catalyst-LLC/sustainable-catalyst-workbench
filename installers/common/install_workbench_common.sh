#!/usr/bin/env bash
set -euo pipefail

PLATFORM="${1:-}"
SOURCE_ROOT="${2:-}"
TARGET_ROOT="${3:-}"
LAUNCHER_PATH="${4:-}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ -n "$PLATFORM" ]] || fail "Platform is required."
[[ -d "$SOURCE_ROOT/backend/app" ]] || fail "Workbench source root is incomplete: $SOURCE_ROOT"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required."

PYTHON_VERSION="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
PY

VERSION="4.0.1"
APP_DIR="$TARGET_ROOT/releases/$VERSION"
CURRENT_LINK="$TARGET_ROOT/current"
DATA_DIR="$TARGET_ROOT/data"
BACKUP_DIR="$TARGET_ROOT/backups"
VENV_DIR="$APP_DIR/.venv"
WHEELHOUSE="$SOURCE_ROOT/offline/wheelhouse"

mkdir -p "$TARGET_ROOT/releases" "$DATA_DIR" "$BACKUP_DIR"
if [[ -e "$CURRENT_LINK" || -L "$CURRENT_LINK" ]]; then
  PREVIOUS="$(readlink "$CURRENT_LINK" 2>/dev/null || true)"
  printf '%s\n' "$PREVIOUS" > "$BACKUP_DIR/pre-v${VERSION}-current.txt"
fi

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
(
  cd "$SOURCE_ROOT"
  tar \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    -cf - .
) | (cd "$APP_DIR" && tar -xf -)

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip

if [[ "${SCWB_SKIP_DEP_INSTALL:-0}" == "1" ]]; then
  echo "Skipping Python dependency installation by request."
elif [[ -d "$WHEELHOUSE" ]] && find "$WHEELHOUSE" -type f | grep -q .; then
  "$VENV_DIR/bin/python" -m pip install \
    --no-index \
    --find-links "$WHEELHOUSE" \
    -r "$APP_DIR/offline/requirements.txt"
else
  "$VENV_DIR/bin/python" -m pip install -r "$APP_DIR/offline/requirements.txt"
fi

ln -sfn "$APP_DIR" "$CURRENT_LINK"

mkdir -p "$(dirname "$LAUNCHER_PATH")"
cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
APP="$CURRENT_LINK"
PYTHON="\$APP/.venv/bin/python"
[[ -x "\$PYTHON" ]] || { echo "Workbench runtime is unavailable: \$PYTHON" >&2; exit 1; }
exec "\$PYTHON" "\$APP/offline/start_local_workbench.py" "\$@"
EOF
chmod +x "$LAUNCHER_PATH"

cat > "$TARGET_ROOT/installation.json" <<EOF
{
  "schema": "sc-workbench-offline-installation/1.0",
  "version": "$VERSION",
  "platform": "$PLATFORM",
  "pythonVersion": "$PYTHON_VERSION",
  "appDirectory": "$APP_DIR",
  "currentLink": "$CURRENT_LINK",
  "dataDirectory": "$DATA_DIR",
  "launcher": "$LAUNCHER_PATH",
  "localHost": "127.0.0.1",
  "localPort": 8787,
  "renderRequired": false,
  "paidServiceRequired": false
}
EOF

"$VENV_DIR/bin/python" -m py_compile \
  "$APP_DIR/offline/start_local_workbench.py" \
  "$APP_DIR/backend/app/v380.py" \
  "$APP_DIR/backend/app/v390.py" \
  "$APP_DIR/backend/app/v400.py" \
  "$APP_DIR/backend/app/v401.py"

echo
echo "Sustainable Catalyst Workbench v4.0.1 installed."
echo "Platform: $PLATFORM"
echo "Location: $APP_DIR"
echo "Launcher: $LAUNCHER_PATH"
echo "Local URL: http://127.0.0.1:8787/offline/"
