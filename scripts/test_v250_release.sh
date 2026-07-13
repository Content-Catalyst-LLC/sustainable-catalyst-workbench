#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V250="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v250-simulation-digital-twin.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v250.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v250.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v250.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RV="$ROOT/runner-go/internal/runner/version.go"
for path in "$PLUGIN" "$V250" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RV"; do
  [[ -f "$path" ]] || { echo "Missing: $path"; exit 1; }
done
grep -q 'Version: 2.5.0' "$PLUGIN"
grep -q 'scwb-v250-simulation-digital-twin.php' "$PLUGIN"
grep -q 'v250_router' "$BACKEND"
grep -q 'const Version = "2.5.0"' "$RV"
for marker in sc_workbench_simulation_studio sc_workbench_digital_twin sc_workbench_systems_modeling sc_workbench_scenario_sweep sc_workbench_monte_carlo sc_workbench_model_validation; do
  grep -q "$marker" "$V250" || exit 1
done
for route in /simulation/run /digital-twin/evaluate /systems/simulate /scenarios/sweep /monte-carlo/run /models/validate; do
  grep -q "$route" "$ROUTES" || exit 1
done
grep -q 'mux.HandleFunc("/simulation-tools"' "$RUNNER"
grep -q 'mux.HandleFunc("/simulation-task"' "$RUNNER"
if command -v php >/dev/null; then
  php -l "$PLUGIN" >/dev/null
  php -l "$V250" >/dev/null
fi
if command -v node >/dev/null; then node --check "$JS"; fi
python3 -c 'from pathlib import Path; import sys; [compile(Path(f).read_text(), f, "exec") for f in sys.argv[1:]]' "$BACKEND" "$ROUTES"
PYTHONPATH="$ROOT" python3 - <<'PY'
from backend.app.v250 import SimulationRequest, run_simulation, SystemsRequest, simulate_system, MonteCarloRequest, UncertainVariable, run_monte_carlo, ValidationRequest, validate_model
sim=run_simulation(SimulationRequest(model_type='first_order',initial_state=0,input_value=10,gain=2,time_constant=4,duration=40,time_step=.1))
assert sim['ok'] and abs(sim['metrics']['finalState']-20)<.01
system=simulate_system(SystemsRequest(matrix_a=[[-.2,0],[.1,-.3]],initial_state=[10,0],input_vector=[0,0],duration=2,time_step=.05))
assert system['ok'] and len(system['series'])==2
mc=run_monte_carlo(MonteCarloRequest(runs=1000,seed=42,variables=[UncertainVariable(name='x',mean=10,standard_deviation=1,minimum=5,maximum=15)],coefficients={'x':2},threshold=20))
assert mc['ok'] and mc['runs']==1000
val=validate_model(ValidationRequest(observed=[1,2,3,4],predicted=[1.01,1.98,3.02,3.99],maximum_rmse=.1,maximum_absolute_bias=.1,minimum_r2=.99,maximum_mape_percent=5))
assert val['ok']
print('v2.5.0 calculation checks passed.')
PY
if command -v go >/dev/null; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.5.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner simulation-tools >/dev/null)
fi
python3 -c 'from pathlib import Path; import re,sys; root=Path(sys.argv[1]); pats=[re.compile(r"AIza[0-9A-Za-z_-]{20,}"),re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY")]; bad=[str(p) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() not in {".zip",".png",".jpg",".pyc"} and any(x.search(p.read_text(errors="ignore")) for x in pats)]; (_ for _ in ()).throw(SystemExit("Potential secret in "+bad[0])) if bad else print("Push-safe secret scan passed.")' "$ROOT"
echo 'Workbench v2.5.0 release checks passed.'
