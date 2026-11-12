"""SC-FIG-05.1 Workbench: bounded, reproducible static 3D scene rendering (PyVista/VTK, off-screen).

Validation, hashing, budget, network and concurrency checks run everywhere. Rendering checks run only
where the pinned PyVista/VTK are installed with an off-screen OpenGL (the staging scene image); they
are skipped elsewhere and reported as skipped, never as passed. Synthetic meshes only.
"""
import base64
import copy
import importlib.util
import math
import signal
import socket
import struct
import zlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import mesh_render_worker as worker
from app import scene_render_adapter as scene
from app.v510 import content_hash

HAS_RENDERER = importlib.util.find_spec("pyvista") is not None and importlib.util.find_spec("vtk") is not None
needs_renderer = pytest.mark.skipif(not HAS_RENDERER, reason="pinned PyVista/VTK not installed (scene staging image only)")


def synthetic_surface(n=11, location="vertex", mesh_id="surface"):
    """A synthetic n x n grid surface z = 0.2 sin(x) cos(y), triangulated, with z as the scalar."""
    verts = [[float(i), float(j), 0.2 * math.sin(i / 2) * math.cos(j / 2)] for j in range(n) for i in range(n)]
    faces = []
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            faces += [[a, a + 1, a + n + 1], [a, a + n + 1, a + n]]
    if location == "vertex":
        scalars = [v[2] for v in verts]
    else:
        scalars = [sum(verts[k][2] for k in f) / 3 for f in faces]
    return {"meshId": mesh_id, "vertices": verts, "faces": faces, "scalars": scalars, "scalarLocation": location,
            "evidenceClass": "hypothetical"}


def job(**kw):
    n = kw.pop("n", 11)
    j = {
        "renderer": "pyvista-vtk",
        "meshes": [synthetic_surface(n)],
        "scalar": {"field": "z", "unit": "m", "range": [-0.25, 0.25], "colormap": "viridis"},
        "camera": {"position": [n * 1.6, -n * 1.2, n * 1.1], "focalPoint": [n / 2, n / 2, 0.0], "viewUp": [0.0, 0.0, 1.0],
                   "projection": "perspective", "viewAngleDegrees": 30},
        "interpolation": {"surface": "vertex-colour-gouraud", "declaredBy": "workbench-job"},
        "verticalExaggeration": 4.0,
        "coordinateSystem": {"kind": "local-cartesian", "units": "m"},
        "budgets": {"cpuSeconds": 60, "memoryMiB": 1536, "wallSeconds": 90, "concurrency": 1},
        "pixelTolerance": {"metric": "mean-absolute-rgb", "max": 1.0},
        "formats": ["png"],
        "width": 640, "height": 480,
        "figure": {"figureId": "synthetic.fig05-1.surface", "title": "Synthetic surface", "caption": "Synthetic surface for SC-FIG-05.1 tests.",
                   "altText": "A synthetic wavy surface coloured by height.", "interpretation": "Synthetic geometry; no scientific meaning.",
                   "limitations": ["Synthetic values"], "projectRef": "synthetic-fig05-1", "calculationRef": "sc://workbench/jobs/synthetic-surface@1",
                   "calculationMethod": "analytic synthetic surface", "sourceId": "synthetic", "sourceProvider": "SC-FIG-05.1 tests"},
    }
    j.update(kw)
    return j


def model(**kw):
    return scene.MeshRenderJob.model_validate(job(**kw))


def refused(j, text):
    with pytest.raises(ValidationError) as exc:
        scene.MeshRenderJob.model_validate(j)
    assert text in str(exc.value), str(exc.value)


# --- validation (no renderer needed) -------------------------------------------------------------

def test_valid_job_is_accepted_and_ceilings_match_the_owner_direction():
    model()
    assert scene.CEILINGS == {"cpuSeconds": 90, "memoryMiB": 1536, "wallSeconds": 120, "concurrency": 1}


def test_undeclared_interpolation_is_refused():
    j = job(); del j["interpolation"]
    refused(j, "interpolation")
    j = job(); j["interpolation"] = {"surface": "smooth-whatever"}
    refused(j, "surface")


def test_unknown_renderer_is_refused():
    refused(job(renderer="three-js"), "renderer")


@pytest.mark.parametrize("key,value", [("cpuSeconds", 91), ("memoryMiB", 1537), ("wallSeconds", 121)])
def test_budget_above_the_staging_ceiling_is_refused(key, value):
    j = job(); j["budgets"][key] = value
    refused(j, "exceeds the staging ceiling")


