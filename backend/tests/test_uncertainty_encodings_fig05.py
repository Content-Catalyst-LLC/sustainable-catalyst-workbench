"""SC-FIG-05.3 Workbench: interval ribbons and ensemble quantile fans drawn only from runtime-computed records.

``fixtures/sc_fig05_runtime_records.json`` holds real Workspace export records produced from synthetic inputs
(R ``stats::predict.lm`` bands and the uncertainty runtime's ensemble-quantile-bands op). The checks here
recompute the bands and quantiles independently with NumPy/SciPy. Synthetic only.
"""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from app import plotly_figure_adapter as adapter
from app.v510 import content_hash
from tests.test_plotly_figure_adapter_fig02a import _bundle, _compile, _points_request, _source, c  # noqa: F401

FX = json.loads((Path(__file__).parent / "fixtures" / "sc_fig05_runtime_records.json").read_text())
ROWS = FX["rows"]


@pytest.fixture(autouse=True)
def _enabled(monkeypatch, tmp_path):
    monkeypatch.setenv(adapter.ENABLE_ENV, "true")
    monkeypatch.delenv(adapter.EXPORT_ENV, raising=False)
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path / "store"))


def _band_calc(**kw):
    b = FX["band"]
    calc = {"label": "Synthetic trend of y", "unit": "mg L⁻¹", "xLabel": "t (years from 2010)", "method": "R stats::lm with stats::predict.lm bands",
            "runRef": "sc://workspace/runs/synthetic-fig05-band", "values": b["values"], "bands": copy.deepcopy(b["bands"]),
            "linearFit": {"interceptKey": "intercept", "slopeKey": "slope"}, "assumptions": b["assumptions"]}
    calc.update(kw)
    return {k: v for k, v in calc.items() if v is not None}


def _fan_calc(**kw):
    f = FX["fan"]
    calc = {"label": "Synthetic ensemble projection", "unit": "mg L⁻¹", "xLabel": "Year", "method": "Uncertainty runtime ensemble-quantile-bands",
            "runRef": "sc://workspace/runs/synthetic-fig05-fan", "values": f["values"], "quantileBands": copy.deepcopy(f["quantileBands"]),
            "assumptions": f["assumptions"]}
    calc.update(kw)
    return {k: v for k, v in calc.items() if v is not None}


def _modelled_bundle(**kw):
    base = dict(figureId="SYN-FIG05-uncertainty", title="Synthetic runtime uncertainty encodings",
                evidenceClass="modelled", measurementStatus="computed-from-specified-inputs", ownerScope="isolated-synthetic",
                interpretation="Synthetic model outputs used only to exercise uncertainty encodings.",
                caption="Synthetic runtime-computed bands and ensemble fans; no scientific meaning.",
                altText="Line with shaded runtime confidence and prediction bands, and an ensemble quantile fan.",
                sourceRefs=[_source("synthetic-fig05", licenceStatus="verified-for-use", qualityStatus="not-applicable")])
    return _bundle(**{**base, **kw})


def _runtime_request(calcs=None, panels=None, **kw):
    req = {"panels": panels or [{"panelId": "trend", "chart": "band", "calculation": 0},
                                {"panelId": "ensemble", "chart": "fan", "calculation": 1}],
           "calculations": calcs if calcs is not None else [_band_calc(), _fan_calc()],
           "bundle": _modelled_bundle()}
    req.update(kw)
    return req


def _traces(out, role):
    return [t for t in out["plotly"]["figure"]["data"] if (t.get("meta") or {}).get("scUncertainty", {}).get("role") == role]


# --- drawing what the runtime computed ---------------------------------------------------------------------------

