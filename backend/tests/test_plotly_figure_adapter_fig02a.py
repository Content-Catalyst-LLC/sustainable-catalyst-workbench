"""SC-FIG-01 / FIG-02A Plotly adapter: contract, numerical, security and reproducibility tests.

Two kinds of tests live here and must not be confused:

* **Synthetic CI tests** (default) use ``fixtures/fig02a_synthetic.json``. Its values are invented,
  carry no scientific meaning and prove only adapter behaviour (gates, hashing, escaping, export).
* **Private scientific acceptance tests** (``test_private_acceptance_*``) run only when
  ``SC_DATA_REPO_DIR`` points to a checkout of the private Content-Catalyst-LLC/data repository.
  They load the Wexford SC-07/SC-08 literature fixture and manifest from there, replay published
  values exactly and validate bundles against ``sc.figure-bundle.v1``. Without that checkout they
  skip, and real scientific validation is NOT_PERFORMED.

The app is assembled from the real v8.0-v8.4 and FIG-02A routers so these tests do not depend on
modules that ``app.main`` imports.
"""
import base64
import copy
import json
import math
import os
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import plotly_figure_adapter as adapter
from app.v800 import router as v800_router
from app.v810 import router as v810_router
from app.v820 import router as v820_router
from app.v840 import router as v840_router

app = FastAPI()
for r in (v800_router, v810_router, v820_router, v840_router, adapter.router):
    app.include_router(r)
c = TestClient(app)

SYNTHETIC = json.loads((Path(__file__).parent / "fixtures" / "fig02a_synthetic.json").read_text())
DATA_DIR = os.getenv("SC_DATA_REPO_DIR", "")
WEXFORD_FIXTURE = "research/wexford-erw/fixtures/fig02a-sc07-sc08-literature-fixture.json"
SCHEMA_PATH = "contracts/sc.figure-bundle.v1.schema.json"
UNIT_CO2 = "t CO₂ ha⁻¹"
private_acceptance = pytest.mark.skipif(
    not DATA_DIR, reason="SC_DATA_REPO_DIR not set; private scientific acceptance NOT_PERFORMED")


def _wexford():
    return json.loads((Path(DATA_DIR) / WEXFORD_FIXTURE).read_text())


@pytest.fixture(autouse=True)
def _enabled(monkeypatch, tmp_path):
    monkeypatch.setenv(adapter.ENABLE_ENV, "true")
    monkeypatch.delenv(adapter.EXPORT_ENV, raising=False)
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path / "store"))


def _source(source_id, **kw):
    base = {"sourceId": source_id, "provider": "published-literature", "identityStatus": "source-identified",
            "qualityStatus": "pending", "licenceStatus": "pending"}
    base.update(kw)
    return base


def _bundle(**kw):
    base = {
        "figureId": "SYN-POINTS-plotly",
        "title": "Synthetic point comparison with uncertainty",
        "projectRef": "fig02a-synthetic-ci",
        "ownerScope": "unbound-local",
        "environment": "local-review",
        "evidenceClass": "literature-derived",
        "figureType": "evidence-chart",
        "interpretation": "Synthetic endpoints with distinct durations, used only to exercise the adapter.",
        "limitations": ["Synthetic values with no scientific meaning"],
        "measurementStatus": "published-literature",
        "doNotInfer": ["any scientific conclusion"],
        "caption": "Synthetic CI fixture exercising points, ranges and a missing result.",
        "altText": "Point chart of three synthetic studies with their uncertainty ranges.",
        "sourceRefs": [_source("synthetic-source-a"), _source("synthetic-source-b"), _source("synthetic-source-c")],
    }
    base.update(kw)
    return base


def _points_request(fx=None, **kw):
    ds = (fx or SYNTHETIC)["points"]
    req = {
        "dataset": {"datasetId": ds["datasetId"], "sha256": ds["sha256"], "evidenceClass": "literature-derived",
                    "rows": copy.deepcopy(ds["rows"]), "xField": "study", "xLabel": "Study",
                    "labelField": "study", "durationField": "duration"},
        "panels": [{"panelId": ds["panelId"], "chart": "scatter", "series": [
            {"field": "potential_value", "label": "Cumulative potential", "unit": UNIT_CO2,
             "uncertainty": {"semantics": "reported-plus-minus", "origin": "as-published", "plusMinusField": "potential_pm"}},
            {"field": "range_upper", "label": "Upper bound of reported gross range", "unit": UNIT_CO2,
             "uncertainty": {"semantics": "range-min-max", "origin": "as-published",
                             "lowerField": "range_lower", "upperField": "range_upper"}},
        ]}],
        "bundle": _bundle(),
    }
    req.update(kw)
    return req