def test_concurrency_other_than_one_is_refused():
    j = job(); j["budgets"]["concurrency"] = 2
    refused(j, "concurrency must be 1")


def test_png_view_is_mandatory():
    refused(job(formats=["glb"]), "PNG view is mandatory")


def test_scalars_outside_the_declared_range_are_refused_not_clipped():
    j = job(); j["scalar"]["range"] = [-0.1, 0.1]
    refused(j, "refused, not clipped")


def test_decreasing_range_nonfinite_vertex_and_bad_face_are_refused():
    j = job(); j["scalar"]["range"] = [0.3, -0.3]
    refused(j, "increasing")
    j = job(); j["meshes"][0]["vertices"][3][1] = float("nan")
    refused(j, "finite")
    j = job(); j["meshes"][0]["faces"][0] = [0, 0, 1]
    refused(j, "three distinct vertex indices")
    j = job(); j["meshes"][0]["faces"][0] = [0, 1, 10_000]
    refused(j, "three distinct vertex indices")


def test_interpolation_must_match_where_scalars_live():
    j = job(); j["interpolation"]["surface"] = "none-flat-faces"
    refused(j, "one scalar per face")
    j = job(meshes=[synthetic_surface(location="face")])
    refused(j, "one scalar per vertex")
    model(meshes=[synthetic_surface(location="face")], interpolation={"surface": "none-flat-faces", "declaredBy": "workbench-job"})


def test_camera_must_look_somewhere_and_coordinates_must_be_declared():
    j = job(); j["camera"]["position"] = j["camera"]["focalPoint"]
    refused(j, "must differ")
    j = job(); j["camera"]["viewUp"] = [0, 1]
    refused(j, "three finite numbers")
    j = job(coordinateSystem={"kind": "projected-crs", "units": "m"})
    refused(j, "needs crs")


def test_mixed_evidence_and_duplicate_meshes_are_refused():
    other = synthetic_surface(mesh_id="second"); other["evidenceClass"] = "observed"
    refused(job(meshes=[synthetic_surface(), other]), "one evidence class")
    refused(job(meshes=[synthetic_surface(), synthetic_surface()]), "unique")


def test_declared_mesh_hash_mismatch_refuses_the_job():
    j = job(); j["meshes"][0]["verticesSha256"] = "0" * 64
    with pytest.raises(ValueError, match="verticesSha256 does not match"):
        scene.render_mesh(scene.MeshRenderJob.model_validate(j))


def test_vertex_limit_is_the_measured_one_and_oversize_bodies_are_refused(monkeypatch):
    assert scene.MAX_VERTICES == 500_000 and scene.MAX_FACES == 1_000_000
    a, b = synthetic_surface(mesh_id="a"), synthetic_surface(mesh_id="b")
    monkeypatch.setattr(scene, "MAX_VERTICES", 200)
    refused(job(meshes=[a, b]), "at most 200 vertices")
    monkeypatch.setenv(scene.ENABLE_ENV, "true")
    monkeypatch.setattr(scene, "MAX_BODY_BYTES", 1000)
    assert _client().post("/figure-adapters/scene/render", json=job()).status_code == 413


# --- hashing and the scene record ----------------------------------------------------------------

def test_mesh_hashes_are_canonical_and_type_normalised():
    m = model().meshes[0]
    h = scene.mesh_hashes(m)
    assert h["verticesSha256"] == content_hash([[float(x) for x in v] for v in m.vertices])
    ints = copy.deepcopy(job()); ints["meshes"][0]["vertices"][0] = [0, 0, 0]
    assert scene.mesh_hashes(scene.MeshRenderJob.model_validate(ints).meshes[0])["verticesSha256"] == h["verticesSha256"]


