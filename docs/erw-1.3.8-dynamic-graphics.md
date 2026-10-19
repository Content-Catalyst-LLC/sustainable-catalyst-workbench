# ERW v1.3.8 — Dynamic Scientific Graphics

**Development release; tests and deployment pending.** Built on the ERW 1.3.6 manuscript repair and style-engine branch. No destructive migrations, publication writes or stored object modifications.

## Scope
- Interactive 0/10/20 t/ha Wexford scenario *dimensionless illustrative index*, with adjustable dose (0–20 t/ha), year (0–10), and arbitrary response attenuation (0–100%). This is a visual demonstration **not a carbon-removal estimate**. A 0 t/ha control remains at 0 on this *project index*; it is **not** an assertion of zero natural weathering.
- Six-stage conceptual enhanced rock weathering pathway explicitly distinguishes dissolution, capture and durable storage. Each is an evidence requirement, not a measured removal claim.
- Export browser-rendered **SVG** diagrams and **CSV** illustrative series, with caveats. An optional manually entered source identifier is annotated *unverified*, NOT validated against the Source Library.
- Existing owner-scoped manuscript snapshots, independent source links, publication-readiness audit, legacy native DOCX/PDF exports and style engine remain unchanged.
- No claim of source-linked numeric series, Monte Carlo uncertainty, DOCX figure insertion, verified atmospheric carbon removal, or production publication readiness. Those require later development and review.

## Mac — tests first
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin feature/erw-1.3.8-dynamic-scientific-graphics
git switch feature/erw-1.3.8-dynamic-scientific-graphics
source .venv/bin/activate
python -m py_compile backend/app/erw_v138.py backend/tests/test_erw_v138.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py backend/tests/test_erw_style_engine.py
# Only when tests pass:
scp backend/app/erw_v138.py backend/tests/test_erw_v138.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backup, build and certify
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw138-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw136-styles.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v138.py backend/app/
cp /tmp/test_erw_v138.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.8 browser-only scientific visual exploration\nfrom app.erw_v138 import router as erw_v138_router\napp.include_router(erw_v138_router)\n"
if "from app.erw_v138 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.8 routes registered")
PY
python3 -m py_compile backend/app/erw_v138.py backend/app/main.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw138 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw138 -c 'from app.erw_v138 import build_page,status; assert "sc138plot" in build_page(); print(status())'
```

Only after smoke checks pass:
```bash
cat > compose.erw138.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw138
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw138.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw138.yml up -d --no-build workbench
for i in $(seq 1 24); do
  STATUS=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $STATUS"
  [ "$STATUS" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health;echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.8/status;echo
curl -sS -o /dev/null -w 'Graphic workspace HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.8/report
```

## Browser acceptance
Maintain SSH tunnel `ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77`. Open `http://127.0.0.1:18088/erw/v1.3.8/report`, authenticate, select Wexford project and inspect graphics. Change dose, year and attenuation; confirm chart updates; download and inspect SVG and CSV; verify warnings and no saved data mutation. Preserve all previous reports. The general /erw/report URL intentionally remains on the stable 1.3.6 editor.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136-styles.yml up -d --no-build --force-recreate workbench
```
Rollback needs an existing `compose.erw136-styles.yml` and its image. Do not delete `/data` or run docker prune.
