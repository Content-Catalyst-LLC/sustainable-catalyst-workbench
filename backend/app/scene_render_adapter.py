"""SC-FIG-05.1 — default-disabled, bounded static 3D mesh rendering (PyVista/VTK, off-screen).

``render_mesh(job)`` validates a declared mesh job, renders it in an isolated worker process under
CPU-time, memory, wall-clock and concurrency budgets with no network, and returns:

* a PNG view (always) and an optional binary glTF (GLB) export,
* a ``scene`` record (``sc.scene-3d.v0-proposed``) whose ``sceneSha256`` is the canonical SHA-256 of
  the record without that field; mesh, face and scalar arrays are hashed the same way,
* a ``figureType: scene-3d`` figure bundle for private review only.

The scene contract is a proposal under owner review. Nothing here approves it, publishes a figure or
infers values: interpolation, camera, scalar range, colormap and units are declared by the job and
refused when missing. Scalars outside the declared range are refused rather than clipped.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import resource
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .release import APP_VERSION
from .v510 import content_hash

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scene-render/0.1"
BUILD_ID = "FIG-05.1"
SCENE_SCHEMA = "sc.scene-3d.v0-proposed"
BUNDLE_SCHEMA = "sc.figure-bundle.v1"
ENABLE_ENV = "SCWB_SCENE_ADAPTER_ENABLED"
PINNED_PACKAGES = {"pyvista": "0.45.2", "vtk": "9.4.2"}
WORKER_PATH = Path(__file__).with_name("mesh_render_worker.py")
# Provisional ceilings accepted for isolated staging (owner direction 2026-11-12); jobs may ask for less.
CEILINGS = {"cpuSeconds": 90, "memoryMiB": 1536, "wallSeconds": 120, "concurrency": 1}
# Measured 2026-11-12 under the ceilings: a 500k-vertex job peaks at about 1240 MiB for the whole container
# (request parsing plus worker); 1M vertices is killed for memory. The proposed contract allows 2M per mesh;
# this job limit is narrower until arrays are transported in binary rather than JSON.
MAX_VERTICES = 500_000
MAX_FACES = 1_000_000
MAX_BODY_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 50_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
GLB_MAGIC = b"glTF"
MEDIA = {"png": "image/png", "glb": "model/gltf-binary"}
# One render at a time per Workbench process; excess requests are refused, not queued.
_RENDER_SLOT = threading.BoundedSemaphore(CEILINGS["concurrency"])
router = APIRouter(tags=["workbench-fig-05-1-scene-render"])

Vec3 = List[float]
EvidenceClass = Literal["observed", "literature-derived", "modelled", "hypothetical", "conceptual", "status-only"]


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _vec3(value: List[float], where: str) -> List[float]:
    if len(value) != 3 or not all(math.isfinite(v) for v in value):
        raise ValueError(f"{where} must be three finite numbers")
    return [float(v) for v in value]


class MeshInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meshId: str = Field(pattern=r"^[a-z][a-z0-9-]{0,47}$")
    vertices: List[List[float]] = Field(min_length=3, max_length=MAX_VERTICES)
    faces: List[List[int]] = Field(min_length=1, max_length=MAX_FACES)
    scalars: Optional[List[float]] = None
    scalarLocation: Literal["vertex", "face"] = "vertex"
    evidenceClass: EvidenceClass
    # Optional hashes the caller already holds; any mismatch refuses the job.
    verticesSha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    facesSha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    scalarsSha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ScalarSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1, max_length=120)
    unit: str = Field(min_length=1, max_length=60)
    range: List[float] = Field(min_length=2, max_length=2)
    colormap: Literal["viridis", "cividis", "magma", "inferno", "greys"]


class CameraSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position: Vec3
    focalPoint: Vec3
    viewUp: Vec3
    projection: Literal["perspective", "parallel"]
    viewAngleDegrees: Optional[float] = Field(default=None, gt=0, le=120)


class InterpolationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    surface: Literal["none-flat-faces", "vertex-colour-gouraud"]
    declaredBy: Literal["workbench-job", "model-revision"] = "workbench-job"


class Budgets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cpuSeconds: float = Field(gt=0)
    memoryMiB: int = Field(ge=64)
    wallSeconds: float = Field(gt=0)
    concurrency: int = 1


class PixelTolerance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric: Literal["mean-absolute-rgb", "max-absolute-rgb"] = "mean-absolute-rgb"
    max: float = Field(default=1.0, ge=0, le=16)


class SceneFigure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    figureId: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,119}$")
    version: int = Field(default=1, ge=1)
    title: str = Field(min_length=3, max_length=200)
    caption: str = Field(min_length=10, max_length=600)
    altText: str = Field(min_length=10, max_length=600)
    interpretation: str = Field(min_length=10, max_length=1200)
    limitations: List[str] = Field(min_length=1, max_length=12)
    projectRef: str = Field(min_length=1, max_length=120)
    calculationRef: str = Field(min_length=1, max_length=240, description="The run that produced the mesh")
    calculationMethod: str = Field(min_length=3, max_length=240)
    sourceId: str = Field(min_length=1, max_length=120)
    sourceProvider: str = Field(min_length=1, max_length=200)


class MeshRenderJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    renderer: Literal["pyvista-vtk"]
    meshes: List[MeshInput] = Field(min_length=1, max_length=16)
    scalar: ScalarSpec
    camera: CameraSpec
    interpolation: InterpolationSpec
    verticalExaggeration: float = Field(gt=0, le=100)
    coordinateSystem: Dict[str, str] = Field(default_factory=lambda: {"kind": "local-cartesian", "units": "m"})
    budgets: Budgets
    pixelTolerance: PixelTolerance = Field(default_factory=PixelTolerance)
    formats: List[Literal["png", "glb"]] = Field(default_factory=lambda: ["png"])
    width: int = Field(default=1024, ge=320, le=2048)
    height: int = Field(default=768, ge=240, le=2048)
    figure: SceneFigure

    @model_validator(mode="after")
    def _check(self):
        if "png" not in self.formats:
            raise ValueError("a PNG view is mandatory for a scene")
        b = self.budgets
        for key in ("cpuSeconds", "memoryMiB", "wallSeconds"):
            if getattr(b, key) > CEILINGS[key]:
                raise ValueError(f"budgets.{key} {getattr(b, key)} exceeds the staging ceiling {CEILINGS[key]}")
        if b.concurrency != 1:
            raise ValueError("budgets.concurrency must be 1")
        lo, hi = self.scalar.range
        if not (math.isfinite(lo) and math.isfinite(hi) and lo < hi):
            raise ValueError("scalar.range must be two finite, increasing numbers")
        for where in ("position", "focalPoint", "viewUp"):
            _vec3(getattr(self.camera, where), f"camera.{where}")
        if self.camera.position == self.camera.focalPoint:
            raise ValueError("camera.position and camera.focalPoint must differ")
        if self.coordinateSystem.get("kind") not in {"local-cartesian", "projected-crs"} or not self.coordinateSystem.get("units"):
            raise ValueError("coordinateSystem needs kind local-cartesian or projected-crs and units")
        if self.coordinateSystem["kind"] == "projected-crs" and not self.coordinateSystem.get("crs"):
            raise ValueError("a projected-crs coordinate system needs crs")
        ids = [m.meshId for m in self.meshes]
        if len(set(ids)) != len(ids):
            raise ValueError("meshId values must be unique")
        if sum(len(m.vertices) for m in self.meshes) > MAX_VERTICES:
            raise ValueError(f"a scene may carry at most {MAX_VERTICES} vertices")
        if len({m.evidenceClass for m in self.meshes}) != 1:
            raise ValueError("meshes in one scene must share one evidence class")
        if not any(m.scalars is not None for m in self.meshes):
            raise ValueError("at least one mesh must carry the declared scalar field")
        for m in self.meshes:
            _check_mesh(m, self)
        return self


def _check_mesh(m: MeshInput, job: MeshRenderJob) -> None:
    n = len(m.vertices)
    for i, v in enumerate(m.vertices):
        if len(v) != 3 or not all(math.isfinite(x) for x in v):
            raise ValueError(f"mesh {m.meshId}: vertex {i} must be three finite numbers")
    for i, f in enumerate(m.faces):
        if len(f) != 3 or len(set(f)) != 3 or not all(0 <= k < n for k in f):
            raise ValueError(f"mesh {m.meshId}: face {i} must be a triangle of three distinct vertex indices")
    if m.scalars is None:
        return
    expected = n if m.scalarLocation == "vertex" else len(m.faces)
    if len(m.scalars) != expected:
        raise ValueError(f"mesh {m.meshId}: {len(m.scalars)} scalars for {expected} {m.scalarLocation} locations")
    if job.interpolation.surface == "none-flat-faces" and m.scalarLocation != "face":
        raise ValueError(f"mesh {m.meshId}: none-flat-faces needs one scalar per face (no interpolation across faces)")
    if job.interpolation.surface == "vertex-colour-gouraud" and m.scalarLocation != "vertex":
        raise ValueError(f"mesh {m.meshId}: vertex-colour-gouraud needs one scalar per vertex")
    lo, hi = job.scalar.range
    for i, s in enumerate(m.scalars):
        if not math.isfinite(s):
            raise ValueError(f"mesh {m.meshId}: scalar {i} must be finite")
        if s < lo or s > hi:
            raise ValueError(f"mesh {m.meshId}: scalar {i} ({s}) lies outside the declared range; it is refused, not clipped")


def mesh_hashes(m: MeshInput) -> Dict[str, str]:
    """Canonical SHA-256 of the vertex (float), face (int) and scalar (float) arrays as submitted."""
    out = {"verticesSha256": content_hash([[float(x) for x in v] for v in m.vertices]),
           "facesSha256": content_hash([[int(k) for k in f] for f in m.faces])}
    if m.scalars is not None:
        out["scalarsSha256"] = content_hash([float(s) for s in m.scalars])
    return out


def scene_sha256(scene: Dict[str, Any]) -> str:
    return content_hash({k: v for k, v in scene.items() if k != "sceneSha256"})


def verify_scene(scene: Dict[str, Any]) -> None:
    if scene.get("sceneSchema") != SCENE_SCHEMA:
        raise ValueError(f"scene record must declare {SCENE_SCHEMA}")
    if scene.get("sceneSha256") != scene_sha256(scene):
        raise ValueError("scene.sceneSha256 does not match the canonical scene record")


def build_scene(job: MeshRenderJob, hashes: Dict[str, Dict[str, str]], renderer_version: str) -> Dict[str, Any]:
    scene: Dict[str, Any] = {
        "sceneSchema": SCENE_SCHEMA,
        "coordinateSystem": dict(job.coordinateSystem),
        "meshes": [{"meshId": m.meshId, "vertexCount": len(m.vertices), "faceCount": len(m.faces),
                    **hashes[m.meshId], "evidenceClass": m.evidenceClass} for m in job.meshes],
        "scalar": {"field": job.scalar.field, "unit": job.scalar.unit, "range": [float(x) for x in job.scalar.range],
                   "colormap": job.scalar.colormap},
        "camera": {k: v for k, v in job.camera.model_dump().items() if v is not None},
        "interpolation": job.interpolation.model_dump(),
        "verticalExaggeration": float(job.verticalExaggeration),
        "renderer": {"name": "pyvista-vtk", "version": renderer_version, "offscreen": True, "network": "none"},
        "budgets": {"cpuSeconds": job.budgets.cpuSeconds, "memoryMiB": job.budgets.memoryMiB,
                    "wallSeconds": job.budgets.wallSeconds, "concurrency": 1},
        "pixelTolerance": job.pixelTolerance.model_dump(),
    }
    scene["sceneSha256"] = scene_sha256(scene)
    return scene


def _worker_env(home: str) -> Dict[str, str]:
    # Single-threaded software rendering; no inherited credentials, proxies or display.
    return {"PATH": os.getenv("PATH", "/usr/bin:/bin"), "HOME": home, "TMPDIR": home, "LANG": "C.UTF-8",
            "MPLCONFIGDIR": home, "PYVISTA_OFFSCREEN": "true", "VTK_DEFAULT_OPENGL_WINDOW": "vtkOSOpenGLRenderWindow",
            "LP_NUM_THREADS": "0", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "PYTHONHASHSEED": "0"}


def _limits(budgets: Budgets):
    cpu = max(1, math.ceil(budgets.cpuSeconds))
    memory = budgets.memoryMiB * 1024 * 1024

    def apply():
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 2))
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


def classify_exit(returncode: int, result: Dict[str, Any]) -> str:
    if returncode in (-signal.SIGXCPU, -signal.SIGKILL) and not result:
        return "cpu-budget-exceeded" if returncode == -signal.SIGXCPU else "render-killed"
    return result.get("error") or ("memory-budget-exceeded" if returncode in (-signal.SIGSEGV, -signal.SIGABRT) else "render-worker-failed")


def run_worker(payload: Dict[str, Any], budgets: Budgets) -> Dict[str, Any]:
    """Render in a separate isolated Python process under the job's budgets; refuse, never queue."""
    if not _RENDER_SLOT.acquire(blocking=False):
        return {"ok": False, "error": "render-busy"}
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="scwb-scene-") as home:
            try:
                proc = subprocess.Popen([sys.executable, "-I", str(WORKER_PATH)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_worker_env(home), cwd=home,
                                        preexec_fn=_limits(budgets), start_new_session=True)
            except (subprocess.SubprocessError, OSError):
                # A host that cannot apply the CPU and memory limits never renders without them.
                return {"ok": False, "error": "render-limits-unavailable"}
            try:
                out, _err = proc.communicate(json.dumps(payload).encode("utf-8"), timeout=budgets.wallSeconds)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                return {"ok": False, "error": "wall-budget-exceeded", "wallSeconds": round(time.monotonic() - started, 3)}
    finally:
        _RENDER_SLOT.release()
    wall = round(time.monotonic() - started, 3)
    try:
        result = json.loads(out.decode("utf-8") or "{}")
    except ValueError:
        result = {}
    if not result.get("ok"):
        return {"ok": False, "error": classify_exit(proc.returncode, result), "exitCode": proc.returncode, "wallSeconds": wall}
    outputs = {}
    for fmt, data in result["outputs"].items():
        raw = base64.b64decode(data)
        if not raw or len(raw) > MAX_OUTPUT_BYTES:
            return {"ok": False, "error": f"render-{fmt}-size-invalid"}
        if not raw.startswith(PNG_MAGIC if fmt == "png" else GLB_MAGIC):
            return {"ok": False, "error": f"render-{fmt}-mime-mismatch"}
        outputs[fmt] = raw
    return {"ok": True, "outputs": outputs, "size": result["size"], "renderer": result["renderer"],
            "usage": {**result["usage"], "wallSeconds": wall}}


def _artifact(fmt: str, sha: str, job: MeshRenderJob) -> Dict[str, Any]:
    art = {"format": fmt, "artifactRef": f"sc://workbench/figure-adapters/scene/{sha}.{fmt}", "sha256": sha,
           "mediaType": MEDIA[fmt], "status": "local-review", "revision": job.figure.version}
    if fmt == "png":
        art.update(width=job.width, height=job.height)
    return art


def build_bundle(job: MeshRenderJob, scene: Dict[str, Any], artifacts: List[Dict[str, Any]], generated_at: str) -> Dict[str, Any]:
    f = job.figure
    evidence = job.meshes[0].evidenceClass
    measurement = {"observed": "observed", "literature-derived": "published-literature", "modelled": "computed-from-specified-inputs",
                   "hypothetical": "hypothetical-only", "conceptual": "conceptual-only", "status-only": "not-applicable"}[evidence]
    return {
        "schema": BUNDLE_SCHEMA,
        "figureId": f.figureId,
        "version": f.version,
        "title": f.title,
        "project": {"projectRef": f.projectRef, "ownerScope": "isolated-synthetic", "environment": "local-review"},
        "publication": {"kind": "none", "target": "unassigned", "bindingStatus": "unbound"},
        "evidenceClass": evidence,
        "figureType": "scene-3d",
        "scientificContext": {"interpretation": f.interpretation, "limitations": f.limitations,
                              "measurementStatus": measurement, "units": f"{job.scalar.unit}; {job.coordinateSystem['units']}"},
        "sourceRefs": [{"sourceId": f.sourceId, "provider": f.sourceProvider, "identityStatus": "source-identified",
                        "qualityStatus": "not-applicable", "licenceStatus": "pending-review"}],
        "calculationRefs": [{"system": "workbench", "runRef": f.calculationRef, "method": f.calculationMethod,
                             "outputSha256": content_hash([{k: m.get(k) for k in ("meshId", "verticesSha256", "facesSha256", "scalarsSha256")}
                                                            for m in scene["meshes"]])}],
        "rendering": {"profileId": "sc-institutional-research-v1", "renderer": "pyvista-vtk", "caption": f.caption,
                      "altText": f.altText, "palette": "colorblind-safe", "accessibilityReview": "pending"},
        "artifacts": artifacts,
        "provenance": {"authorityOwner": "workbench", "sourceSnapshotIds": [f"scene:{scene['sceneSha256']}"],
                       "generationRunId": f"scene-render:{scene['sceneSha256'][:16]}", "generatedAt": generated_at,
                       "reproducibility": "pinned-renderer-declared-camera"},
        "review": {k: "pending" for k in ("scientific", "visual", "rights", "sourceIntegrity", "publication")},
        "labels": ["scene-3d-proposed"],
        "scene": scene,
    }


def _installed(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def runtime_status() -> Dict[str, Any]:
    installed = {k: _installed(k) for k in PINNED_PACKAGES}
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "buildId": BUILD_ID, "adapterEnabled": _flag(ENABLE_ENV),
            "sceneContract": SCENE_SCHEMA, "contractStatus": "proposed-owner-review", "pinned": PINNED_PACKAGES,
            "installed": installed, "pinnedMatch": installed == PINNED_PACKAGES, "ceilings": CEILINGS,
            "publicationPerformed": False}


def render_mesh(job: MeshRenderJob) -> Dict[str, Any]:
    hashes = {}
    for m in job.meshes:
        h = mesh_hashes(m)
        for key in ("verticesSha256", "facesSha256", "scalarsSha256"):
            declared = getattr(m, key)
            if declared and declared != h.get(key):
                raise ValueError(f"mesh {m.meshId}: {key} does not match the submitted array")
        hashes[m.meshId] = h
    payload = {"meshes": [{"vertices": m.vertices, "faces": m.faces, "scalars": m.scalars, "scalarLocation": m.scalarLocation}
                          for m in job.meshes],
               "scalar": job.scalar.model_dump(), "camera": job.camera.model_dump(), "interpolation": job.interpolation.model_dump(),
               "verticalExaggeration": job.verticalExaggeration, "formats": list(job.formats), "width": job.width, "height": job.height}
    result = run_worker(payload, job.budgets)
    if not result["ok"]:
        raise RuntimeError(result["error"])
    r = result["renderer"]
    if {"pyvista": r.get("pyvista"), "vtk": r.get("vtk")} != PINNED_PACKAGES:
        raise RuntimeError(f"renderer is not the pinned pyvista {PINNED_PACKAGES['pyvista']} / vtk {PINNED_PACKAGES['vtk']}")
    scene = build_scene(job, hashes, f"pyvista {r['pyvista']}; vtk {r['vtk']}")
    files, artifacts = {}, []
    for fmt in job.formats:
        raw = result["outputs"][fmt]
        sha = hashlib.sha256(raw).hexdigest()
        artifacts.append(_artifact(fmt, sha, job))
        files[fmt] = {"sha256": sha, "bytes": len(raw), "mediaType": MEDIA[fmt], "contentBase64": base64.b64encode(raw).decode("ascii")}
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    bundle = build_bundle(job, scene, artifacts, generated_at)
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION, "buildId": BUILD_ID,
        "scene": scene, "figureBundle": bundle, "files": files,
        "renderer": r, "usage": result["usage"], "budgets": scene["budgets"],
        "boundaries": {"contractApproved": False, "publicationPerformed": False, "valuesInterpolatedByAdapter": False,
                       "scalarsClipped": False, "networkUsed": False, "remoteAssetsReferenced": False},
    }
    out["resultHash"] = content_hash({k: v for k, v in out.items() if k not in ("files", "usage", "figureBundle")})
    return out


@router.get("/figure-adapters/scene/status")
def status_route():
    return runtime_status()


async def _bounded_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail=f"scene job exceeds {MAX_BODY_BYTES} bytes")
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail=f"scene job exceeds {MAX_BODY_BYTES} bytes")
    return bytes(body)


@router.post("/figure-adapters/scene/render")
async def render_route(request: Request):
    if not _flag(ENABLE_ENV):
        raise HTTPException(status_code=503, detail=f"FIG-05.1 scene renderer is disabled ({ENABLE_ENV}).")
    # Bounded before parsing, then parsed by pydantic directly, so an oversize job cannot exhaust memory.
    body = await _bounded_body(request)
    try:
        job = MeshRenderJob.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False, include_context=False)) from exc
    try:
        return await run_in_threadpool(render_mesh, job)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        code = 429 if str(exc) == "render-busy" else 409
        raise HTTPException(status_code=code, detail=str(exc)) from exc