def test_scene_hash_recomputes_and_any_edit_is_detected():
    j = model()
    rec = scene.build_scene(j, {m.meshId: scene.mesh_hashes(m) for m in j.meshes}, "pyvista 0.45.2; vtk 9.4.2")
    scene.verify_scene(rec)
    assert rec["sceneSha256"] == scene.build_scene(j, {m.meshId: scene.mesh_hashes(m) for m in j.meshes}, "pyvista 0.45.2; vtk 9.4.2")["sceneSha256"]
    assert rec["renderer"] == {"name": "pyvista-vtk", "version": "pyvista 0.45.2; vtk 9.4.2", "offscreen": True, "network": "none"}
    for edit in (lambda r: r["camera"]["position"].__setitem__(0, 99.0), lambda r: r["meshes"][0].update(facesSha256="1" * 64),
                 lambda r: r.update(verticalExaggeration=1.0), lambda r: r["scalar"].update(colormap="magma")):
        tampered = copy.deepcopy(rec); edit(tampered)
        with pytest.raises(ValueError, match="does not match"):
            scene.verify_scene(tampered)


# --- isolation, budgets and concurrency ----------------------------------------------------------

def test_worker_refuses_network_once_denied(monkeypatch):
    for name in ("connect", "connect_ex", "bind", "sendto"):
        monkeypatch.setattr(socket.socket, name, getattr(socket.socket, name))
    for name in ("create_connection", "getaddrinfo", "gethostbyname"):
        monkeypatch.setattr(socket, name, getattr(socket, name))
    worker.deny_network()
    with pytest.raises(worker.NetworkDenied):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
    with pytest.raises(worker.NetworkDenied):
        socket.getaddrinfo("example.invalid", 443)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(worker.NetworkDenied):
            s.connect(("192.0.2.1", 80))
    finally:
        s.close()


def test_worker_environment_carries_no_inherited_credentials(monkeypatch):
    monkeypatch.setenv("SCWB_SECRET_TOKEN", "x")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid")
    env = scene._worker_env("/tmp/h")
    assert "SCWB_SECRET_TOKEN" not in env and "HTTPS_PROXY" not in env
    assert env["VTK_DEFAULT_OPENGL_WINDOW"] == "vtkOSOpenGLRenderWindow" and env["PYVISTA_OFFSCREEN"] == "true"


def test_a_second_concurrent_render_is_refused_not_queued():
    assert scene._RENDER_SLOT.acquire(blocking=False)
    try:
        assert scene.run_worker({}, model().budgets) == {"ok": False, "error": "render-busy"}
    finally:
        scene._RENDER_SLOT.release()


def test_exit_classification():
    assert scene.classify_exit(-signal.SIGXCPU, {}) == "cpu-budget-exceeded"
    assert scene.classify_exit(-signal.SIGKILL, {}) == "render-killed"
    assert scene.classify_exit(0, {"ok": False, "error": "memory-budget-exceeded"}) == "memory-budget-exceeded"
    assert scene.classify_exit(1, {}) == "render-worker-failed"


def test_png_encoder_is_deterministic_and_valid():
    rgb = bytes(range(256)) * 9  # 48 x 16 pixels
    a, b = worker.png_bytes(rgb, 48, 16), worker.png_bytes(rgb, 48, 16)
    assert a == b and a.startswith(scene.PNG_MAGIC)
    ihdr = a[8:33]
    assert struct.unpack(">II", ihdr[8:16]) == (48, 16)
    idat_len = struct.unpack(">I", a[33:37])[0]
    raw = zlib.decompress(a[41:41 + idat_len])
    assert len(raw) == 16 * (1 + 48 * 3) and b"tEXt" not in a and b"tIME" not in a


def _client():
    app = FastAPI()
    app.include_router(scene.router)
    return TestClient(app)


def test_gltf_is_packed_into_a_self_contained_glb():
    payload = base64.b64encode(bytes(range(10))).decode("ascii")
    doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 10, "uri": "data:application/octet-stream;base64," + payload},
                                                     {"byteLength": 3, "uri": "data:application/octet-stream;base64," + base64.b64encode(b"abc").decode()}],
           "bufferViews": [{"buffer": 0, "byteLength": 10}, {"buffer": 1, "byteOffset": 1, "byteLength": 2}]}
    glb = worker.gltf_to_glb(copy.deepcopy(doc))
    assert glb == worker.gltf_to_glb(copy.deepcopy(doc))
    magic, version, length = struct.unpack("<4sII", glb[:12])
    assert (magic, version, length) == (b"glTF", 2, len(glb))
    jlen = struct.unpack("<I", glb[12:16])[0]
    packed = __import__("json").loads(glb[20:20 + jlen])
    assert packed["buffers"] == [{"byteLength": 16}] and packed["bufferViews"][1] == {"buffer": 0, "byteOffset": 13, "byteLength": 2}
    blob = glb[20 + jlen + 8:]
    assert blob[:10] == bytes(range(10)) and blob[13:15] == b"bc"
    doc["buffers"][1]["uri"] = "https://example.invalid/b.bin"
    with pytest.raises(ValueError, match="not inline"):
        worker.gltf_to_glb(doc)


