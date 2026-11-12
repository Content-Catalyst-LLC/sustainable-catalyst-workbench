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


def gltf_to_glb(doc):
    """Pack a glTF 2.0 document with inline base64 buffers into one deterministic binary GLB.

    Every buffer is moved into the single BIN chunk (each 4-byte aligned) and buffer views are re-pointed.
    Embedded data URIs for images stay; any external URI is refused so the GLB stays self-contained.
    """
    blob, offsets = b"", []
    for buf in doc.get("buffers", []):
        uri = buf.get("uri", "")
        if not uri.startswith("data:") or ";base64," not in uri:
            raise ValueError("glTF buffer is not inline")
        data = base64.b64decode(uri.split(";base64,", 1)[1])
        offsets.append(len(blob))
        blob += data + b"\x00" * (-len(data) % 4)
    for img in doc.get("images", []):
        if "uri" in img and not img["uri"].startswith("data:"):
            raise ValueError("glTF image is not inline")
    for view in doc.get("bufferViews", []):
        view["byteOffset"] = offsets[view.get("buffer", 0)] + view.get("byteOffset", 0)
        view["buffer"] = 0
    if offsets:
        doc["buffers"] = [{"byteLength": len(blob)}]
    text = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    body = struct.pack("<I4s", len(text), b"JSON") + text
    if blob:
        body += struct.pack("<I4s", len(blob), b"BIN\x00") + blob
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


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
                                           "vertical": True, "fmt": "%.3g", "n_labels": 5,
                                           # Inset from the right edge so tick labels are never clipped.
                                           "position_x": 0.80, "position_y": 0.15, "width": 0.05, "height": 0.7,
                                           "title_font_size": 16, "label_font_size": 14})
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
            path = os.path.join(tmp, "scene.gltf")
            plotter.export_gltf(path, inline_data=True, save_normals=True)
            with open(path, "rb") as fh:
                outputs["glb"] = base64.b64encode(gltf_to_glb(json.load(fh))).decode("ascii")
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