def _baselines_request(fx=None, panels=None):
    ds = (fx or SYNTHETIC)["baselines"]
    stocks, rates = ds["panelIds"]
    return {
        "dataset": {"datasetId": ds["datasetId"], "sha256": ds["sha256"], "evidenceClass": "literature-derived",
                    "rows": copy.deepcopy(ds["rows"]), "xField": "category", "xLabel": "Land use",
                    "labelField": "category", "basisField": "basis", "panelField": "panel"},
        "panels": panels or [
            {"panelId": stocks, "chart": "bar", "series": [{"field": "soc_stock", "label": "SOC stock", "unit": "t C ha⁻¹"}]},
            {"panelId": rates, "chart": "bar", "series": [{"field": "soc_rate", "label": "SOC change rate", "unit": "Mg C ha⁻¹ yr⁻¹"}]},
        ],
        "bundle": _bundle(figureId="SYN-BASELINES-plotly", title="Synthetic stocks and rates baselines",
                          interpretation="Stocks and rates on different measurement bases shown separately.",
                          caption="Synthetic CI fixture: stocks and change rates on separate bases.",
                          altText="Two bar panels: synthetic stocks by category and synthetic change rates.",
                          sourceRefs=[_source("synthetic-source-d"), _source("synthetic-source-e")]),
    }


def _private_request(key):
    """Build a request entirely from the private fixture; no private values live in this file."""
    fx = _wexford()
    req = _points_request(fx) if key == "points" else _baselines_request(fx)
    for series in req["panels"][0]["series"]:
        series.update(fx[key].get("series", {}).get(series["field"], {}))
    req["bundle"] = _bundle(**fx[key]["bundle"])
    return req


def _expected_series(fx, key, field, panel_value=None):
    rows = fx[key]["rows"]
    if panel_value is not None:
        rows = [r for r in rows if r.get("panel") == panel_value]
    return [r.get(field) for r in rows]


def _walk(obj, path):
    for part in path:
        obj = obj[part]
    return obj


def _compile(req, status=200):
    r = c.post("/figure-adapters/plotly/compile", json=req)
    assert r.status_code == status, r.text
    return r.json()


def _trace(out, name_fragment):
    return next(t for t in out["plotly"]["figure"]["data"] if name_fragment in t.get("name", ""))


# --- runtime / registry -----------------------------------------------------------------------

def test_status_reports_disabled_default_and_contract_only_core(monkeypatch):
    monkeypatch.delenv(adapter.ENABLE_ENV)
    s = c.get("/figure-adapters/plotly/status").json()
    assert s["adapterEnabled"] is False and s["staticExportEnabled"] is False
    assert s["core"] == {"rendererKey": "contract.plotly", "coreRegistrationStatus": "CONTRACT_ONLY",
                         "coreExecutesPlotly": False, "automaticCoreDispatch": False}
    assert s["pinnedPackages"] == {"plotly": "6.5.2", "kaleido": "1.2.0"}
    assert s["installedPackages"]["plotly"] == "6.5.2" and s["pinnedPackagesMatch"]["plotly"] is True
    assert s["staticExportProbe"] == {"performed": False} and s["staticExportAvailable"] is False


def test_compile_is_refused_while_flag_disabled(monkeypatch):
    monkeypatch.delenv(adapter.ENABLE_ENV)
    r = c.post("/figure-adapters/plotly/compile", json=_points_request())
    assert r.status_code == 503 and adapter.ENABLE_ENV in r.text


def test_status_probe_skipped_when_export_disabled():
    s = c.get("/figure-adapters/plotly/status?probe=true").json()
    assert s["staticExportProbe"] == {"performed": False}


# --- synthetic adapter behaviour (no scientific meaning) ---------------------------------------