def test_route_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv(scene.ENABLE_ENV, raising=False)
    c = _client()
    assert c.post("/figure-adapters/scene/render", json=job()).status_code == 503
    st = c.get("/figure-adapters/scene/status").json()
    assert st["adapterEnabled"] is False and st["contractStatus"] == "proposed-owner-review" and st["publicationPerformed"] is False


def test_route_refuses_invalid_jobs_with_422(monkeypatch):
    monkeypatch.setenv(scene.ENABLE_ENV, "true")
    j = job(); del j["camera"]
    assert _client().post("/figure-adapters/scene/render", json=j).status_code == 422


# --- rendering (scene staging image only) -------------------------------------------------------

def _pixels(png):
    import numpy as np
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(png):
        n = struct.unpack(">I", png[pos:pos + 4])[0]
        kind, data = png[pos + 4:pos + 8], png[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h = struct.unpack(">II", data[:8])
        elif kind == b"IDAT":
            idat += data
        pos += 12 + n
    raw = np.frombuffer(zlib.decompress(idat), dtype=np.uint8).reshape(h, 1 + w * 3)
    return raw[:, 1:].reshape(h, w, 3).astype(int)


@needs_renderer
def test_render_is_reproducible_within_the_declared_pixel_tolerance(monkeypatch):
    import numpy as np
    monkeypatch.setenv(scene.ENABLE_ENV, "true")
    first, second = scene.render_mesh(model()), scene.render_mesh(model())
    assert first["scene"]["sceneSha256"] == second["scene"]["sceneSha256"]
    scene.verify_scene(first["scene"])
    a, b = _pixels(base64.b64decode(first["files"]["png"]["contentBase64"])), _pixels(base64.b64decode(second["files"]["png"]["contentBase64"]))
    assert a.shape == (480, 640, 3)
    assert float(np.abs(a - b).mean()) <= first["scene"]["pixelTolerance"]["max"]
    assert len(np.unique(a.reshape(-1, 3), axis=0)) > 50  # a coloured surface was drawn, not a blank frame
    assert first["renderer"]["renderWindow"] in {"vtkOSOpenGLRenderWindow", "vtkEGLRenderWindow"}
    assert first["usage"]["peakRssMiB"] <= 1536 and first["usage"]["cpuSeconds"] <= 60
    b = first["figureBundle"]
    assert b["figureType"] == "scene-3d" and b["scene"] == first["scene"] and b["artifacts"][0]["format"] == "png"
    assert b["publication"]["kind"] == "none" and all(v == "pending" for v in b["review"].values())


@needs_renderer
def test_flat_faces_and_glb_export():
    out = scene.render_mesh(model(meshes=[synthetic_surface(location="face")], formats=["png", "glb"],
                                  interpolation={"surface": "none-flat-faces", "declaredBy": "workbench-job"}))
    assert base64.b64decode(out["files"]["glb"]["contentBase64"]).startswith(b"glTF")
    again = scene.render_mesh(model(meshes=[synthetic_surface(location="face")], formats=["png", "glb"],
                                    interpolation={"surface": "none-flat-faces", "declaredBy": "workbench-job"}))
    assert again["files"]["glb"]["sha256"] == out["files"]["glb"]["sha256"]
    assert [a["format"] for a in out["figureBundle"]["artifacts"]] == ["png", "glb"]


@needs_renderer
def test_cpu_memory_and_wall_budgets_are_enforced():
    big = dict(n=301)
    j = job(**big); j["budgets"]["cpuSeconds"] = 1
    with pytest.raises(RuntimeError, match="cpu-budget-exceeded"):
        scene.render_mesh(scene.MeshRenderJob.model_validate(j))
    j = job(); j["budgets"]["memoryMiB"] = 128
    with pytest.raises(RuntimeError, match="memory-budget-exceeded"):
        scene.render_mesh(scene.MeshRenderJob.model_validate(j))
    j = job(**big); j["budgets"]["wallSeconds"] = 0.5
    with pytest.raises(RuntimeError, match="wall-budget-exceeded"):
        scene.render_mesh(scene.MeshRenderJob.model_validate(j))
