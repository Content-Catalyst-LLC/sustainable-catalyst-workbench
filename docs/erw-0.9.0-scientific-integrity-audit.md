# ERW 0.9.0 — Scientific Integrity & Publication Audit

Internal checks for **six caller-supplied research objects + the ERW 0.8 academic report**. The audit checks object digests (using `content_hash`), reference matching, manuscript structure, limitations and user-declared claim-to-evidence traces. External source authenticity, physical site verification, scientific peer review, independent re-execution, verified CDR, publication and outbound submission **remain disabled/unverified**.

API:
- `GET /erw/v0.9.0/status`
- `POST /erw/v0.9.0/audit` stateless preview
- `POST /erw/v0.9.0/projects/audit` authenticated persistence

An audit marked `internalConsistency=pass-with-limitations` is **not a scientific certification**; `publicationReadiness` is always `not-ready` pending a distinct future process. Tests use synthetic fixtures; integration against real saved project objects remains a production acceptance gate.

## Mac — unit tests and transfer

```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.9.0-scientific-integrity-audit
git switch feature/erw-0.9.0-scientific-integrity-audit
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py backend/tests/test_erw_v070.py backend/tests/test_erw_v080.py backend/tests/test_erw_v090.py
# Only when tests pass:
scp backend/app/erw_v090.py backend/tests/test_erw_v090.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — safe deployment after successful Mac tests

```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw090-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw080-fixed.yml "$BACKUP/"
cp /tmp/erw_v090.py backend/app/
cp /tmp/test_erw_v090.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py')
s=p.read_text()
code='\n# ERW 0.9.0 scientific-integrity and publication audit\nfrom app.erw_v090 import router as erw_v090_router\napp.include_router(erw_v090_router)\n'
if 'from app.erw_v090 import router' not in s:p.write_text(s.rstrip()+code)
print('ERW 0.9.0 router registered')
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v090.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw090 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw090 -c 'from app.erw_v090 import status; print(status())'
cat > compose.erw090.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw090
EOF
docker compose -f compose.yml -f compose.erw090.yml config --quiet
docker compose -f compose.yml -f compose.erw090.yml up -d --no-build workbench
for i in $(seq 1 24); do
 STATUS=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
 echo "$STATUS"
 [ "$STATUS" = "healthy" ] && break
 [ "$STATUS" = "unhealthy" ] && break
 sleep 5
done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v0.9.0/status; echo
```

Rollback **only if needed**, without deleting persistent records:

```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw080-fixed.yml up -d --no-build --force-recreate workbench
```

Do not call 0.9 production-certified until authenticated eight-object save/export workflow passes on Contabo. Do not merge stacked draft PRs without explicit authorization.
