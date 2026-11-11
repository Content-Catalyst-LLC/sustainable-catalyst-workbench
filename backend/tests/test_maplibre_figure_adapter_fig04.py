"""SC-FIG-04 MapLibre adapter: SI package verification, row derivation, evidence and licence gates, view and
bundle contract.

``fixtures/fig04_wexford_dataset.json`` is SYNTHETIC: invented Wexford field parcels and hypothetical
monitoring sites, produced by Site Intelligence's own normaliser and sealed in an SI reproducible spatial
package (generator: Lab ``tests/fixtures/fig04-wexford/build_fixtures.py``). It proves adapter behaviour only.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import maplibre_figure_adapter as adapter
from app.v510 import content_hash

app = FastAPI()
app.include_router(adapter.router)
c = TestClient(app)

RAW = (Path(__file__).parent / "fixtures" / "fig04_wexford_dataset.json").read_bytes()
DOC = json.loads(RAW)
SOIL, WATER = "synthetic:fig04-wexford-soil-model", "synthetic:fig04-wexford-nitrate-model"
VALUES = {"intercept": 29.1, "slope": 0.8333, "slope_stdError": 1.8857}


def encode(doc=None, raw=None):
    raw = raw if raw is not None else json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"datasetId": "fig04-wexford", "sha256": hashlib.sha256(raw).hexdigest(),
            "contentBase64": base64.b64encode(raw).decode(), "evidenceClass": "modelled"}


def source(sid, licence="verified-for-use"):
    return {"sourceId": sid, "provider": "Sustainable Catalyst synthetic fixture via Site Intelligence",
            "identityStatus": "source-hash-verified", "qualityStatus": "not-applicable", "licenceStatus": licence,
            "notes": "CC0-1.0 synthetic fixture"}


def reseal(doc):
    """Re-seal an edited package the way SI would (new object, manifest and package digests)."""
    pkg = doc["siPackage"]
    for o in pkg["components"]["evidence_objects"]:
        o["content_digest"] = adapter._si_digest({k: v for k, v in o.items() if k != "content_digest"})
    by_id = {o["object_id"]: o["content_digest"] for o in pkg["components"]["evidence_objects"]}
    m = pkg["manifest"]
    for e in m["entries"]:
        if e["group"] == "evidence_objects":
            e["digest"] = by_id[e["entry_id"]]
    m["entries"].sort(key=lambda x: (x["group"], x["entry_id"], x["digest"]))
    m["source_digests"] = sorted({e["digest"] for e in m["entries"]})
    m["manifest_digest"] = adapter._si_digest({k: v for k, v in m.items() if k != "manifest_digest"})
    pkg["package_digest"] = adapter._si_digest({k: v for k, v in pkg.items() if k not in adapter.SI_PACKAGE_UNSEALED})
    return doc


def request(doc=None):
    return {
        "dataset": encode(doc) if doc is not None else encode(raw=RAW),
        "view": {
            "title": "SYNTHETIC Wexford field soil organic carbon and hypothetical nitrate monitoring",
            "fields": {"field_id": {"label": "Field", "unit": "category"},
                       "soc": {"label": "Soil organic carbon", "unit": "g kg-1", "uncertainty": "soc_se", "uncertaintyKind": "standard-error"},
                       "ph": {"label": "Soil pH", "unit": "1"},
                       "site_id": {"label": "Monitoring site", "unit": "category"},
                       "nitrate_n": {"label": "Nitrate-N", "unit": "mg L-1"}},
            "layers": [
                {"id": "field-soc", "geometry": "polygon", "evidenceClass": "modelled", "legend": "Modelled field soil organic carbon (synthetic)",
                 "style": {"opacity": 0.75, "outlineColor": "#333333", "outlineWidth": 1},
                 "classify": {"field": "soc", "breaks": [26, 29, 32], "colors": ["#edf8e9", "#bae4b3", "#74c476", "#238b45"]}},
                {"id": "nitrate-heat", "geometry": "heatmap", "evidenceClass": "modelled", "legend": "Modelled nitrate-N density (hypothetical sites)",
                 "weight": {"field": "nitrate_n", "max": 15}, "ramp": "magma", "style": {"radius": 40, "intensity": 1, "opacity": 0.7}},
                {"id": "nitrate-sites", "geometry": "point", "evidenceClass": "modelled", "legend": "Hypothetical monitoring sites",
                 "style": {"color": "#1f78b4", "radius": 5}}],
            "time": {"label": "Quarter (synthetic)"},
            "comparison": {"field": "soc", "match": "field_id", "label": "Change in modelled soil organic carbon (synthetic)"},
        },
        "calculations": [{"label": "Soil organic carbon trend (Workspace R lm)", "unit": "g kg-1 yr-1",
                          "method": "lm(soc ~ t_years), 24 field-quarter rows", "runRef": "workspace-run:test",
                          "values": VALUES, "valueKey": "slope", "uncertaintyKey": "slope_stdError", "uncertaintyKind": "standard-error"}],
        "bundle": {"figureId": "SC-FIG-04-WEXFORD", "title": "SYNTHETIC Wexford soil carbon and nitrate map",
                   "projectRef": "research-entry:test", "ownerScope": "isolated-synthetic", "environment": "staging",
                   "evidenceClass": "modelled", "measurementStatus": "computed-from-specified-inputs",
                   "interpretation": "Synthetic map for geospatial pipeline acceptance only.",
                   "limitations": ["Invented field shapes, sites and values"], "doNotInfer": ["any real Wexford value"],
                   "caption": "SYNTHETIC: modelled field SOC classes and hypothetical nitrate density by quarter.",
                   "altText": "Six field parcels shaded by modelled SOC class with eight hypothetical monitoring points.",
                   "sourceRefs": [source(SOIL), source(WATER)]},
    }


@pytest.fixture(autouse=True)
def enabled(monkeypatch):
    monkeypatch.setenv(adapter.ENABLE_ENV, "1")


def compile_ok(req):
    r = c.post("/figure-adapters/maplibre/compile", json=req)
    assert r.status_code == 200, r.text
    return r.json()


def refused(req, status, needle):
    r = c.post("/figure-adapters/maplibre/compile", json=req)
    assert r.status_code == status, r.text
    detail = r.json()["detail"]
    assert needle in (detail if isinstance(detail, str) else json.dumps(detail)), detail


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(adapter.ENABLE_ENV)
    assert c.post("/figure-adapters/maplibre/compile", json=request()).status_code == 503
    s = c.get("/figure-adapters/maplibre/status").json()
    assert s["enabled"] is False and s["approvedTileProviders"] == []


def test_compiles_view_and_bundle_from_verified_si_package():
    out = compile_ok(request())
    view, bundle = out["maplibre"]["view"], out["figureBundle"]
    objects = DOC["siPackage"]["components"]["evidence_objects"]
    assert view["schema"] == "sc-lab-maplibre-view/1.1" and view["objects"] == objects  # SI objects unchanged
    assert out["maplibre"]["specSha256"] == content_hash(view) == bundle["artifacts"][0]["sha256"]
    assert bundle["artifacts"][0]["mediaType"] == "application/vnd.sc.maplibre-view.v1+json"
    assert bundle["figureType"] == "spatial-map" and bundle["spatial"]["crs"] == "EPSG:4326"
    assert bundle["spatial"]["siPackage"]["package_digest"] == DOC["siPackage"]["package_digest"]
    assert bundle["spatial"]["bbox"] == [-6.62, 52.3, -6.388, 52.412]
    assert all(s["sha256"] == hashlib.sha256(RAW).hexdigest() for s in bundle["sourceRefs"])
    assert bundle["calculationRefs"][0]["outputSha256"] == content_hash(VALUES)
    assert view["calculations"][0] == {"label": "Soil organic carbon trend (Workspace R lm)", "value": 0.8333, "unit": "g kg-1 yr-1",
                                       "method": "lm(soc ~ t_years), 24 field-quarter rows", "calculationRef": 0,
                                       "uncertainty": 1.8857, "uncertaintyKind": "standard-error"}
    steps = sorted({o["observed_at"] for o in objects})
    assert view["time"] == {"property": "observed_at", "label": "Quarter (synthetic)", "steps": steps, "initial": steps[-1]}
    assert view["comparison"]["from"] == steps[0] and view["comparison"]["to"] == steps[-1]
    assert view["layers"][0]["where"] == {"property": "evidence_class", "equals": "modelled"}
    assert view["basemap"] is None and "rasterLayers" not in view
    assert bundle["review"] == {k: "pending" for k in ("scientific", "visual", "rights", "sourceIntegrity", "publication")}
    assert bundle["publication"]["bindingStatus"] == "synthetic-test"
    assert out["verification"]["objects"] == 56 and out["verification"]["rowsVerified"] == 24
    assert all(v is False for v in out["boundaries"].values())
    assert len(out["accessibleAlternative"]["rows"]) == 56


def test_compile_is_deterministic_apart_from_time():
    a, b = compile_ok(request()), compile_ok(request())
    assert a["maplibre"]["specSha256"] == b["maplibre"]["specSha256"]


def test_no_url_anywhere_in_the_view():
    text = json.dumps(compile_ok(request())["maplibre"]["view"])
    assert "http" not in text and "{z}" not in text and "tiles" not in text


def test_dataset_bytes_must_match_the_pin():
    req = request()
    req["dataset"]["sha256"] = "0" * 64
    refused(req, 403, "do not match the declared")


def test_edited_si_object_refused():
    doc = copy.deepcopy(DOC)
    doc["siPackage"]["components"]["evidence_objects"][3]["properties"]["soc"] = 99.0
    refused(request(doc), 403, "digest")


def test_object_resealed_without_si_digest_refused():
    doc = copy.deepcopy(DOC)
    o = doc["siPackage"]["components"]["evidence_objects"][3]
    o["properties"]["soc"] = 99.0
    o["content_digest"] = adapter._si_digest({k: v for k, v in o.items() if k != "content_digest"})
    refused(request(doc), 403, "siPackage digest does not match")


def test_row_not_derived_from_its_object_refused():
    doc = copy.deepcopy(DOC)
    doc["rows"][0]["soc"] = doc["rows"][0]["soc"] + 1
    refused(request(doc), 403, "differs from its SI object")
    doc = copy.deepcopy(DOC)
    doc["rows"][1]["object_id"] = "se-not-in-package"
    refused(request(doc), 403, "not in the SI package")
    doc = copy.deepcopy(DOC)
    doc["rows"][2]["content_digest"] = "sha256:" + "0" * 64
    refused(request(doc), 403, "content digest")


def test_restricted_or_undeclared_source_refused():
    req = request()
    req["bundle"]["sourceRefs"][1]["licenceStatus"] = "restricted"
    refused(req, 403, "restricted sources cannot be rendered")
    req = request()
    req["bundle"]["sourceRefs"] = [source(SOIL)]
    refused(req, 403, "without a declared licence status")
    req = request()
    req["bundle"]["sourceRefs"][0]["licenceStatus"] = "pending"
    refused(req, 403, "pending licence review")


def test_no_promotion_to_observed():
    doc = copy.deepcopy(DOC)
    o = doc["siPackage"]["components"]["evidence_objects"][0]
    req = request()
    req["bundle"]["evidenceClass"] = "observed"
    req["bundle"]["measurementStatus"] = "observed"
    refused(req, 422, "cannot be relabelled")
    req["dataset"]["evidenceClass"] = "observed"
    req["bundle"]["sourceRefs"] = [dict(source(SOIL), qualityStatus="pending"), source(WATER)]
    refused(req, 422, "qualified sources")
    assert o["properties"]["evidence_class"] == "modelled"


def test_private_object_refused_even_when_sealed():
    doc = copy.deepcopy(DOC)
    doc["siPackage"]["components"]["evidence_objects"][0]["visibility"] = "private"
    refused(request(reseal(doc)), 403, "not public")


def test_resealed_package_still_needs_rows_derived_from_it():
    doc = copy.deepcopy(DOC)
    o = next(x for x in doc["siPackage"]["components"]["evidence_objects"] if "soc" in x["properties"])
    o["properties"]["soc"] = 99.0
    refused(request(reseal(doc)), 403, "content digest")


def test_manifest_must_list_exactly_the_objects():
    doc = copy.deepcopy(DOC)
    pkg = doc["siPackage"]
    pkg["manifest"]["entries"] = [e for e in pkg["manifest"]["entries"] if e["group"] != "evidence_objects"][:0] + pkg["manifest"]["entries"][1:]
    pkg["manifest"]["manifest_digest"] = adapter._si_digest({k: v for k, v in pkg["manifest"].items() if k != "manifest_digest"})
    pkg["package_digest"] = adapter._si_digest({k: v for k, v in pkg.items() if k not in adapter.SI_PACKAGE_UNSEALED})
    refused(request(doc), 403, "does not list exactly")


def test_view_policy_refusals():
    req = request()
    req["view"]["layers"][0]["classify"]["field"] = "field_id"
    refused(req, 422, "must be numeric")
    req = request()
    req["view"]["layers"][1]["weight"]["field"] = "yield"
    refused(req, 422, "not a declared field")
    req = request()
    req["view"]["layers"] = req["view"]["layers"][:1]
    refused(req, 422, "not drawn by any layer")
    req = request()
    req["view"]["layers"][2]["style"]["color"] = ["get", "x"]
    refused(req, 422, "#rrggbb constant")
    req = request()
    req["view"]["title"] = "Map see https://example.test/tiles"
    refused(req, 422, "URLs")
    req = request()
    req["view"]["comparison"]["fromStep"] = req["view"]["comparison"]["toStep"] = "2026-05-01T00:00:00+00:00"
    refused(req, 422, "earlier first")
    req = request()
    req["calculations"][0]["valueKey"] = "missing"
    refused(req, 422, "not a finite number")
