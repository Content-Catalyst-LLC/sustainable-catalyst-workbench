# SC-FIG-05.1 — bounded, reproducible static 3D scene rendering (PyVista/VTK)

**Status: staging candidate, default disabled. The `sc.scene-3d.v0` scene contract is a proposal under owner
review. Nothing here approves it or publishes a figure.**

`POST /figure-adapters/scene/render` (enabled only with `SCWB_SCENE_ADAPTER_ENABLED=true`) takes a declared mesh
job and returns:

* a PNG view (always required);
* an optional binary glTF (GLB) export;
* a `scene` record with a recomputable `sceneSha256`;
* a `figureType: scene-3d` figure bundle for private review.

`GET /figure-adapters/scene/status` reports the pinned and installed renderer versions and the ceilings.

## What the job must declare

The job must declare every one of these; each is refused when missing:

* camera position, focal point, view-up and projection;
* scalar field, unit, increasing range and a sequential colormap (`viridis`, `cividis`, `magma`, `inferno`, `greys`);
* surface interpolation, which must match where the scalars live:
  * `none-flat-faces` needs one scalar per face;
  * `vertex-colour-gouraud` needs one scalar per vertex;
* vertical exaggeration, coordinate system and units;
* evidence class (one per scene);
* budgets.

Scalars outside the declared range are **refused, not clipped**. Optional `verticesSha256`, `facesSha256` and
`scalarsSha256` must match the submitted arrays.

## Hashes

The scene record carries:

* `verticesSha256`, `facesSha256` and `scalarsSha256`: SHA-256 of the canonical JSON (sorted keys, no whitespace,
  UTF-8) of the vertex arrays (floats), face arrays (integers) and scalar arrays (floats).
* `sceneSha256`: the same canonical hash of the scene record without `sceneSha256` itself.

Identity is on geometry and declared rendering, not pixels: changing the legend layout changes the PNG but not the
scene hash.

## Isolation and budgets

* **Worker.** Rendering runs in a separate `python -I` worker:
  * minimal environment with no inherited credentials, proxies or display;
  * a fresh temporary home;
  * sockets and name resolution refused before PyVista is imported;
  * off-screen Mesa (OSMesa, `vtkOSOpenGLRenderWindow`), with llvmpipe running in the main thread.
* **Container.** Run the scene staging image with `--network none`.
* **Ceilings.** Provisional, for isolated staging:

  | Limit | Ceiling | How it is enforced |
  |---|---|---|
  | CPU | 1 CPU, 90 CPU-s | `RLIMIT_CPU` |
  | Memory | 1536 MiB | `RLIMIT_AS` |
  | Wall time | 120 s | timeout; the process group is killed |
  | Concurrency | 1 | a second job is refused (429), not queued |

  Jobs may ask for less but never more. A host that cannot apply the limits refuses to render.
* **Job size.** At most 350,000 vertices and 700,000 faces per scene, and a request body of at most 48 MiB, which
  is refused (413) before it is parsed.

## Measured (synthetic grid surfaces)

Conditions: 1 CPU, 1536 MiB, no network; two runs each.

| Vertices | Worker CPU s | Worker peak RSS MiB | Container peak MiB | Run 2 vs run 1 |
|---|---|---|---|---|
| 10,201 | 4.7–4.9 | 374–376 | 335 | identical PNG bytes |
| 100,489 (+ GLB) | 5.8–6.4 | 478 | 504 | identical PNG and GLB bytes |
| 250,000 | 8.2–8.5 | 605 | 794 | identical PNG bytes |
| 349,281 | 9.8–10.7 | 689 | 962–965 | identical PNG bytes |
| 350,464 | — | — | 527 | refused at validation |

Above the job limit:
* 500,000 vertices reached the 1536 MiB container limit.
* 1,000,000 vertices was killed for memory while the JSON was parsed.

The proposed contract allows 2M vertices per mesh. This job limit stays narrower until arrays move to a binary
transport.

Overruns at 349,281 vertices:

| Budget | Result |
|---|---|
| 5 CPU-s | `cpu-budget-exceeded` |
| 512 MiB | `memory-budget-exceeded` |
| 5 s wall | `wall-budget-exceeded` |

## Building and testing

```
docker build --platform linux/amd64 -f backend/Dockerfile.scene-staging -t <tag> backend
docker run --rm --network none --cpus 1 --memory 1536m --read-only --tmpfs /tmp <tag> \
  python -m pytest -q tests/test_scene_render_fig05_1.py
docker run ... <tag> python scripts/scene_benchmark_fig05_1.py --grid 317 --runs 2
```

Renderer wheels are hash-locked in `backend/requirements-scene.txt`:
* `pyvista` 0.45.2
* `vtk` 9.4.2

The image build fails if VTK cannot open an off-screen OSMesa window. Outside that image the rendering tests are
skipped, never reported as passed.

## Not in this step

* An interactive viewer: the Lab shows the verified PNG only, until 05.2.
* Public release: Research binds scenes privately and holds release until the contract is approved.
* Real or measured scenes: synthetic meshes only.