def test_band_ribbons_are_the_runtime_numbers_and_match_independent_ols():
    out = _compile(_runtime_request())
    bands = _traces(out, "band")
    assert [t["meta"]["scUncertainty"]["semantics"] for t in bands] == ["prediction-band", "confidence-band"]
    t = np.array([r["t"] for r in ROWS], float)
    y = np.array([r["y"] for r in ROWS], float)
    X = np.column_stack([np.ones_like(t), t])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    dof = len(y) - 2
    s2 = float(((y - X @ beta) ** 2).sum() / dof)
    q = stats.t.ppf(0.95, dof)  # level 0.9
    inv = np.linalg.inv(X.T @ X)
    xs = sorted(set(t.tolist()))
    for trace, extra in zip(bands, (1.0, 0.0)):
        n = len(xs)
        assert trace["x"] == xs + xs[::-1] and trace["fill"] == "toself"
        upper, lower = trace["y"][:n], trace["y"][n:][::-1]
        for x0, lo, hi in zip(xs, lower, upper):
            v = np.array([1.0, x0])
            fit, half = float(v @ beta), q * np.sqrt(s2 * (float(v @ inv @ v) + extra))
            assert abs(lo - (fit - half)) < 1e-9 and abs(hi - (fit + half)) < 1e-9
    fit = _traces(out, "fit")[0]
    assert all(abs(f - (beta[0] + beta[1] * x0)) < 1e-9 for x0, f in zip(fit["x"], fit["y"]))
    names = " ".join(t["name"] for t in bands)
    assert "90% prediction band (Student t, df 10" in names and "90% confidence band" in names and "Workspace runtime" in names
    u = {p["panelId"]: p for p in out["uncertainty"]}
    assert u["trend"]["status"] == "runtime-computed"
    assert u["trend"]["consistency"] == ["symmetric-student-t", "prediction-confidence-residual-variance-constant",
                                         "fit-equals-exported-coefficients"]
    assert out["boundaries"]["uncertaintyComputedByAdapter"] is False
    assert u["trend"]["record"] == FX["band"]["bands"] and u["trend"]["recordSha256"] == content_hash(FX["band"]["bands"])
    assert u["trend"]["recordSha256"] == out["figureBundle"]["calculationRefs"][0]["bandsSha256"]
    assert {t["meta"]["scUncertainty"]["recordSha256"] for t in bands} == {u["trend"]["recordSha256"]}


def test_fan_is_the_runtime_quantiles_and_matches_numpy():
    out = _compile(_runtime_request())
    fans = _traces(out, "fan")
    assert [t["meta"]["scUncertainty"]["level"] for t in fans] == [0.95, 0.8, 0.5]  # widest drawn first
    members = np.array([m["values"] for m in FX["fanInput"]["members"]])
    steps = FX["fanInput"]["steps"]
    for trace in fans:
        lv, n = trace["meta"]["scUncertainty"]["level"], len(steps)
        upper, lower = trace["y"][:n], trace["y"][n:][::-1]
        for j in range(n):
            assert abs(lower[j] - np.quantile(members[:, j], (1 - lv) / 2)) < 1e-9
            assert abs(upper[j] - np.quantile(members[:, j], (1 + lv) / 2)) < 1e-9
    med = _traces(out, "median")[0]
    assert all(abs(m - np.median(members[:, j])) < 1e-9 for j, m in enumerate(med["y"]))
    assert "60 ensemble members" in fans[0]["name"]


def test_colour_vision_safe_single_hue_with_opacity_and_outline():
    out = _compile(_runtime_request())
    fills = {t["fillcolor"] for t in _traces(out, "band") + _traces(out, "fan")}
    assert all(f.startswith("rgba(0,114,178,") for f in fills)  # Okabe-Ito blue only; levels differ by opacity
    pred = _traces(out, "band")[0]
    assert pred["line"]["dash"] == "dash"  # prediction band is also distinguished by its dashed outline
    alphas = sorted(float(f.split(",")[-1].rstrip(")")) for f in fills)
    assert len(set(alphas)) == len(alphas)
    assert {t["line"]["color"] for t in _traces(out, "fit") + _traces(out, "median")} == {"#000000"}


def test_table_bundle_and_provenance_carry_runtime_records():
    req = _runtime_request()
    out = _compile(req)
    panels = {p["panelId"]: p for p in out["accessibleAlternative"]["panels"]}
    trend = panels["trend"]
    assert trend["uncertaintyStatus"] == "runtime-computed"
    keys = [c_["key"] for c_ in trend["columns"]]
    assert keys == ["x", "fit", "confidence.lower", "confidence.upper", "prediction.lower", "prediction.upper"]
    assert len(trend["rows"]) == 12 and "stats::predict.lm" in " ".join(trend["descriptiveSummary"])
    assert [c_["key"] for c_ in panels["ensemble"]["columns"]][:3] == ["x", "median", "q0.5.lower"]
    b = out["figureBundle"]
    ctx = b["scientificContext"]
    assert ctx["uncertaintyStatus"] == "runtime-computed"
    assert ctx["uncertaintyEncodings"] == ["ensemble-quantile-fan", "interval-ribbon", "prediction-ribbon", "table-columns"]
    refs = b["calculationRefs"]
    assert refs[0]["system"] == "workspace" and refs[0]["bandsSha256"] == content_hash(req["calculations"][0]["bands"])
    assert refs[1]["quantileBandsSha256"] == content_hash(req["calculations"][1]["quantileBands"])
    assert refs[0]["outputSha256"] == content_hash(req["calculations"][0]["values"])
    assert refs[0]["assumptionRefs"] == [f"sha256:{content_hash(req['calculations'][0]['assumptions'])}"]
    assert b["provenance"]["sourceSnapshotIds"][0].startswith("workspace-run:sc://workspace/runs/synthetic-fig05-band:")
    assert out["source"]["kind"] == "workspace-runtime-records"


