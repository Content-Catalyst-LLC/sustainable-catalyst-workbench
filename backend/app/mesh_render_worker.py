"""SC-FIG-05.1 isolated off-screen PyVista/VTK mesh render worker (static PNG, optional GLB).

Run only as ``python -I mesh_render_worker.py`` by ``scene_render_adapter.render_mesh``. Reads one
validated JSON job on stdin and writes one JSON result on stdout. It imports nothing from the
Workbench application, receives a minimal environment without service credentials, refuses every
socket before PyVista is imported, and runs under the CPU-time and address-space limits the parent
sets. The PNG is encoded here (no timestamps or text chunks) so identical pixels give identical bytes.
"""
import base64
import json
import os
import resource
import socket
import struct
import sys
import tempfile
import time
import zlib

COLORMAPS = {"viridis", "cividis", "magma", "inferno", "greys"}


class NetworkDenied(OSError):
    pass


def _deny(*_args, **_kwargs):
    raise NetworkDenied("network access is not permitted in the scene render worker")


def deny_network():
    """Refuse name resolution and every socket; the staging container also runs with no network."""
    for name in ("connect", "connect_ex", "bind", "sendto"):
        setattr(socket.socket, name, _deny)
    socket.create_connection = _deny  # type: ignore[assignment]
    socket.getaddrinfo = _deny  # type: ignore[assignment]
    socket.gethostbyname = _deny  # type: ignore[assignment]


def _fail(error):
    sys.stdout.write(json.dumps({"ok": False, "error": error}))
    return 0


def png_bytes(rgb, width, height):
    """Encode an 8-bit RGB pixel buffer (rows top to bottom) as a minimal deterministic PNG."""
    stride = width * 3
    raw = b"".join(b"\x00" + rgb[y * stride:(y + 1) * stride] for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _usage(started):
    ru = resource.getrusage(resource.RUSAGE_SELF)
    # Linux reports ru_maxrss in KiB.
    return {"cpuSeconds": round(ru.ru_utime + ru.ru_stime, 3), "peakRssMiB": round(ru.ru_maxrss / 1024, 1),
            "workerWallSeconds": round(time.monotonic() - started, 3)}


def render(job, np, pv):
    meshes = []
    for m in job["meshes"]:
        verts = np.asarray(m["vertices"], dtype=np.float64)
        verts[:, 2] *= job["verticalExaggeration"]
        faces = np.asarray(m["faces"], dtype=np.int64)
        poly = pv.PolyData(verts, np.hstack([np.full((len(faces), 1), 3, dtype=np.int64), faces]).ravel())
        field = job["scalar"]["field"]
        if m.get("scalars") is not None:
            values = np.asarray(m["scalars"], dtype=np.float64)
            if m["scalarLocation"] == "face":
                poly.cell_data[field] = values
            else:
                poly.point_data[field] = values
        meshes.append((m, poly))
    width, height = job["width"], job["height"]
    plotter = pv.Plotter(off_screen=True, window_size=(width, height))
    plotter.set_background("white")
    flat = job["interpolation"]["surface"] == "none-flat-faces"
    scalar = job["scalar"]
    for i, (m, poly) in enumerate(meshes):
        kwargs = {"show_edges": False, "smooth_shading": not flat, "lighting": True}
        if m.get("scalars") is not None:
            kwargs.update(scalars=scalar["field"], cmap=scalar["colormap"] if scalar["colormap"] != "greys" else "Greys",
                          clim=list(scalar["range"]), preference="cell" if m["scalarLocation"] == "face" else "point",
                          interpolate_before_map=not flat, show_scalar_bar=(i == 0),
                          scalar_bar_args={"title": f"{scalar['field']} ({scalar['unit']})", "color": "black",
                                           "vertical": True, "fmt": "%.3g"})
        else:
            kwargs.update(color="#bdbdbd")
        plotter.add_mesh(poly, **kwargs)
    cam = job["camera"]
    plotter.camera.position = tuple(cam["position"])
    plotter.camera.focal_point = tuple(cam["focalPoint"])
    plotter.camera.up = tuple(cam["viewUp"])
    if cam["projection"] == "parallel":
        plotter.enable_parallel_projection()
    elif cam.get("viewAngleDegrees"):
        plotter.camera.view_angle = float(cam["viewAngleDegrees"])
    img = plotter.screenshot(return_img=True, window_size=(width, height))
    rgb = np.ascontiguousarray(img[:, :, :3], dtype=np.uint8)
    outputs = {"png": base64.b64encode(png_bytes(rgb.tobytes(), rgb.shape[1], rgb.shape[0])).decode("ascii")}
    if "glb" in job["formats"]:
        with tempfile.TemporaryDirectory(prefix="scene-glb-") as tmp:
            path = os.path.join(tmp, "scene.glb")
            plotter.export_gltf(path, inline_data=True, save_normals=True)
            with open(path, "rb") as fh:
                outputs["glb"] = base64.b64encode(fh.read()).decode("ascii")
    window = plotter.ren_win.GetClassName()
    plotter.close()
    return outputs, {"width": int(rgb.shape[1]), "height": int(rgb.shape[0]), "renderWindow": window}


def main():
    started = time.monotonic()
    deny_network()
    try:
        job = json.loads(sys.stdin.read())
        if job["scalar"]["colormap"] not in COLORMAPS or not set(job["formats"]) <= {"png", "glb"}:
            return _fail("invalid-job")
    except (ValueError, KeyError, TypeError):
        return _fail("invalid-job")
    try:
        import numpy as np
        import pyvista as pv
        import vtk
    except MemoryError:
        return _fail("memory-budget-exceeded")
    except ImportError as exc:
        text = str(exc).lower()
        if "cannot allocate" in text or "failed to map" in text or "memory" in text:
            return _fail("memory-budget-exceeded")
        return _fail("pyvista-or-vtk-not-installed")
    pv.OFF_SCREEN = True
    try:
        outputs, size = render(job, np, pv)
    except MemoryError:
        return _fail("memory-budget-exceeded")
    except NetworkDenied:
        return _fail("network-attempt-refused")
    except Exception as exc:  # noqa: BLE001 - classified, never echoed with paths or environment
        text = f"{type(exc).__name__} {exc}".lower()
        if "bad_alloc" in text or "cannot allocate" in text:
            return _fail("memory-budget-exceeded")
        return _fail("render-failed")
    sys.stdout.write(json.dumps({
        "ok": True, "outputs": outputs, "size": size,
        "renderer": {"pyvista": pv.__version__, "vtk": vtk.vtkVersion.GetVTKVersion(), "renderWindow": size.pop("renderWindow")},
        "usage": _usage(started),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