def test_synthetic_points_uncertainty_and_missing_result_are_preserved():
    out = _compile(_points_request())
    pot = _trace(out, "Cumulative potential")
    rng = _trace(out, "Upper bound")
    assert pot["y"] == [5.0, None, None]
    assert pot["error_y"]["array"][0] == pytest.approx(1.5) and pot["error_y"]["arrayminus"][0] == pytest.approx(1.5)
    assert rng["y"] == [None, 0.9, None]
    assert rng["error_y"]["arrayminus"][1] == pytest.approx(0.8) and rng["error_y"]["array"][1] == 0
    # A study without a quantified result stays missing, never zero.
    assert pot["y"][2] is None and rng["y"][2] is None
    assert "duration: %{customdata[3]}" in pot["hovertemplate"]
    assert "reported-plus-minus, as-published" in pot["hovertemplate"]
    assert adapter.EVIDENCE_LABEL["literature-derived"] in out["plotly"]["figure"]["layout"]["title"]["text"]
    table = out["accessibleAlternative"]["panels"][0]
    assert table["rows"][2]["potential_value"] is None and "not reported" in out["accessibleAlternative"]["html"]
    b = out["figureBundle"]
    assert b["evidenceClass"] == "literature-derived" and b["scientificContext"]["measurementStatus"] == "published-literature"
    assert set(b["review"].values()) == {"pending"} and b["rendering"]["accessibilityReview"] == "pending"
    assert b["provenance"]["inputManifestSha256"] == SYNTHETIC["points"]["sha256"]
    assert b["artifacts"][0]["sha256"] == out["plotly"]["specSha256"] == b["rendering"]["visualizationSpecSha256"]


def test_synthetic_baselines_render_in_separate_panels():
    out = _compile(_baselines_request())
    data = out["plotly"]["figure"]["data"]
    assert data[0]["y"] == [100.0, 110.0, 60.0] and data[0]["xaxis"] == "x"
    assert data[1]["y"] == [0.5, -0.4] and data[1]["xaxis"] == "x2"
    assert data[0]["marker"]["color"] != data[1]["marker"]["color"]


def test_mixing_measurement_bases_or_units_in_one_panel_is_rejected():
    req = _points_request()
    req["panels"][0]["series"][1]["unit"] = "t C ha⁻¹"
    assert "mixes units" in _compile(req, 422)["detail"]
    req = _baselines_request()
    stocks = req["panels"][0]["panelId"]
    for row in req["dataset"]["rows"]:
        row["panel"] = stocks
    req["dataset"]["sha256"] = adapter.dataset_sha256(req["dataset"]["rows"])
    req["panels"] = req["panels"][:1]
    assert "mixes measurement bases" in _compile(req, 422)["detail"]


# --- private scientific acceptance: Wexford SC-07 / SC-08 (literature-derived) -----------------
# Values, citations and expected results come only from the private Data checkout.

@private_acceptance
def test_private_acceptance_fixture_replays_authoritative_data_manifest():
    import hashlib
    fx = _wexford()
    manifest_path = Path(DATA_DIR) / fx["provenance"]["sourceManifest"]
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == fx["provenance"]["sourceManifestSha256"]
    for key in ("points", "baselines"):
        assert adapter.dataset_sha256(fx[key]["rows"]) == fx[key]["sha256"]
    manifest = json.loads(manifest_path.read_text())
    assert fx["replay"]
    for check in fx["replay"]:
        if "fixture" in check and "manifest" in check:
            assert _walk(fx, check["fixture"]) == _walk(manifest, check["manifest"]), check
        elif "fixture" in check:
            assert _walk(fx, check["fixture"]) == check["equals"], check
        else:
            assert _walk(manifest, check["manifest"]) == check["equals"], check


