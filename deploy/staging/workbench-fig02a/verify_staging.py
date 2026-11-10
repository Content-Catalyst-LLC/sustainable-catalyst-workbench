"""Verify a running Workbench FIG-02A staging container over HTTP.

Runs from a workstation against a loopback tunnel to the staging container, so private
acceptance data (SC_DATA_REPO_DIR) is sent only in request bodies and is never copied to the host:

    ssh -N -L 18188:127.0.0.1:18188 <staging host> &
    cd backend && SC_DATA_REPO_DIR=<data checkout> python ../deploy/staging/workbench-fig02a/verify_staging.py \
        http://127.0.0.1:18188

It checks runtime identity, the recovered v10110 package routes, the Plotly runtime probe, and then
replays the FIG-02A HTTP-level tests from backend/tests against the remote service. Tests that patch
the local process (environment flags, the export semaphore, job files on disk) are not remote-capable
and are excluded by name below.
"""
import base64
import json
import os
import sys
import traceback
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))

REMOTE_TESTS = [
    "test_synthetic_points_uncertainty_and_missing_result_are_preserved",
    "test_synthetic_baselines_render_in_separate_panels",
    "test_mixing_measurement_bases_or_units_in_one_panel_is_rejected",
    "test_private_acceptance_fixture_replays_authoritative_data_manifest",
    "test_private_acceptance_sc07_values_equal_published_originals",
    "test_private_acceptance_sc08_keeps_measurement_bases_in_separate_panels",
    "test_private_acceptance_bundles_validate_against_canonical_schema",
    "test_literature_cannot_be_promoted_to_observed",
    "test_hypothetical_dataset_cannot_become_observed_even_with_matching_labels",
    "test_restricted_or_unreviewed_licences_are_refused_outside_local_review",
    "test_authenticated_owner_scope_and_production_are_not_accepted_before_up01",
    "test_dataset_hash_must_match_declared_source",
    "test_uncertainty_semantics_must_be_explicit_and_consistent",
    "test_value_outside_declared_interval_is_rejected",
    "test_unknown_metric_is_rejected",
    "test_lines_cannot_connect_results_with_different_durations",
    "test_untrusted_markup_is_escaped_and_no_remote_assets_are_emitted",
    "test_source_uri_is_never_fetched_and_must_be_https",
    "test_extra_fields_and_control_characters_are_rejected",
    "test_completed_jobs_compile_line_time_series_distribution_and_heatmap",
    "test_workbench_results_cannot_be_labelled_observed_or_literature",
    "test_series_not_composed_by_workbench_is_rejected",
    "test_compilation_is_deterministic",
    "test_static_png_svg_pdf_export_is_hashed_and_matches_spec",
]


class _Response:
    def __init__(self, status, body):
        self.status_code = status
        self.text = body.decode("utf-8", "replace")

    def json(self):
        return json.loads(self.text)


class HttpClient:
    """Minimal stand-in for fastapi.testclient.TestClient (get/post with json=)."""

    def __init__(self, base):
        self.base = base.rstrip("/")

    def _call(self, method, path, payload=None, params=None):
        url = self.base + path
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return _Response(r.status, r.read())
        except urllib.error.HTTPError as e:
            return _Response(e.code, e.read())

    def get(self, path, params=None, **_):
        return self._call("GET", path, params=params)

    def post(self, path, json=None, **_):
        return self._call("POST", path, payload=json)


class _NoopMonkeypatch:
    def setenv(self, *a, **k):
        pass

    def delenv(self, *a, **k):
        pass


_SEQ = iter(range(1, 100000))


# The local helpers seed a fixed project into a fresh temporary store and read the source catalog
# in-process. Against a persistent remote store, seed a unique project per call and read the
# catalog over HTTP; the test bodies and assertions are unchanged.

