# Sustainable Catalyst Scientific Publication Style Engine

Development add-on to ERW 1.3.6. Branch `feature/erw-1.3.6-style-engine`. **Pending local tests and Contabo deployment.**

## Supported presets
- **Modern Academic (default):** Cambria requested in editable DOCX, 11 pt, 1.5 spacing, A4, 25 mm margins, black headings.
- **Sustainable Catalyst Institutional:** Modern serif body, modest maroon heading accent, branded research report header/title treatment, A4, 25 mm margins.
- **Classic Academic:** switchable Times New Roman with optional 12 pt, double spacing, adjustable margins.

All presets are customizable at export (font choice, 10–12 pt size, 1–2 line spacing, 20–35 mm margins, optional section numbering). Saved reports are immutable; style changes do **not** alter existing research calculations or sources. New authenticated POST endpoints generate actual DOCX and PDF files; old v1.3.4 native export endpoints remain available. These are draft report styles, NOT verified publication layouts or a claim of UCD compliance.

**Font limitation:** The Docker PDF environment may not have Cambria. A compatible serif fallback is used, possibly Times-Roman, Liberation Serif or DejaVu Serif. Word specifies Cambria but the receiving computer must have that font for exact appearance. Native PDF/Word outputs require visual comparison and Harvard bibliography review. Mathematical expressions still use source notation, some charts may not render, and scientific verification remains false.

## Mac terminal (test first)
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin feature/erw-1.3.6-style-engine
git switch feature/erw-1.3.6-style-engine
source .venv/bin/activate
python -m py_compile backend/app/erw_style_engine.py backend/app/erw_style_ui.py backend/tests/test_erw_style_engine.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py backend/tests/test_erw_style_engine.py
# After all tests pass:
scp backend/app/erw_style_engine.py backend/app/erw_style_ui.py backend/tests/test_erw_style_engine.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo terminal (preserve 1.3.6 bibliography-fix baseline)
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-style-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw136-bibfix.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_style_engine.py /tmp/erw_style_ui.py backend/app/
cp /tmp/test_erw_style_engine.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# Configurable academic and institutional document styling\nfrom app.erw_style_engine import router as erw_style_router\nfrom app.erw_style_ui import router as erw_style_ui_router\napp.include_router(erw_style_router)\napp.include_router(erw_style_ui_router)\n"
if "from app.erw_style_engine import router" not in s:p.write_text(s.rstrip()+reg)
print("Document style engine routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_style_engine.py backend/app/erw_style_ui.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw136-styles -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw136-styles -c 'from app.erw_style_ui import build_page; from app.erw_style_engine import status; assert "style-preset" in build_page(); print(status())'
```

After all checks pass:
```bash
cat > compose.erw136-styles.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw136-styles
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136-styles.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136-styles.yml up -d --no-build workbench
for i in $(seq 1 24); do
  status=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "$status"
  [ "$status" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.6/styles/status; echo
curl -s -o /dev/null -w 'Styled page HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.6/styled-report
```

## Browser acceptance
The style controls appear at `http://127.0.0.1:18088/erw/v1.3.6/styled-report` via the existing SSH tunnel. Sign in; select your Wexford project and saved manuscript snapshot in **Native research report exports**. Choose Modern Academic or Sustainable Catalyst Institutional. Download styled Word and PDF, compare page margins, headings, fonts, line spacing, scientific objects, page breaks and bibliography. The permanent `/erw/report` route still points to the original v1.3.6 editor so no legacy link changes unexpectedly.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136-bibfix.yml up -d --no-build --force-recreate workbench
```
Leave `/data` and all saved Word/PDF source files untouched.