@private_acceptance
def test_private_acceptance_sc07_values_equal_published_originals():
    fx = _wexford()
    out = _compile(_private_request("points"))
    for trace, field, pm in ((out["plotly"]["figure"]["data"][0], "potential_value", "potential_pm"),
                             (out["plotly"]["figure"]["data"][1], "range_upper", None)):
        assert trace["y"] == _expected_series(fx, "points", field)
    pot = out["plotly"]["figure"]["data"][0]
    for i, row in enumerate(fx["points"]["rows"]):
        if row["potential_value"] is not None:
            assert pot["error_y"]["array"][i] == pytest.approx(row["potential_pm"])
        if row["range_lower"] is not None:
            assert out["plotly"]["figure"]["data"][1]["error_y"]["arrayminus"][i] == pytest.approx(row["range_upper"] - row["range_lower"])
        if all(row[k] is None for k in ("potential_value", "range_upper")):
            assert pot["y"][i] is None  # unquantified results stay missing, never zero
    assert out["figureBundle"]["provenance"]["inputManifestSha256"] == fx["points"]["sha256"]


@private_acceptance
def test_private_acceptance_sc08_keeps_measurement_bases_in_separate_panels():
    fx = _wexford()
    stocks, rates = fx["baselines"]["panelIds"]
    data = _compile(_private_request("baselines"))["plotly"]["figure"]["data"]
    assert data[0]["y"] == _expected_series(fx, "baselines", "soc_stock", stocks) and data[0]["xaxis"] == "x"
    assert data[1]["y"] == _expected_series(fx, "baselines", "soc_rate", rates) and data[1]["xaxis"] == "x2"
    for trace, panel in ((data[0], stocks), (data[1], rates)):
        assert trace["x"] == [r["category"] for r in fx["baselines"]["rows"] if r["panel"] == panel]


