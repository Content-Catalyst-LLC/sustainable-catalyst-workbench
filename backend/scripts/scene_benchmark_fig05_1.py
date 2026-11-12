"""SC-FIG-05.1 benchmark: resource use and reproducibility of render_mesh on synthetic grid surfaces.

    python scripts/scene_benchmark_fig05_1.py --grid 317 [--runs 2] [--glb] > result.json

Run inside the scene staging image with the container limits under test (for example
``--cpus 1 --memory 1536m --network none``). Each grid n gives n*n vertices and 2(n-1)^2 triangles.
Reports, per run, the worker's own CPU seconds and peak RSS, wall time, the parent's peak RSS, the
container's cgroup memory peak when readable, the scene hash and the PNG pixel difference between runs.
Synthetic geometry only.
"""
import argparse
import base64
import json
import math
import resource
import struct
import sys
import time
import zlib
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import scene_render_adapter as scene  # noqa: E402


def surface(n):
    verts = [[float(i), float(j), 0.2 * math.sin(i * 12 / n) * math.cos(j * 12 / n)] for j in range(n) for i in range(n)]
    faces = []
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            faces += [[a, a + 1, a + n + 1], [a, a + n + 1, a + n]]
    return verts, faces, [v[2] for v in verts]


def pixels(png):
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(png):
        n = struct.unpack(">I", png[pos:pos + 4])[0]
        kind, data = png[pos + 4:pos + 8], png[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h = struct.unpack(">II", data[:8])
        elif kind == b"IDAT":
            idat += data
        pos += 12 + n
    raw = zlib.decompress(idat)
    return [raw[y * (1 + 3 * w) + 1:(y + 1) * (1 + 3 * w)] for y in range(h)]


def cgroup_peak_mib():
    for p in ("/sys/fs/cgroup/memory.peak", "/sys/fs/cgroup/memory/memory.max_usage_in_bytes"):
        try:
            return round(int(Path(p).read_text().strip()) / 1048576, 1)
        except (OSError, ValueError):
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=int, required=True)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--glb", action="store_true")
    ap.add_argument("--cpu", type=float, default=90)
    ap.add_argument("--memory", type=int, default=1536)
    ap.add_argument("--wall", type=float, default=120)
    a = ap.parse_args()
    t0 = time.monotonic()
    verts, faces, scalars = surface(a.grid)
    n = a.grid
    job = {
        "renderer": "pyvista-vtk",
        "meshes": [{"meshId": "surface", "vertices": verts, "faces": faces, "scalars": scalars, "scalarLocation": "vertex",
                    "evidenceClass": "hypothetical"}],
        "scalar": {"field": "z", "unit": "m", "range": [-0.25, 0.25], "colormap": "viridis"},
        "camera": {"position": [n * 1.6, -n * 1.2, n * 1.1], "focalPoint": [n / 2, n / 2, 0.0], "viewUp": [0.0, 0.0, 1.0],
                   "projection": "perspective", "viewAngleDegrees": 30},
        "interpolation": {"surface": "vertex-colour-gouraud", "declaredBy": "workbench-job"},
        "verticalExaggeration": 4.0,
        "budgets": {"cpuSeconds": a.cpu, "memoryMiB": a.memory, "wallSeconds": a.wall, "concurrency": 1},
        "formats": ["png", "glb"] if a.glb else ["png"], "width": 1024, "height": 768,
        "figure": {"figureId": f"synthetic.fig05-1.bench-{n}", "title": "Synthetic benchmark surface",
                   "caption": "Synthetic surface for the SC-FIG-05.1 benchmark.", "altText": "A synthetic wavy surface coloured by height.",
                   "interpretation": "Synthetic geometry; no scientific meaning.", "limitations": ["Synthetic values"],
                   "projectRef": "synthetic-fig05-1", "calculationRef": f"sc://workbench/jobs/synthetic-bench-{n}@1",
                   "calculationMethod": "analytic synthetic surface", "sourceId": "synthetic", "sourceProvider": "SC-FIG-05.1 benchmark"},
    }
    # Same path as the HTTP route: bytes parsed and validated by pydantic directly.
    body = json.dumps(job).encode("utf-8")
    del job, verts, faces, scalars
    payload_bytes = len(body)
    try:
        model = scene.MeshRenderJob.model_validate_json(body)
    except ValidationError as exc:
        print(json.dumps({"grid": n, "vertices": n * n, "payloadBytes": payload_bytes, "refused": True,
                          "reason": exc.errors(include_url=False, include_context=False, include_input=False)[0]["msg"],
                          "parentPeakRssMiB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                          "containerPeakMiB": cgroup_peak_mib()}))
        return
    del body
    validate_s = round(time.monotonic() - t0, 3)
    runs, first = [], None
    for _ in range(a.runs):
        t = time.monotonic()
        try:
            out = scene.render_mesh(model)
        except (RuntimeError, ValueError) as exc:
            runs.append({"ok": False, "error": str(exc), "wallSeconds": round(time.monotonic() - t, 3)})
            continue
        png = base64.b64decode(out["files"]["png"]["contentBase64"])
        rec = {"ok": True, "sceneSha256": out["scene"]["sceneSha256"], "pngSha256": out["files"]["png"]["sha256"],
               "glbSha256": out["files"].get("glb", {}).get("sha256"), "glbBytes": out["files"].get("glb", {}).get("bytes"),
               "renderWindow": out["renderer"]["renderWindow"], **out["usage"], "endToEndSeconds": round(time.monotonic() - t, 3)}
        rows = pixels(png)
        if first is None:
            first = rows
        else:
            total = sum(abs(x - y) for ra, rb in zip(first, rows) for x, y in zip(ra, rb))
            rec["meanAbsRgbVsRun1"] = round(total / sum(len(r) for r in rows), 6)
            rec["maxAbsRgbVsRun1"] = max((abs(x - y) for ra, rb in zip(first, rows) for x, y in zip(ra, rb)), default=0)
        runs.append(rec)
    ok = [r for r in runs if r["ok"]]
    print(json.dumps({
        "grid": n, "vertices": n * n, "faces": 2 * (n - 1) ** 2, "payloadBytes": payload_bytes, "validateSeconds": validate_s,
        "budgets": model.budgets.model_dump(), "maxVertices": scene.MAX_VERTICES, "runs": runs,
        "reproducible": bool(ok) and len({r["sceneSha256"] for r in ok}) == 1 and all(r.get("meanAbsRgbVsRun1", 0) <= 1.0 for r in ok),
        "identicalPng": bool(ok) and len({r["pngSha256"] for r in ok}) == 1,
        "parentPeakRssMiB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "containerPeakMiB": cgroup_peak_mib(),
    }))


if __name__ == "__main__":
    main()
