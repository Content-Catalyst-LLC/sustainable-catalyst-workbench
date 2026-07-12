#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V230="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v230-robotics-controls.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v230.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v230.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v230.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RV="$ROOT/runner-go/internal/runner/version.go"
for path in "$PLUGIN" "$V230" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RV"; do [[ -f "$path" ]] || { echo "Missing: $path"; exit 1; }; done
grep -q 'Version: 2.3.0' "$PLUGIN"
grep -q 'scwb-v230-robotics-controls.php' "$PLUGIN"
grep -q 'v230_router' "$BACKEND"
grep -q 'const Version = "2.3.0"' "$RV"
for marker in sc_workbench_robotics_studio sc_workbench_controls_studio sc_workbench_mechatronics_studio sc_workbench_actuator_studio sc_workbench_state_machine_studio sc_workbench_hil_validation; do grep -q "$marker" "$V230" || exit 1; done
for route in /robotics/kinematics /controls/simulate /mechatronics/review /actuators/size /state-machines/validate /hil/evaluate; do grep -q "$route" "$ROUTES" || exit 1; done
grep -q 'mux.HandleFunc("/robotics-tools"' "$RUNNER"
grep -q 'mux.HandleFunc("/robotics-task"' "$RUNNER"
if command -v php >/dev/null; then php -l "$PLUGIN" >/dev/null; php -l "$V230" >/dev/null; fi
if command -v node >/dev/null; then node --check "$JS"; fi
python3 -c 'from pathlib import Path; import sys; [compile(Path(f).read_text(), f, "exec") for f in sys.argv[1:]]' "$BACKEND" "$ROUTES"
if command -v go >/dev/null; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.3.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner robotics-tools >/dev/null)
fi
python3 -c 'from pathlib import Path; import re,sys; root=Path(sys.argv[1]); pats=[re.compile(r"AIza[0-9A-Za-z_-]{20,}"),re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY")]; bad=[str(p) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() not in {".zip",".png",".jpg",".pyc"} and any(x.search(p.read_text(errors="ignore")) for x in pats)]; (_ for _ in ()).throw(SystemExit("Potential secret in "+bad[0])) if bad else print("Push-safe secret scan passed.")' "$ROOT"
echo 'Workbench v2.3.0 release checks passed.'
