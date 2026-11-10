# ERW 0.6.0 — Scientific Visualization

Built from the certified ERW 0.5.0 development branch. The API produces renderer-neutral, deterministic declarative objects for five exploratory scientific displays. It does **not** render PNG/SVG, perform external data fetches, prove source hash authenticity against persistence, measure carbon removal, or authorize credits.

## Graphs
1. Scenario trajectories — yearly baseline, scenario theoretical potential and incremental potential proxy for each application rate.
2. Lifecycle emissions — category-by-category modeled burdens, kgCO2e previously converted to tonnes CO2e.
3. Uncertainty intervals — deterministic low/central/high extrema, **not** statistical confidence intervals.
4. Sensitivity rankings — one-at-a-time absolute proxy swing, **not** causal attribution.
5. MRV evidence matrix — categorical status and evidence classes, **not** verified observation quality.

## Scientific gates
- Requires prior calculation objects with compatible schema, Wexford research ID and distinct hash references.
- Cross-checks references for string equality, not against persisted authoritative sources.
- Requires consecutive annual years; checks numeric finiteness, interval order and ledger sum.
- The model always reports `verifiedCDR=false`, `netDurableAtmosphericRemoval=null`, and `sourceIntegrityVerified=false`.
- Saves only under signed, owner-scoped ERW projects using existing v1220 persistence.

## Endpoints
- `GET /erw/v0.6.0/status`
- `POST /erw/v0.6.0/visualize`
- `POST /erw/v0.6.0/projects/visualize` (signed bearer token)

## Mac terminal
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.6.0-scientific-visualization
git switch feature/erw-0.6.0-scientific-visualization
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py
scp backend/app/erw_v060.py backend/tests/test_erw_v060.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo terminal — only after 66 tests PASS
```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw060-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a compose.yml compose.erw050.yml backend "$BACKUP/"
cp /tmp/erw_v060.py backend/app/
cp /tmp/test_erw_v060.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
code='\n# ERW 0.6.0 visual research objects\nfrom app.erw_v060 import router as erw_v060_router\napp.include_router(erw_v060_router)\n'
if "from app.erw_v060 import router" not in s:p.write_text(s.rstrip()+code)
print("ERW 0.6.0 registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v060.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw060 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw060 -c 'from app.erw_v060 import status; print(status())'
cat > compose.erw060.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw060
EOF
docker compose -f compose.yml -f compose.erw060.yml config --quiet
docker compose -f compose.yml -f compose.erw060.yml up -d --no-build workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/erw/v0.6.0/status
```

Only claim production certification after checking health and performing authenticated project save + package export. Rollback (ONLY if needed):
```bash
docker compose -f compose.yml -f compose.erw050.yml up -d --no-build --force-recreate workbench
```
Keep persistent `/data` untouched. PR is stacked upon ERW 0.5, not main.
