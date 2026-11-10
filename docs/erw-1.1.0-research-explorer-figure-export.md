# ERW 1.1.0 — Research Explorer & Scientific Figure Export

Private FastAPI-hosted research explorer at `/erw/v1.1.0/explorer`, with:
- owner-scoped ERW project listing and figure object browsing using existing v12.2 signed-session persistence;
- visual types from saved ERW v0.6 (scenario trajectories, MRV matrix, lifecycle bar chart) and v0.7 (model equation cards, optional generic conceptual carbon pathway);
- deterministic client-side SVG export for insertion into Word; provenance warning and saved-object content-hash check.

**Scope limitations:** Browser accesses only research objects belonging to the provided Workbench signed-session token. Historical test projects created under separate session subjects are *not* transferred or visible. This is not yet a WordPress shortcode or integrated SSO login; the browser needs a valid Workbench bearer token and must be opened through the same backend origin (or trusted proxy) as the API. Equation cards render existing LaTeX strings as literal text, *not* MathJax typesetting. Carbon pathway is a generic explanatory illustration, not automatically generated field chemistry or evidence. PNG and PDF export are not part of this release. No external JS/CDN or external API use; only local browser SVG rendering. Scientific source validity is not independently checked. Publication and outbound submission remain disabled.

## Mac regression suite

```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.1.0-research-explorer-figure-export
git switch feature/erw-1.1.0-research-explorer-figure-export
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v0*.py backend/tests/test_erw_v100.py backend/tests/test_erw_v110.py
# Only if tests pass:
scp backend/app/erw_v110.py backend/tests/test_erw_v110.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo backend deployment

```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw110-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw100.yml "$BACKUP/"
cp /tmp/erw_v110.py backend/app/
cp /tmp/test_erw_v110.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
code='\n# ERW 1.1.0 authenticated research explorer and SVG export\nfrom app.erw_v110 import router as erw_v110_router\napp.include_router(erw_v110_router)\n'
if 'from app.erw_v110 import router' not in s:p.write_text(s.rstrip()+code)
print("ERW 1.1.0 router registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v110.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw110 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw110 -c 'from app.erw_v110 import status; print(status())'
cat > compose.erw110.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw110
EOF
docker compose -f compose.yml -f compose.erw110.yml config --quiet
docker compose -f compose.yml -f compose.erw110.yml up -d --no-build workbench
for i in $(seq 1 24); do
  H=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "$H"
  [ "$H" = healthy ] && break
  [ "$H" = unhealthy ] && break
  sleep 5
done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.1.0/status; echo
curl -fsSI http://127.0.0.1:8088/erw/v1.1.0/explorer
```

For local-only browser inspection (avoid exposing signed tokens to third-party sites), from your Mac create a tunnel:

```bash
ssh -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77
# Keep tunnel open, visit http://127.0.0.1:18088/erw/v1.1.0/explorer
```

Browser's bearer-token box requires a signed Workbench v12.1 session token. Do not paste a WordPress password, GitHub token, or server credentials. The old production certification scripts created identities that may not be recoverable after they exit; start a new research project under your own signed session if no old studies appear.

**Acceptance gates:** unit suite passes; nine previously certified ERW routers remain available; signed-session project listing returns only current owner's studies; cross-project object fetch fails; tampered stored object is rejected; SVG export renders and opens in Word; unauthenticated API access denied. If an old study belongs to another subject, treat it as an ownership boundary, not a broken index.

Rollback without deleting the database:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw100.yml up -d --no-build --force-recreate workbench
```

Draft PR remains unmerged until explicit instruction.