def test_band_over_dataset_observations():
    rows = [{"t": r["t"], "y": r["y"]} for r in ROWS]
    req = _runtime_request(calcs=[_band_calc()], panels=[{"panelId": "trend", "chart": "band", "calculation": 0, "xUnit": "years",
                                                          "series": [{"field": "y", "label": "Observed y (synthetic)", "unit": "mg L⁻¹"}]}])
    req["dataset"] = {"datasetId": "synthetic-fig05-rows", "sha256": content_hash(rows), "evidenceClass": "modelled",
                      "rows": rows, "xField": "t", "xLabel": "t"}
    out = _compile(req)
    obs = [t for t in out["plotly"]["figure"]["data"] if t.get("mode") == "markers"]
    assert obs and obs[0]["y"] == [r["y"] for r in rows]
    assert {p["panelId"] for p in out["accessibleAlternative"]["panels"]} == {"trend", "trend.observations"}


def test_compilation_is_deterministic():
    a, b = _compile(_runtime_request()), _compile(_runtime_request())
    assert a["plotly"]["specSha256"] == b["plotly"]["specSha256"] and a["resultHash"] == b["resultHash"]


# --- unavailable, never invented ----------------------------------------------------------------------------------

def test_missing_runtime_record_is_shown_as_unavailable():
    req = _runtime_request(calcs=[_band_calc(bands=None, linearFit=None), _fan_calc(quantileBands=None)])
    out = _compile(req)
    assert not _traces(out, "band") and not _traces(out, "fan")
    assert not any(t.get("fill") for t in out["plotly"]["figure"]["data"])
    notes = [a["text"] for a in out["plotly"]["figure"]["layout"]["annotations"] if "Uncertainty unavailable" in a["text"]]
    assert len(notes) == 2
    panels = {p["panelId"]: p for p in out["accessibleAlternative"]["panels"]}
    assert panels["trend"]["uncertaintyStatus"] == "unavailable" and panels["trend"]["rows"] == []
    assert panels["trend"]["descriptiveSummary"][0].startswith("Uncertainty unavailable: the Workspace run reported no")
    ctx = out["figureBundle"]["scientificContext"]
    assert ctx["uncertaintyStatus"] == "unavailable" and "unavailable-notice" in ctx["uncertaintyEncodings"]
    assert {u["status"] for u in out["uncertainty"]} == {"unavailable"}


# --- refusals ---------------------------------------------------------------------------------------------------

def _bad_band(mutate):
    calc = _band_calc()
    mutate(calc["bands"])
    return _runtime_request(calcs=[calc, _fan_calc()])


def _bad_fan(mutate):
    calc = _fan_calc()
    mutate(calc["quantileBands"])
    return _runtime_request(calcs=[_band_calc(), calc])


@pytest.mark.parametrize("mutate,needle", [
    (lambda b: b[0].update(computedBy="workbench"), "not the runtime's band record"),
    (lambda b: b[0].update(computedBy="computed-by-workbench"), "not the runtime's band record"),
    (lambda b: b[0].pop("degreesOfFreedom"), "not the runtime's band record"),
    (lambda b: b[0].update(distribution="normal"), "Student t"),
    (lambda b: b[0].update(level=0.3), "level"),
    (lambda b: b[0]["points"][2].__setitem__(2, b[0]["points"][2][1] + 1), "lower <= fit <= upper"),
    (lambda b: b[0]["points"][2].__setitem__(3, b[0]["points"][2][3] + 0.01), "not symmetric"),
    (lambda b: b[0]["points"].reverse(), "strictly increasing"),
    (lambda b: b[1].update(level=0.95), "share level"),
    (lambda b: [p.__setitem__(3, p[3] + 0.001 * i) or p.__setitem__(2, p[2] - 0.001 * i) for i, p in enumerate(b[1]["points"])],
     "different residual variances"),
    (lambda b: b.append(copy.deepcopy(b[0])), "one or two"),
])
def test_bands_not_computed_by_the_runtime_or_inconsistent_are_refused(mutate, needle):
    r = c.post("/figure-adapters/plotly/compile", json=_bad_band(mutate))
    assert r.status_code == 422 and needle in r.text


