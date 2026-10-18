# ERW 0.3.0 — Baseline, Additionality & Scenario Modeling

A reproducible, **illustrative-only** scenario ledger. Inputs are deliberately supplied rather than fabricated from field records. Ten-year comparison of 0, 10, 20 t/ha over a hypothetical 100 ha Wexford site is the default research fixture. v0.3.0 does NOT claim to establish causal additionality, measured fluxes, net CDR or permanence.

## Modeling boundaries
- Gross theoretical capacity from ERW 0.2.0 is explicitly referenced by its hash.
- Annual realization fractions allocate a share of the initial feedstock chemical potential. Fractions must total <=1; no double counting. These fractions are assumptions, **not modeled weathering kinetics**.
- User-defined annual background potential is shared by all scenarios; incremental proxy is treatment-derived only. This **does not** constitute an empirically identified no-treatment counterfactual.
- Zero-dose control required; rates unique; full year range; all finite numbers; cumulative mass constraints.
- Results stored through existing Workbench v12.2 owner-scoped SQLite project store; no migrations, no auth changes.
- Future v0.4/0.5 must resolve LCA, actual kinetics, leaching/secondary minerals, MRV and permanent storage. Do not call the outputs additional durable carbon removals.

## Routes
GET /erw/v0.3.0/status
POST /erw/v0.3.0/scenarios
POST /erw/v0.3.0/projects/scenarios (bearer auth)

## Mac test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.3.0-baseline-additionality-scenarios
git switch feature/erw-0.3.0-baseline-additionality-scenarios
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py
```

## Contabo preparation (only after Mac tests pass)
The production backend is a source directory, **not** a Git clone: /opt/sustainable-catalyst/workbench. Running v14.0.0-erw020 image must be retained for rollback.
Mac scp `backend/app/erw_v030.py` and `backend/tests/test_erw_v030.py` to `catalystadmin@94.72.113.77:/tmp/`.
Contabo: back up backend/compose; copy the new files into backend/app and backend/tests and append one new import/router registration to the end of backend/app/main.py. Build image `sustainable-catalyst-workbench:14.0.0-erw030` using `docker build -t sustainable-catalyst-workbench:14.0.0-erw030 -f backend/Dockerfile backend`. Keep existing compose.erw020.yml. New override compose.erw030.yml specifies the new image only; combine with compose.yml and deploy with `--no-build`. Wait for healthy before checking routes. Verify project save/package with a new ephemeral test session. Do not print auth tokens or .env. Roll back using compose.yml + compose.erw020.yml; preserve /data.

## Test fixture
0, 10, 20 t/ha; 100 ha; theoretical 0.3181033497849858083214093835 tCO2/t feedstock from **synthetic** ERW 0.2.0 sample; ten annual assumed shares each 0.1; assumed background potential 2 tCO2/year. Neither input is observed Wexford data.
