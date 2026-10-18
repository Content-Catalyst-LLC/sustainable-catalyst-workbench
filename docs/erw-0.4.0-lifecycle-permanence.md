# ERW 0.4.0 — Lifecycle Emissions and Carbon Permanence

**Research only. No verified durable CO2 removal.** Extends certified ERW 0.3.0 with a user-supplied lifecycle activity ledger and a provenance-preserving permanence evidence gap record, linked via source scenario hash. No estimation factors are fabricated and no measured field observations are implied.

## API

- GET /erw/v0.4.0/status
- POST /erw/v0.4.0/assess (stateless)
- POST /erw/v0.4.0/projects/assess (requires Workbench bearer session and owner-scoped ERW research project). Stored as an ordinary v1220 calculation and therefore appears in the existing v0.1 package export.

Required request fields: sourceScenarioCalculationHash; scenarioDoseTonnesPerHa; rockTonnes; theoreticalUpperBoundTonnesCO2; activities (array of category, unique activityId, quantity, unit, emissionsFactorKgCO2ePerUnit, factorUnit exactly kgCO2e/<unit>, evidenceClass, sourceReference, boundaryNote); permanence (pathway, status, sourceReference, four establishment flags); assessmentSourceReference. StudyYears defaults to 10. Numeric values are nonnegative finite decimal strings.

Activities can represent quarrying, crushing, processing, transport, spreading, monitoring or other burdens. Model returns tonnes CO2e per activity and category and combined ledger burden, using *quantity × factor / 1000*. The screening difference of theoretical upper-bound tCO2 minus modeled tCO2e burden is **not net removal** and is deliberately named so. Such subtraction omits weathering conversion, additionality, temporal boundaries and permanence. Input factor sources and system boundaries remain the researcher's responsibility.

The permanence evidence ledger records uncertainty about hydrological fate, secondary-mineral effects, strong-acid corrections and long-term retention. All flags, even all true, are insufficient to auto-certify storage. Always report netDurableAtmosphericRemoval:null, additionalityDemonstrated:false, verifiedDurableStorage:false.

## Mac test and file transfer

```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.4.0-lifecycle-permanence
git switch feature/erw-0.4.0-lifecycle-permanence
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py
scp backend/app/erw_v040.py backend/tests/test_erw_v040.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo deployment after Mac PASS

```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw040-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a compose.yml compose.erw030.yml backend "$BACKUP/"
cp /tmp/erw_v040.py backend/app/
cp /tmp/test_erw_v040.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
code='\n# ERW 0.4.0 lifecycle and permanence\nfrom app.erw_v040 import router as erw_v040_router\napp.include_router(erw_v040_router)\n'
if "from app.erw_v040 import router" not in s:
    p.write_text(s.rstrip()+code)
print("ERW 0.4.0 registration present")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v040.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw040 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw040 -c 'from app.erw_v040 import status; print(status())'
cat > compose.erw040.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw040
EOF
docker compose -f compose.yml -f compose.erw040.yml config --quiet
docker compose -f compose.yml -f compose.erw040.yml up -d --no-build workbench
```

Wait for the container to be healthy before running:
```bash
docker inspect sc-workbench --format '{{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health
curl -fsS http://127.0.0.1:8088/erw/v0.4.0/status
```

Rollback if needed: `docker compose -f compose.yml -f compose.erw030.yml up -d --no-build --force-recreate workbench`. Never delete /data. After health, run separately designed authenticated save/package smoke test before certification. Draft PR based on ERW 0.3.0, not main; reconcile parent PRs before standard release.