def test_band_fit_must_equal_exported_coefficients():
    calc = _band_calc(values={**FX["band"]["values"], "slope": FX["band"]["values"]["slope"] + 0.01})
    r = c.post("/figure-adapters/plotly/compile", json=_runtime_request(calcs=[calc, _fan_calc()]))
    assert r.status_code == 422 and "intercept + slope" in r.text


@pytest.mark.parametrize("mutate,needle", [
    (lambda q: q.update(computedBy="lab"), "runtime's ensemble-quantile-fan record"),
    (lambda q: q.update(memberCount=4), "member count"),
    (lambda q: q.update(centralLevels=[0.95, 0.8, 0.5]), "increasing"),
    (lambda q: q["steps"][3]["bands"][0].__setitem__(0, q["steps"][3]["median"] + 1), "not nested"),
    (lambda q: q["steps"][3]["bands"][2].__setitem__(1, q["steps"][3]["max"] + 1), "not nested"),
    (lambda q: q["steps"].reverse(), "strictly increasing"),
    (lambda q: q.update(extra=1), "runtime's ensemble-quantile-fan record"),
])
def test_fans_not_computed_by_the_runtime_or_inconsistent_are_refused(mutate, needle):
    r = c.post("/figure-adapters/plotly/compile", json=_bad_fan(mutate))
    assert r.status_code == 422 and needle in r.text


@pytest.mark.parametrize("change,needle", [
    ({"bundle": None}, "observed"),
    ({"panels": [{"panelId": "trend", "chart": "band"}]}, "calculation index"),
    ({"panels": [{"panelId": "trend", "chart": "band", "calculation": 1}]}, "carries the other record"),
    ({"panels": [{"panelId": "trend", "chart": "band", "calculation": 5}]}, "not in calculations"),
    ({"panels": [{"panelId": "trend", "chart": "line", "calculation": 0, "series": [{"field": "y", "unit": "u"}]}]}, "band and fan panels"),
])
def test_request_shape_refusals(change, needle):
    req = _runtime_request()
    if "bundle" in change:
        req["bundle"] = _modelled_bundle(evidenceClass="observed", measurementStatus="observed")
    else:
        req.update(change)
    r = c.post("/figure-adapters/plotly/compile", json=req)
    assert r.status_code == 422 and needle in r.text


def test_assumptions_must_be_the_declared_unchecked_record():
    calc = _band_calc(assumptions={"declaredBy": "workbench", "checked": True, "statements": ["x"]})
    r = c.post("/figure-adapters/plotly/compile", json=_runtime_request(calcs=[calc, _fan_calc()]))
    assert r.status_code == 422 and "assumptions" in r.text


# --- backward compatibility ---------------------------------------------------------------------------------------

def test_existing_figures_are_unchanged_by_fig05():
    out = _compile(_points_request())
    assert "uncertainty" not in out and "uncertaintyComputedByAdapter" not in out["boundaries"]
    ctx = out["figureBundle"]["scientificContext"]
    assert "uncertaintyStatus" not in ctx and "uncertaintyEncodings" not in ctx
    assert all("fill" not in t for t in out["plotly"]["figure"]["data"])
    assert all(r["system"] == "workbench" for r in out["figureBundle"]["calculationRefs"]) or not out["figureBundle"]["calculationRefs"]


# --- map uncertainty layer (MapLibre adapter) ---------------------------------------------------------------------

import base64  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import maplibre_figure_adapter as ml  # noqa: E402

_ml_app = FastAPI()
_ml_app.include_router(ml.router)
mc = TestClient(_ml_app)
MAP_REQ = json.loads((Path(__file__).parent / "fixtures" / "sc_fig05_map_request.json").read_text())


@pytest.fixture
def map_enabled(monkeypatch):
    monkeypatch.setenv(ml.ENABLE_ENV, "1")


def _map_doc():
    return json.loads(base64.b64decode(MAP_REQ["dataset"]["contentBase64"]))


def _map_with(doc=None, **over):
    req = copy.deepcopy(MAP_REQ)
    if doc is not None:
        raw = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        req["dataset"].update(sha256=hashlib.sha256(raw).hexdigest(), contentBase64=base64.b64encode(raw).decode())
    for k, v in over.items():
        req[k] = v
    return req


