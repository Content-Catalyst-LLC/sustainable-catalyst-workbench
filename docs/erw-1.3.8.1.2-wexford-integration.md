# ERW 1.3.8.1.2 — Wexford Scenario Model & Visualization Integration

**Development build. Do not call production-certified until real Wexford browser acceptance passes.** Base: 1.3.8.1.1. No schema migrations, deletion, publication, carbon-credit issuance or unsafe data changes.

## Model and research interpretation
The researcher supplies area (default 100 ha), unique rates including 0 (default 0/10/20 t/ha), potential yield factor (default 0.15 tCO₂ / tonne basalt), annual realization fraction (0.10), attenuation (0.05), study horizon (10 years) and a required assumptions note. **Every default coefficient is illustrative and unvalidated, not an Irish soil measurement or cited estimate.**

The intentionally simplified annual potential proxy is:

`area_ha × dose_t_ha × assumed_yield × assumed_annual_fraction × (1 − assumed_attenuation)^(year−1)`

This assumes a hypothetical treatment mass and simplistic attenuation; it is **not** validated geochemistry, emissions life-cycle accounting, net atmospheric removal, additionality, downstream fate or a certified removal model. The modeled zero-dose control is zero *incremental modeled application proxy*, not zero natural weathering. All saved objects set `verifiedCDR=false`, `netDurableAtmosphericRemoval=null`, `publicationEnabled=false` and `sourceIntegrityVerifiedExternally=false`.

### New workflow
- Open `/erw/v1.3.8.1.2/report` in the existing authenticated tunnel and choose Wexford.
- **Preview source-derived model** calculates values server-side, but does not write anything.
- Review assumptions and plotted annual scenario lines, then **Save immutable scenario package** *only if desired*. This is an explicit user-authorized write; previous 19 source objects are not overwritten.
- **Load previously saved model packages** then select a generated package and **Display saved model package**. This requires an owner-scoped saved object and hash verification.
- Export SVG, 300-DPI-equivalent PNG or CSV. Figures visibly say *hypothetical* and *NOT verified CDR*.
- Older stacked prototype panels are hidden on this route only. Historical route names remain working.
- Scientific assumptions do not come from uploaded manuscript values unless deliberately entered by the researcher; nothing is quietly inferred.

## Mac: obtain and test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin feature/erw-1.3.8.1.2-wexford-scenario-integration
git switch feature/erw-1.3.8.1.2-wexford-scenario-integration
source .venv/bin/activate
python -m py_compile backend/app/erw_v13812_model.py backend/app/erw_v13812_ui.py backend/tests/test_erw_v13812.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py backend/tests/test_erw_style_engine.py
```
Do not stash/reset/delete unrelated untracked local files. Investigate failed tests before uploading.

After tests PASS:
```bash
scp backend/app/erw_v13812_model.py backend/app/erw_v13812_ui.py backend/tests/test_erw_v13812.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo: backup, backend build, smoke and switch
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw13812-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw13811.yml compose.erw1381.yml; do [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"; done
cp /tmp/erw_v13812_model.py /tmp/erw_v13812_ui.py backend/app/
cp /tmp/test_erw_v13812.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py");s=p.read_text()
reg="\n# ERW 1.3.8.1.2 Wexford scenario modeling and integrated graphics\nfrom app.erw_v13812_model import router as erw_v13812_model_router\nfrom app.erw_v13812_ui import router as erw_v13812_ui_router\napp.include_router(erw_v13812_model_router)\napp.include_router(erw_v13812_ui_router)\n"
if "from app.erw_v13812_model import router" not in s:p.write_text(s.rstrip()+reg)
print("1.3.8.1.2 routes installed")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v13812_model.py backend/app/erw_v13812_ui.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw13812 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw13812 -c 'from app.erw_v13812_ui import build_page; from app.erw_v13812_model import calculate,ScenarioParameters; assert "msave" in build_page(); x=calculate(ScenarioParameters(assumptionNote="Illustrative only; no field calibration"),"wexford"); print(x["calculationObjectHash"],x["verifiedCDR"])'
```

Only after successful smoke:
```bash
cat > compose.erw13812.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw13812
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw13812.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw13812.yml up -d --no-build workbench
for i in $(seq 1 24); do state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}'); echo "$state"; [ "$state" = healthy ] && break; sleep 5; done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.8.1.2/status; echo
curl -sS -o /dev/null -w 'Workspace HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.8.1.2/report
```

## Acceptance on real saved project
Open the Mac tunnel `ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77` if needed; browser `http://127.0.0.1:18088/erw/v1.3.8.1.2/report`. Authenticate and select Wexford project `baf85d6f-8821-451f-87f6-5a90ccfd5f56`. Check: (1) preview renders 0/10/20 curves and source hash, no saved write; (2) Save creates a new immutable visual research package and does not alter existing 19 objects; (3) Refresh lists the saved package; (4) reload renders identical points/hash; (5) SVG, PNG, CSV download and retain warnings; (6) old manuscript and styled DOCX/PDF routes still function. Record acceptance logs. If any stage fails, *do not claim success*.

## Rollback
Use the **actual** previous Compose override and tag. Example if previously healthy 1.3.8.1.1:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw13811.yml up -d --no-build --force-recreate workbench
```
Never delete `/data`, reset projects or use Docker volume prune.