def remote_seed_jobs(client):
    suffix = f"{os.getpid()}-{next(_SEQ)}"
    project, envkey = f"project-fig02a-staging-{suffix}", f"env-fig02a-staging-{suffix}"
    env = client.post("/research-environment/build", json={"environment": {
        "environmentKey": envkey, "title": "FIG-02A", "projectEntityId": project, "components": []}}).json()
    r = client.post("/research-environment/persistence/save",
                    json={"researchEnvironment": env, "expectedCurrentRevision": 0, "reason": "fig02a-staging-seed"})
    assert r.status_code == 200, r.text
    ws = client.post("/research-projects/build", json={"project": {
        "projectKey": project, "title": "FIG-02A", "activeEnvironmentKey": envkey, "activeEnvironmentRevision": 1}}).json()
    r = client.post("/research-projects/save", json={"workspace": ws, "expectedProjectRevision": 0, "reason": "fig02a-staging-seed"})
    assert r.status_code == 200, r.text
    jobs = []
    for k in (4, 9, 16, 25):
        r = client.post("/execution-console/jobs/prepare", json={
            "projectKey": project, "runtimeKind": "solver", "label": f"k={k}",
            "request": {"problemKind": "root", "problem": {"expression": f"x**2-{k}", "variable": "x", "bracket": [0, k]},
                        "solverKey": "root.brentq"}})
        assert r.status_code == 200, r.text
        jid = r.json()["jobId"]
        r = client.post(f"/execution-console/jobs/{jid}/run", json={"expectedJobRevision": 1, "reason": "fig02a-staging-seed"})
        assert r.status_code == 200, r.text
        jobs.append(jid)
    return project, jobs

def remote_root_metric(client, project):
    catalog = client.get(f"/figure-composer/source-catalog/{project}").json()
    metrics = [m["metric"] for m in catalog["resultMetrics"] if m["presentCount"] == 4]
    return next(m for m in metrics if m.endswith("root") or m.endswith(".x") or "root" in m)


def main(base):
    client = HttpClient(base)
    report = {"base": base, "checks": {}, "tests": {}}

    def check(name, cond, detail=None):
        report["checks"][name] = {"ok": bool(cond), "detail": detail}

    h = client.get("/health").json()
    check("health", h.get("ok") and h.get("version") == "14.0.0", {"version": h.get("version")})
    s = client.get("/v10110/status").json()
    check("v10110.status", s.get("ok") and s.get("version") == "14.0.0", {"version": s.get("version")})
    pkg = client.post("/computational-packages/build",
                      json={"calculation": {"operation": "exact", "expression": "1/3 + 1/6"}}).json()
    check("v10110.build", pkg.get("ok") and pkg["result"]["result"]["exact"] == "1/2", {"packageHash": pkg.get("packageHash")})
    ver = client.post("/computational-packages/verify", json={"package": pkg, "mode": "replay"}).json()
    check("v10110.replay-verify", ver.get("ok") is True)
    v12 = client.get("/v10120/status")
    check("v10120.status", v12.status_code == 200 and v12.json().get("ok") is True, {"status": v12.status_code})
    st = client.get("/figure-adapters/plotly/status", params={"probe": "true"}).json()
    check("plotly.status", st.get("adapterEnabled") and st.get("staticExportEnabled") and st.get("runtimeAvailable")
          and all(st.get("pinnedPackagesMatch", {}).values()) and st.get("plotlyJsVersion") == "3.3.1", st)
    check("plotly.static-export-probe", st.get("staticExportProbe", {}).get("ok") is True, st.get("staticExportProbe"))

    import test_plotly_figure_adapter_fig02a as t
    t.c = client
    t._seed_jobs = lambda: remote_seed_jobs(client)
    t._root_metric = lambda project: remote_root_metric(client, project)
    private = bool(os.getenv("SC_DATA_REPO_DIR"))
    for name in REMOTE_TESTS:
        if name.startswith("test_private_") and not private:
            report["tests"][name] = "NOT_PERFORMED (SC_DATA_REPO_DIR unset)"
            continue
        fn = getattr(t, name)
        try:
            fn(_NoopMonkeypatch()) if fn.__code__.co_argcount else fn()
            report["tests"][name] = "passed"
        except Exception:  # noqa: BLE001 - reported, not swallowed
            report["tests"][name] = "FAILED: " + traceback.format_exc(limit=3)[-600:]

    # Keep the exported files' identity (not their content) as evidence.
    out = client.post("/figure-adapters/plotly/compile", json={**t._points_request(), "staticFormats": ["png", "svg", "pdf"]}).json()
    files = out.get("staticExport", {}).get("files", {})
    report["staticExport"] = {
        "chromeVersion": out.get("staticExport", {}).get("chromeVersion"),
        "specSha256": out.get("plotly", {}).get("specSha256"),
        "files": {k: {"sha256": v["sha256"], "bytes": v["bytes"], "magic": base64.b64decode(v["contentBase64"])[:5].hex()}
                  for k, v in files.items()},
    }
    failed = [k for k, v in report["checks"].items() if not v["ok"]] + \
             [k for k, v in report["tests"].items() if v.startswith("FAILED")]
    report["result"] = "FAIL" if failed else "PASS"
    report["failed"] = failed
    print(json.dumps(report, indent=1, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:18188"))