def _reseal(doc):
    pkg = doc["siPackage"]
    for o in pkg["components"]["evidence_objects"]:
        o["content_digest"] = ml._si_digest({k: v for k, v in o.items() if k != "content_digest"})
    by_id = {o["object_id"]: o["content_digest"] for o in pkg["components"]["evidence_objects"]}
    m = pkg["manifest"]
    for e in m["entries"]:
        if e["group"] == "evidence_objects":
            e["digest"] = by_id[e["entry_id"]]
    m["entries"].sort(key=lambda x: (x["group"], x["entry_id"], x["digest"]))
    m["source_digests"] = sorted({e["digest"] for e in m["entries"]})
    m["manifest_digest"] = ml._si_digest({k: v for k, v in m.items() if k != "manifest_digest"})
    pkg["package_digest"] = ml._si_digest({k: v for k, v in pkg.items() if k not in ml.SI_PACKAGE_UNSEALED})
    for r in doc["rows"]:
        r["content_digest"] = by_id[r["object_id"]]
        o = next(o for o in pkg["components"]["evidence_objects"] if o["object_id"] == r["object_id"])
        r.pop("soc_sd", None)
        if "soc_sd" in o["properties"]:
            r["soc_sd"] = o["properties"]["soc_sd"]
    return doc


def _map_refused(req, needle):
    r = mc.post("/figure-adapters/maplibre/compile", json=req)
    assert r.status_code == 422, r.text
    assert needle in r.text, r.text


def test_map_uncertainty_layer_draws_only_the_runtime_values(map_enabled):
    r = mc.post("/figure-adapters/maplibre/compile", json=MAP_REQ)
    assert r.status_code == 200, r.text
    out = r.json()
    layer = next(l for l in out["maplibre"]["view"]["layers"] if l["id"] == "soc-uncertainty")
    assert layer["encode"] == "uncertainty" and layer["uncertaintyRef"] == 0
    assert "calculations" not in out["maplibre"]["view"]  # the per-field record is not a shown value
    record = MAP_REQ["calculations"][0]["uncertainty"]
    objs = {o["properties"]["field_id"]: o["properties"] for o in out["maplibre"]["view"]["objects"]}
    assert {f: p["soc_sd"] for f, p in objs.items() if "soc_sd" in p} == record["values"]
    assert "soc_sd" not in objs["WX-F6"]  # no runtime value: not reported, never imputed
    b = out["figureBundle"]
    assert b["calculationRefs"][0]["uncertaintySha256"] == content_hash(record)
    assert b["scientificContext"]["uncertaintyStatus"] == "runtime-computed"
    assert b["scientificContext"]["uncertaintyEncodings"] == ["map-uncertainty-layer", "table-columns"]


def test_map_uncertainty_mismatch_with_the_run_is_refused(map_enabled):
    doc = _map_doc()
    o = doc["siPackage"]["components"]["evidence_objects"][1]
    o["properties"]["soc_sd"] = round(o["properties"]["soc_sd"] + 0.01, 6)
    _map_refused(_map_with(_reseal(doc)), "is not the run's value")


def test_map_uncertainty_the_run_did_not_report_is_refused(map_enabled):
    doc = _map_doc()
    o = next(o for o in doc["siPackage"]["components"]["evidence_objects"] if o["properties"]["field_id"] == "WX-F6")
    o["properties"]["soc_sd"] = 1.0
    _map_refused(_map_with(_reseal(doc)), "that the run did not report")


@pytest.mark.parametrize("mutate,needle", [
    (lambda r: r["view"]["layers"][1]["classify"].update(colors=["#d73027", "#fc8d59", "#91bfdb", "#4575b4"]), "ordered run"),
    (lambda r: r["view"]["layers"][1].pop("uncertaintyRef"), "needs encode, uncertaintyRef"),
    (lambda r: r["view"]["fields"]["soc"].update(uncertaintyKind="standard-error"), "declared kind"),
    (lambda r: r["calculations"][0].update(role="value", valueKey="WX-F1"), "map-uncertainty calculation"),
    (lambda r: r["calculations"][0]["uncertainty"].update(computed="workbench"), "declared kind"),
    (lambda r: r["view"]["layers"].pop(1), "no layer draws"),
    (lambda r: r["view"]["fields"]["soc"].pop("uncertainty") and r["view"]["fields"]["soc"].pop("uncertaintyKind"), "declares no uncertainty"),
])
def test_map_uncertainty_layer_refusals(map_enabled, mutate, needle):
    req = copy.deepcopy(MAP_REQ)
    mutate(req)
    _map_refused(req, needle)


def test_fan_is_lightest_outside_and_darkest_inside():
    out = _compile(_runtime_request())
    alphas = [float(t["fillcolor"].split(",")[-1].rstrip(")")) for t in _traces(out, "fan")]  # drawn widest first
    assert alphas == sorted(alphas) and alphas[0] < alphas[-1]
