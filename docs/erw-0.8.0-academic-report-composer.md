# ERW 0.8.0 — Academic Report Composer

Developed on the production-certified ERW 0.7.0 branch. Generates a deterministic **unpublished structured JSON manuscript object**, not a verified scientific paper, rendered PDF, or outbound publication.

Contents: abstract, research context, methods, exploratory results, discussion and uncertainties, limitations, conclusions; five referenced figure specifications, four equation references, bibliography with evidence classification, and six-source reproducibility appendix. Checks expected object schemas, lineage references and integrity status. No external source fetch, independent hash verification, re-execution, PDF generation, automatic publication, or remote submission.

## Mac — test, then transfer only if tests pass
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.8.0-academic-report-composer
git switch feature/erw-0.8.0-academic-report-composer
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py backend/tests/test_erw_v070.py backend/tests/test_erw_v080.py
scp backend/app/erw_v080.py backend/tests/test_erw_v080.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backup, build and deploy
```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw080-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw070.yml "$BACKUP/"
cp /tmp/erw_v080.py backend/app/
cp /tmp/test_erw_v080.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py')
s=p.read_text()
code='\n# ERW 0.8.0 unpublished report composer\nfrom app.erw_v080 import router as erw_v080_router\napp.include_router(erw_v080_router)\n'
if 'from app.erw_v080 import router' not in s:p.write_text(s.rstrip()+code)
print('ERW 0.8 router registered')
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v080.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw080 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw080 -c 'from app.erw_v080 import status; print(status())'
cat > compose.erw080.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw080
EOF
docker compose -f compose.yml -f compose.erw080.yml config --quiet
docker compose -f compose.yml -f compose.erw080.yml up -d --no-build workbench
for i in $(seq 1 24); do s=$(docker inspect sc-workbench --format '{{.State.Health.Status}}'); echo "$s"; [ "$s" = healthy ] && break; [ "$s" = unhealthy ] && break; sleep 5; done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v0.8.0/status; echo
```

Rollback only if required:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw070.yml up -d --no-build --force-recreate workbench
```

Do not delete persistent database, merge draft PRs or assert certification before signed-session research project creation, seven-object persistence and research-package export pass on Contabo.