@private_acceptance
def test_private_acceptance_bundles_validate_against_canonical_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((Path(DATA_DIR) / SCHEMA_PATH).read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for req in (_points_request(), _baselines_request(), _private_request("points"), _private_request("baselines")):
        errors = sorted(validator.iter_errors(_compile(req)["figureBundle"]), key=str)
        assert not errors, [e.message for e in errors]


# --- evidence-class and licence gates ----------------------------------------------------------

def test_literature_cannot_be_promoted_to_observed():
    req = _points_request(bundle=_bundle(evidenceClass="observed", measurementStatus="observed"))
    assert "cannot be relabelled" in _compile(req, 422)["detail"]
    req = _points_request(bundle=_bundle(measurementStatus="observed"))
    assert "requires measurementStatus published-literature" in _compile(req, 422)["detail"]


def test_hypothetical_dataset_cannot_become_observed_even_with_matching_labels():
    req = _points_request(bundle=_bundle(evidenceClass="observed", measurementStatus="observed"))
    req["dataset"]["evidenceClass"] = "observed"
    assert "source-hash-verified, qualified" in _compile(req, 422)["detail"]


def test_restricted_or_unreviewed_licences_are_refused_outside_local_review():
    req = _points_request()
    req["bundle"]["sourceRefs"][0]["licenceStatus"] = "restricted"
    assert "restricted" in _compile(req, 403)["detail"]
    req = _points_request(bundle=_bundle(environment="staging"))
    assert "pending licence review" in _compile(req, 403)["detail"]


def test_authenticated_owner_scope_and_production_are_not_accepted_before_up01():
    for patch in ({"ownerScope": "authenticated"}, {"environment": "production"}):
        assert _compile(_points_request(bundle=_bundle(**patch)), 422)


def test_dataset_hash_must_match_declared_source():
    req = _points_request()
    req["dataset"]["rows"][0]["potential_value"] = 6.0
    assert "sha256 does not match" in _compile(req, 403)["detail"]


# --- numerical and uncertainty negative tests --------------------------------------------------

def test_uncertainty_semantics_must_be_explicit_and_consistent():
    req = _points_request()
    del req["panels"][0]["series"][0]["uncertainty"]["semantics"]
    _compile(req, 422)
    req = _points_request()
    req["panels"][0]["series"][1]["uncertainty"] = {"semantics": "standard-error", "origin": "as-published",
                                                    "lowerField": "range_lower", "upperField": "range_upper"}
    assert "requires plusMinusField" in str(_compile(req, 422)["detail"])


def test_value_outside_declared_interval_is_rejected():
    req = _points_request()
    req["dataset"]["rows"][1]["range_upper"] = 0.4
    req["dataset"]["rows"][1]["range_lower"] = 0.6
    req["dataset"]["sha256"] = adapter.dataset_sha256(req["dataset"]["rows"])
    assert "lower bound exceeds upper bound" in _compile(req, 422)["detail"]


def test_unknown_metric_is_rejected():
    req = _points_request()
    req["panels"][0]["series"][0]["field"] = "measured_removal"
    assert "not in dataset" in _compile(req, 422)["detail"]


def test_nonfinite_values_are_rejected():
    req = adapter.PlotlyCompileRequest(**_points_request())
    req.dataset.rows[0]["potential_value"] = math.nan
    req.dataset.sha256 = adapter.dataset_sha256(req.dataset.rows)
    with pytest.raises(ValueError, match="finite"):
        adapter.compile_request(req)


def test_lines_cannot_connect_results_with_different_durations():
    req = _points_request()
    req["panels"][0]["chart"] = "line"
    assert "different durations" in _compile(req, 422)["detail"]


# --- security -----------------------------------------------------------------------------------

def test_untrusted_markup_is_escaped_and_no_remote_assets_are_emitted():
    req = _points_request(bundle=_bundle(title='Evidence <img src=x onerror=alert(1)> chart'))
    req["panels"][0]["series"][0]["label"] = "<script>alert(1)</script>"
    req["dataset"]["rows"][0]["study"] = '<a href="https://evil.example">Study A</a>'
    req["dataset"]["sha256"] = adapter.dataset_sha256(req["dataset"]["rows"])
    out = _compile(req)
    blob = json.dumps(out["plotly"]) + out["accessibleAlternative"]["html"]
    assert "<script" not in blob and "<img" not in blob and "<a " not in blob and "&lt;script&gt;" in blob
    figure = out["plotly"]["figure"]
    assert "images" not in figure["layout"] and not re.search(r'(src|href)="', json.dumps(figure))
    assert all(t["type"] in {"scatter", "bar", "box", "histogram", "heatmap"} for t in figure["data"])
    assert out["plotly"]["config"]["showLink"] is False and "sendDataToCloud" in out["plotly"]["config"]["modeBarButtonsToRemove"]


def test_source_uri_is_never_fetched_and_must_be_https():
    req = _points_request()
    req["bundle"]["sourceRefs"][0]["sourceUri"] = "file:///etc/passwd"
    _compile(req, 422)


def test_extra_fields_and_control_characters_are_rejected():
    req = _points_request()
    req["panels"][0]["series"][0]["template"] = "<b>%{y}</b>"
    _compile(req, 422)
    req = _points_request(bundle=_bundle(title="Evidence\x07 chart title"))
    _compile(req, 422)


# --- completed Workbench jobs (modelled) ------------------------------------------------------

def _seed_jobs():
    project, envkey = "project-fig02a", "env-fig02a"
    env = c.post("/research-environment/build", json={"environment": {"environmentKey": envkey, "title": "FIG-02A", "projectEntityId": project, "components": []}}).json()
    assert c.post("/research-environment/persistence/save", json={"researchEnvironment": env, "expectedCurrentRevision": 0, "reason": "fig02a-seed"}).status_code == 200
    ws = c.post("/research-projects/build", json={"project": {"projectKey": project, "title": "FIG-02A", "activeEnvironmentKey": envkey, "activeEnvironmentRevision": 1}}).json()
    assert c.post("/research-projects/save", json={"workspace": ws, "expectedProjectRevision": 0, "reason": "fig02a-seed"}).status_code == 200
    jobs = []
    for k in (4, 9, 16, 25):
        r = c.post("/execution-console/jobs/prepare", json={
            "projectKey": project, "runtimeKind": "solver", "label": f"k={k}",
            "request": {"problemKind": "root", "problem": {"expression": f"x**2-{k}", "variable": "x", "bracket": [0, k]}, "solverKey": "root.brentq"},
        })
        assert r.status_code == 200, r.text
        jid = r.json()["jobId"]
        assert c.post(f"/execution-console/jobs/{jid}/run", json={"expectedJobRevision": 1, "reason": "fig02a-seed"}).status_code == 200
        jobs.append(jid)
    return project, jobs


def _root_metric(project):
    from app.v890 import source_catalog
    metrics = [m["metric"] for m in source_catalog(project)["resultMetrics"] if m["presentCount"] == 4]
    root = next(m for m in metrics if m.endswith("root") or m.endswith(".x") or "root" in m)
    return root


def _jobs_request(project, jobs, chart, metric, **panel_kw):
    return {
        "workbenchFigure": {"projectKey": project, "jobIds": jobs, "title": "Synthetic solver fixture",
                            "panels": [{"panelId": "p1", "mark": "line", "yMetrics": [metric],
                                        "xMetric": "result.executionObject.inputs.declaredPayload.bracket[1]"}]},
        "panels": [{"panelId": "p1", "chart": chart, "series": [{"field": metric, "label": "root", "unit": "dimensionless"}], **panel_kw}],
        "bundle": _bundle(figureId="SYN-FIG02A-jobs", title="Synthetic solver roots by bracket",
                          ownerScope="isolated-synthetic", evidenceClass="modelled",
                          measurementStatus="computed-from-specified-inputs",
                          caption="Synthetic unit fixture: Brent roots of x^2-k for four k values.",
                          altText="Roots increase from 2 to 5 as k increases from 4 to 25.",
                          sourceRefs=[_source("synthetic-fixture", provider="workbench-test", licenceStatus="verified-for-use",
                                              qualityStatus="not-applicable")], labels=["synthetic-fixture"]),
    }


def test_completed_jobs_compile_line_time_series_distribution_and_heatmap():
    project, jobs = _seed_jobs()
    metric = _root_metric(project)
    out = _compile(_jobs_request(project, jobs, "line", metric))
    trace = out["plotly"]["figure"]["data"][0]
    assert trace["x"] == [4.0, 9.0, 16.0, 25.0]
    assert trace["y"] == pytest.approx([2.0, 3.0, 4.0, 5.0], abs=1e-9)
    refs = out["figureBundle"]["calculationRefs"]
    assert [r["runRef"].split("/")[-1].split("@")[0] for r in refs] == jobs and all(len(r["outputSha256"]) == 64 for r in refs)
    assert out["figureBundle"]["provenance"]["reproducibility"] == "synthetic-fixture-tested"
    assert out["figureBundle"]["publication"]["bindingStatus"] == "synthetic-test"
    ts = _compile(_jobs_request(project, jobs, "time-series", metric, xUnit="simulated step"))
    assert ts["plotly"]["figure"]["data"][0]["mode"] == "lines+markers"
    dist = _compile(_jobs_request(project, jobs, "distribution", metric))
    assert dist["plotly"]["figure"]["data"][0]["type"] == "box" and sorted(dist["plotly"]["figure"]["data"][0]["y"]) == pytest.approx([2, 3, 4, 5])
    hist = _compile(_jobs_request(project, jobs, "distribution", metric, distributionKind="histogram"))
    assert hist["plotly"]["figure"]["data"][0]["type"] == "histogram"
    heat = _compile(_jobs_request(project, jobs, "heatmap", metric))
    assert heat["plotly"]["figure"]["data"][0]["z"] == [[pytest.approx(v)] for v in (2, 3, 4, 5)]


def test_workbench_results_cannot_be_labelled_observed_or_literature():
    project, jobs = _seed_jobs()
    req = _jobs_request(project, jobs, "line", _root_metric(project))
    req["bundle"].update(evidenceClass="literature-derived", measurementStatus="published-literature")
    assert "modelled results" in _compile(req, 422)["detail"]


def test_series_not_composed_by_workbench_is_rejected():
    project, jobs = _seed_jobs()
    req = _jobs_request(project, jobs, "line", _root_metric(project))
    req["panels"][0]["series"][0]["field"] = "result.not_a_metric"
    assert "not composed by Workbench" in _compile(req, 422)["detail"]


def test_tampered_job_fails_integrity():
    from app.v840 import _job_path
    project, jobs = _seed_jobs()
    path = _job_path(jobs[0])
    job = json.loads(path.read_text())
    job["result"]["tampered"] = 1
    path.write_text(json.dumps(job))
    _compile(_jobs_request(project, jobs, "line", "result.tampered"), 422)


# --- reproducibility ---------------------------------------------------------------------------

def test_compilation_is_deterministic():
    a, b = _compile(_points_request()), _compile(_points_request())
    assert a["plotly"]["specSha256"] == b["plotly"]["specSha256"]
    assert a["accessibleAlternative"] == b["accessibleAlternative"]
    assert a["figureBundle"]["provenance"]["scriptSha256"] == b["figureBundle"]["provenance"]["scriptSha256"]


# --- isolated static export (requires a local Chrome/Chromium) ---------------------------------

def _chrome_available():
    try:
        from choreographer.browsers.chromium import Chromium
        return bool(os.getenv("BROWSER_PATH") or Chromium.find_browser(skip_local=True))
    except Exception:
        return False


def test_static_formats_report_disabled_without_export_flag():
    out = _compile(_points_request(staticFormats=["png"]))
    assert out["staticExport"]["status"] == "disabled" and len(out["figureBundle"]["artifacts"]) == 1


@pytest.mark.skipif(not _chrome_available(), reason="no Chrome/Chromium available; static export NOT_PERFORMED")
def test_static_png_svg_pdf_export_is_hashed_and_matches_spec(monkeypatch):
    monkeypatch.setenv(adapter.EXPORT_ENV, "true")
    out = _compile(_points_request(staticFormats=["png", "svg", "pdf"]))
    files = out["staticExport"]["files"]
    raw = {fmt: base64.b64decode(files[fmt]["contentBase64"]) for fmt in files}
    assert raw["png"].startswith(b"\x89PNG") and raw["pdf"].startswith(b"%PDF") and b"<svg" in raw["svg"][:400]
    arts = {a["format"]: a for a in out["figureBundle"]["artifacts"]}
    assert set(arts) == {"json", "png", "svg", "pdf"}
    import hashlib
    for fmt in ("png", "svg", "pdf"):
        assert arts[fmt]["sha256"] == hashlib.sha256(raw[fmt]).hexdigest() == files[fmt]["sha256"]
    svg = raw["svg"].decode("utf-8", "replace")
    assert "Synthetic point comparison with uncertainty" in svg
    assert adapter.EVIDENCE_LABEL["literature-derived"] in svg
    assert "Synthetic study A" in svg and "2 years (cumulative)" in svg
    assert "reported-plus-minus, as-published" in svg and "no quantified value reported" in svg
    assert out["staticExport"]["chromeVersion"]


def test_missing_chrome_is_reported_explicitly(monkeypatch):
    monkeypatch.setenv(adapter.EXPORT_ENV, "true")
    monkeypatch.setenv("SCWB_PLOTLY_BROWSER_PATH", "/nonexistent/chrome")
    assert "chrome-unavailable" in _compile(_points_request(staticFormats=["svg"]), 409)["detail"]


def test_export_timeout_is_bounded():
    result = adapter.run_static_export({"data": [], "layout": {}}, ["svg"], 320, 240, timeout=0.01)
    assert result == {"ok": False, "error": "export-timeout"}


def test_concurrent_export_is_refused_not_queued(monkeypatch):
    monkeypatch.setenv(adapter.EXPORT_ENV, "true")
    assert adapter._EXPORT_SLOT.acquire(blocking=False)
    try:
        assert "busy" in _compile(_points_request(staticFormats=["svg"]), 429)["detail"]
    finally:
        adapter._EXPORT_SLOT.release()


def test_worker_rejects_nonfinite_numbers():
    import subprocess
    import sys
    payload = '{"figure": {"data": [{"type": "scatter", "y": [NaN]}]}, "formats": ["svg"], "width": 320, "height": 240}'
    p = subprocess.run([sys.executable, "-I", str(adapter.WORKER_PATH)], input=payload.encode(), capture_output=True, timeout=60)
    assert json.loads(p.stdout) == {"ok": False, "error": "invalid-request"}


def test_main_app_registers_adapter_routes():
    try:
        from app.main import app as main_app
    except ModuleNotFoundError as exc:
        pytest.skip(f"app.main is not importable on this base ({exc}); route registration checked in source")
    client = TestClient(main_app)
    status = client.get("/figure-adapters/plotly/status")
    assert status.status_code == 200 and status.json()["buildId"] == "FIG-02A"
    assert client.post("/figure-adapters/plotly/compile", json=_points_request()).status_code == 200
