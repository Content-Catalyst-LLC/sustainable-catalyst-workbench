# ERW 0.5.0 — Uncertainty, Sensitivity & MRV Readiness

Derived from the ERW 0.4.0 lifecycle/permanence feature branch; preserves Workbench v14 and owner-scoped v1220 persistence. **Exploratory, not verified carbon removal.**

Four explicit low/central/high intervals: rock feedstock tonnes, theoretical capacity tCO2/t feedstock, modeled realization fraction between 0 and 1, lifecycle burden tCO2e. All finite, ordered, nonnegative. Deterministic extreme screening: gross capacity = mass × capacity; modeled proxy = gross × fraction; screening difference = modeled proxy − burden. No joint probability, dependency structure, Monte Carlo or measured field calibration; endpoints must NOT be described as confidence intervals or net CDR. One-at-a-time sensitivities vary each input holding others central; not a causal sensitivity measure.

Ten MRV requirements are represented as an evidence checklist with source, provenance and limitations: baseline control, feedstock assay, porewater, water flux, alkalinity, downstream fate, strong acid correction, lifecycle inventory, permanence and independent review. User-supplied statuses are descriptive, not independently validated by the API. Even an all-reviewed checklist remains NOT certified for crediting. Hashes from previous scenario/lifecycle outputs are supplied provenance references and are not cross-checked server-side in v0.5.0.

## Routes
- GET /erw/v0.5.0/status
- GET /erw/v0.5.0/mrv-requirements
- POST /erw/v0.5.0/analyze
- POST /erw/v0.5.0/projects/analyze (signed Workbench bearer token, owner-scoped ERW research project; saved into existing research package)

## Mac
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.5.0-uncertainty-mrv
git switch feature/erw-0.5.0-uncertainty-mrv
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py
scp backend/app/erw_v050.py backend/tests/test_erw_v050.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo (ONLY after 52 tests pass)
```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw050-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a compose.yml compose.erw040-fixed.yml backend "$BACKUP/"
cp /tmp/erw_v050.py backend/app/
cp /tmp/test_erw_v050.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
code='\n# ERW 0.5.0 uncertainty and MRV readiness\nfrom app.erw_v050 import router as erw_v050_router\napp.include_router(erw_v050_router)\n'
if "from app.erw_v050 import router" not in s:
    p.write_text(s.rstrip()+code)
print("ERW 0.5.0 router registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v050.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw050 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw050 -c 'from app.erw_v050 import status; print(status())'
cat > compose.erw050.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw050
EOF
docker compose -f compose.yml -f compose.erw050.yml config --quiet
docker compose -f compose.yml -f compose.erw050.yml up -d --no-build workbench
```

Wait until Docker container health is healthy, then check `curl -fsS http://127.0.0.1:8088/erw/v0.5.0/status`. Roll back if needed using `docker compose -f compose.yml -f compose.erw040-fixed.yml up -d --no-build --force-recreate workbench`. Do not remove /data. A further authenticated save/export API test must PASS before claiming production certification. Do not merge draft chain into main without separate reconciliation.
