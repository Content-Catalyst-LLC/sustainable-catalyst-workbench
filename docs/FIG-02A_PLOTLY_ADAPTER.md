# SC-FIG-01 / FIG-02A — Plotly scientific figure adapter

**State:** source candidate, default disabled. Not deployed. Not owner-bound. Not publication-approved.

FIG-02A adds a Plotly renderer to the existing Workbench v8.9 figure composer. It does not add a
second figure studio: Workbench stays the numerical authority, Lab Graph Studio stays the authoring
surface, and Platform Core keeps `contract.plotly` as contract metadata only.

## Files

| File | Role |
|---|---|
| `backend/app/plotly_figure_adapter.py` | Request models, evidence/licence gates, Plotly compilation, accessible table, `sc.figure-bundle.v1` assembly, routes |
| `backend/app/plotly_export_worker.py` | Isolated PNG/SVG/PDF worker, run as `python -I` with a credential-free environment |
| `backend/requirements-plotly.txt` | Pinned optional runtime (`plotly==6.5.2`, `kaleido==1.2.0` and transitive pins). Not in the base image |
| `backend/tests/test_plotly_figure_adapter_fig02a.py` | Contract, numerical, security, reproducibility and export tests |
| `backend/tests/fixtures/fig02a_synthetic.json` | Synthetic CI values (no scientific meaning), same shape as the private acceptance fixture |
| `.github/workflows/fig-02a-plotly-adapter.yml` | Public CI for this test module (synthetic only) |

## Flags

| Variable | Default | Effect |
|---|---|---|
| `SCWB_PLOTLY_ADAPTER_ENABLED` | off | `POST /figure-adapters/plotly/compile` returns 503 while off |
| `SCWB_PLOTLY_STATIC_EXPORT_ENABLED` | off | Static formats are reported as `disabled` while off |
| `SCWB_PLOTLY_BROWSER_PATH` | unset | Explicit Chrome/Chromium binary for the worker. The worker never downloads a browser |

## Endpoints

- `GET /figure-adapters/plotly/status[?probe=true]`: pinned vs installed package versions, bundled
  plotly.js version, flags, and Core registration (`CONTRACT_ONLY`). With `probe=true` and export
  enabled, it renders one tiny SVG and reports the Chrome version. Installed state is never inferred
  from the Core registry.
- `POST /figure-adapters/plotly/compile`: exactly one source:
  - `workbenchFigure`: a v8.9 `FigureComposeRequest`. Jobs are reloaded with their integrity hash
    check; every panel/series must be one Workbench composed. Uncertainty metrics must exist in the
    same job scope. Evidence class must be `modelled`.
  - `dataset`: an authorized dataset whose canonical-JSON SHA-256 must equal the declared `sha256`.
    Its evidence class cannot be relabelled.

  The response holds the Plotly figure + config, an accessible table (structured rows plus escaped
  HTML `<table>`) and descriptive summary, the `sc.figure-bundle.v1` record, and optional static files.

Chart kinds: `line`, `scatter`, `bar`, `time-series` (explicit `xUnit`), `distribution` (box or
histogram), `heatmap` (rows × series).

## Scientific gates (enforced, tested)

- `evidenceClass` must match `measurementStatus`. `observed` requires every source to be
  `source-hash-verified` and `qualified`. Workbench computations are always `modelled`.
- Evidence class is printed in the figure subtitle, so it survives PNG/SVG/PDF export.
- One unit per panel; one measurement basis (for example soil depth) per panel; results with different
  durations cannot be joined by a line. Category labels carry the duration in static output.
- Uncertainty requires explicit `semantics` (`reported-plus-minus`, `standard-deviation`,
  `standard-error`, `confidence-interval-95`, `range-min-max`) and `origin`. Nothing is guessed.
  Values outside their interval are rejected.
- Missing values stay missing (gaps, `not reported`, `no quantified value reported`). NaN/±Inf are
  rejected.
- Review decisions are always `pending`. `ownerScope` is limited to `isolated-synthetic` or
  `unbound-local` and `environment` to `local-review` or `staging` until UP-01 lands.
- Licence: `restricted` sources are refused; `pending` sources render only for `local-review`.

## Security

- All user text is HTML-escaped and control characters are rejected; Plotly specs carry no images,
  links or templates from input; `extra="forbid"` on every model.
- `sourceUri` must be `https://` and is recorded, never fetched. No adapter code performs network I/O.
- The export worker loads plotly.js from the installed plotly.py package and disables MathJax.
  Kaleido's defaults would otherwise load plotly.js 2.35.2 and MathJax from public CDNs.
- One export at a time per process (429 otherwise), 90 s timeout, 10 MB per file, magic-byte checks.
- The compile route has the same authentication posture as the existing v8.9 compose route (none at
  the Workbench layer). **Do not enable the flag on an internet-reachable route before UP-01
  owner authentication is in front of it.**

## Tests: synthetic CI vs private scientific acceptance

- **Synthetic CI (default, public):** `fixtures/fig02a_synthetic.json` holds invented values. These tests
  prove adapter behaviour only (gates, hashing, escaping, export) and say nothing about any study.
- **Private scientific acceptance (`test_private_acceptance_*`):** run only when `SC_DATA_REPO_DIR`
  points to a checkout of the private Data repository. The Wexford SC-07/SC-08 literature fixture
  (`research/wexford-erw/fixtures/fig02a-sc07-sc08-literature-fixture.json`), its citations,
  uncertainty definitions, manifest hash and replay map live **only** there. The public test file
  contains no private values; expected results are read from the private fixture. Without the
  checkout these tests skip with `private scientific acceptance NOT_PERFORMED`.

```sh
cd backend
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-plotly.txt jsonschema==4.26.0
python -m pytest -q -rs tests/test_plotly_figure_adapter_fig02a.py          # synthetic only
SC_DATA_REPO_DIR=../../data python -m pytest -q -rs tests/test_plotly_figure_adapter_fig02a.py  # + private acceptance
```

Static export tests need a local Chrome/Chromium; otherwise they skip and report `NOT_PERFORMED`.
`main` currently cannot import `app.main` because `app/v10110.py` is missing from the repository (see
the PR description); the route-registration test skips in that case.

## Not done here

- Lab Graph Studio preview of the Plotly JSON (browser-side plotly.js must match `plotlyJsVersion`).
- Container image with Chrome + `requirements-plotly.txt`, SBOM and licence review.
- Metrics of Sustainable Development (SDM-UNSD-2026) acceptance: source files are not in any
  repository and their licence is recorded as `requires license review`.
- Owner-bound persistence, Workspace insertion and Research publication (UP-01/UP-03/UP-04).
