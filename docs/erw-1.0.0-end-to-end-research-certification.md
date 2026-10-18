# ERW 1.0.0 — End-to-End Research Certification

**Scope:** Deterministic internal certification manifest over eight previously saved ERW research objects (geochemistry, scenario, lifecycle, uncertainty, visualization, diagrams, unpublished academic report, internal scientific audit). The ninth object is the certification manifest. Source schemas, content digests, report/audit lineage, publication controls, claims references and internal consistency are gated.

**Important:** This is software/research-package integrity certification, not field verification, peer review, independently verified net carbon removal, publication permission, or a crediting methodology. `productionPersistenceCertified` and `researchPackageExportCertified` remain `false` *inside the manifest* even after a successful external acceptance test; these require a separate test-run record. No public communications.

API routes:
- `GET /erw/v1.0.0/status`
- `POST /erw/v1.0.0/certify` preview
- `POST /erw/v1.0.0/projects/certify` owner-scoped authenticated persistence. Rejects manifests with failed gates.

## Mac verification

```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.0.0-end-to-end-research-certification
git switch feature/erw-1.0.0-end-to-end-research-certification
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py backend/tests/test_erw_v070.py backend/tests/test_erw_v080.py backend/tests/test_erw_v090.py backend/tests/test_erw_v100.py
# Only after tests pass:
scp backend/app/erw_v100.py backend/tests/test_erw_v100.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo deployment (after successful tests)

```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw100-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw090.yml "$BACKUP/"
cp /tmp/erw_v100.py backend/app/
cp /tmp/test_erw_v100.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py");s=p.read_text()
code='\n# ERW 1.0.0 end-to-end research certification manifest\nfrom app.erw_v100 import router as erw_v100_router\napp.include_router(erw_v100_router)\n'
if "from app.erw_v100 import router" not in s:p.write_text(s.rstrip()+code)
print("ERW 1.0.0 router registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v100.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw100 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw100 -c 'from app.erw_v100 import status;print(status())'
cat > compose.erw100.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw100
EOF
docker compose -f compose.yml -f compose.erw100.yml config --quiet
docker compose -f compose.yml -f compose.erw100.yml up -d --no-build workbench
for i in $(seq 1 24); do
  HEALTH=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "$HEALTH"
  [ "$HEALTH" = healthy ] && break
  [ "$HEALTH" = unhealthy ] && break
  sleep 5
done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.0.0/status; echo
```

## Rollback (if needed)
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw090.yml up -d --no-build --force-recreate workbench
```

## Production certification to perform *after* deployment

Obtain a signed session. Create a fresh hypothetical ERW project. Persist the eight v0.2–v0.9 calculation objects using authenticated project endpoints. Submit these eight objects to `POST /erw/v1.0.0/projects/certify`. Verify the saved manifest contains zero failed gates and has a deterministic hash, then export the research package with **nine saved objects** and verify its package digest. Reject missing or mutated objects and verify the publication controls. The result is a **software acceptance** result only. A separate production certification script/test run is required; the development PR alone is not production certification.

Do not merge the stacked draft PRs without explicit authorization, restart OS, or enable publications.
