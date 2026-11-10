# ERW 1.3.8.1 — Source-Linked Scientific Graphics

**Draft implementation: tests and Contabo deployment not yet executed.** Based on ERW 1.3.8 + PNG export. No data migrations and no source-object writes.

### Scope and limits
- Read-only, authenticated project-specific catalog of `sc.erw.visual-research-package.v0.6.0` saved research objects with consistent content hashes.
- Before displaying any chart, the API calls the existing `valid_source` integrity, project ownership, schema, research ID and non-verification checks. It rejects malformed points, negative/nonfinite values and nonsorted observation years.
- Chart values come **only** from the stored `scenario-trajectories` series `incrementalPotentialProxyTonnesCO2` and `rateTonnesPerHa`, never browser-derived index data.
- SVG and CSV outputs include the server-confirmed source hash and a prominent hypothetical/unverified notice.
- 1.3.8 dimensionless demonstration remains separate; no probabilistic uncertainty is invented, no automatic coupling into DOCX/PDF, and no claim of independently verified net durable atmospheric removal.
- The page inherits the 1.3.6 academic/institutional style export options, existing manuscript snapshots and audit. Native export routes remain unchanged.
- PNG export for the **new source-linked** chart is not included in this build; previous demonstration chart PNG export is unchanged. This is a deliberately isolated scientific-provenance increment.

### Mac test and transfer
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin feature/erw-1.3.8.1-source-linked-graphics
git switch feature/erw-1.3.8.1-source-linked-graphics
source .venv/bin/activate
python -m py_compile backend/app/erw_v1381_source.py backend/app/erw_v1381_ui.py backend/tests/test_erw_v1381.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py backend/tests/test_erw_style_engine.py
# Only after tests pass
scp backend/app/erw_v1381_source.py backend/app/erw_v1381_ui.py backend/tests/test_erw_v1381.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

### Contabo backup, backend-first build and smoke test
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw1381-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw138-png.yml compose.erw138.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v1381_source.py /tmp/erw_v1381_ui.py backend/app/
cp /tmp/test_erw_v1381.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.8.1 hash-verified saved source visualization\nfrom app.erw_v1381_source import router as erw_v1381_source_router\nfrom app.erw_v1381_ui import router as erw_v1381_ui_router\napp.include_router(erw_v1381_source_router)\napp.include_router(erw_v1381_ui_router)\n"
if "from app.erw_v1381_source import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.8.1 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v1381_source.py backend/app/erw_v1381_ui.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw1381 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw1381 -c 'from app.erw_v1381_ui import build_page; from app.erw_v1381_source import status; assert "sc1381chart" in build_page(); print(status())'
```

Only if smoke check passes:
```bash
cat > compose.erw1381.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw1381
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw1381.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw1381.yml up -d --no-build workbench
for i in $(seq 1 24); do
 STATUS=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
 echo "Health: $STATUS"
 [ "$STATUS" = healthy ] && break
 sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.8.1/status; echo
curl -sS -o /dev/null -w 'Page HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.8.1/report
```

### Browser acceptance
Tunnel from Mac `ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77`; open `http://127.0.0.1:18088/erw/v1.3.8.1/report`. Sign in, select Wexford project, and click **Load verified research objects**. Choose a saved ERW 0.6 visual research package, plot it, and download SVG/CSV. Confirm the chart is identical to its saved series, includes correct SHA-256, and warns the potential proxy is hypothetical and not verified atmospheric removal. If there are no qualifying saved objects, the empty catalog is a valid result; do not generate mock data or claim deployment failure.

### Rollback
If current production is `erw138-png`, preserve its Compose override and image:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw138-png.yml up -d --no-build --force-recreate workbench
```
If that is not the actual prior deployed image, use the *actual* backed-up Compose override. Never run destructive Docker pruning or remove /data.
