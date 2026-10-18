# ERW 0.7.0 — Equations, Maps & Scientific Diagrams

Built on ERW 0.6.0's certified declarative research visual objects.

Adds four symbolic equation specifications, an EPSG:4326 user-coordinate point-map specification, and a deterministic material-flow DAG. No external services, geocoding, raster tiles or map image generation. **Not a rendered graphic**: renderer integration is still required. Source visual hash equality is a caller assertion; 0.7 does not independently fetch and verify previous objects from persistence.

Safeguards: hypothetical or input-dependent spatial markers; no certified treatment site; net durable atmospheric removal is null and `verifiedCDR=false`.

## Mac test and transfer
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.7.0-equations-maps-diagrams
git switch feature/erw-0.7.0-equations-maps-diagrams
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py backend/tests/test_erw_v070.py
scp backend/app/erw_v070.py backend/tests/test_erw_v070.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo deployment after tests pass
```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw070-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw060.yml "$BACKUP/"
cp /tmp/erw_v070.py backend/app/
cp /tmp/test_erw_v070.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py')
s=p.read_text()
code='\n# ERW 0.7.0 equation/map/diagram representations\nfrom app.erw_v070 import router as erw_v070_router\napp.include_router(erw_v070_router)\n'
if 'from app.erw_v070 import router' not in s:p.write_text(s.rstrip()+code)
print('ERW 0.7.0 router registered')
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v070.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw070 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw070 -c 'from app.erw_v070 import status; print(status())'
cat > compose.erw070.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw070
EOF
docker compose -f compose.yml -f compose.erw070.yml config --quiet
docker compose -f compose.yml -f compose.erw070.yml up -d --no-build workbench
for i in $(seq 1 24); do s=$(docker inspect sc-workbench --format '{{.State.Health.Status}}'); echo "$s"; [ "$s" = healthy ] && break; sleep 5; done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v0.7.0/status; echo
```

For failures, rollback ONLY if needed: `docker compose -f compose.yml -f compose.erw060.yml up -d --no-build --force-recreate workbench`. Never delete persistent data. Production save/export certification remains a separate acceptance gate.
