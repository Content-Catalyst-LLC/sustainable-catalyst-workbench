"""Emit a CycloneDX 1.5 SBOM for the Workbench staging image from inside the image.

Run in a throwaway container with no network, for example:
    docker run --rm --network none -i --entrypoint python <image> - < sbom.py > sbom.cdx.json

Inventories Debian packages (/var/lib/dpkg/status), Python distributions (importlib.metadata),
Chrome for Testing and the Julia runtime. Uses only the standard library and data already in
the image; no third-party scanner is executed.
"""
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from importlib import metadata


def _debian_version():
    # Scanners match Debian advisories by release (e.g. debian-12.15), not by codename.
    try:
        return open("/etc/debian_version", encoding="utf-8").read().strip()
    except OSError:
        return "unknown"


def _debian():
    out, cur = [], {}
    with open("/var/lib/dpkg/status", encoding="utf-8", errors="replace") as fh:
        for line in fh.read().split("\n") + [""]:
            if not line.strip():
                if cur.get("Package") and "installed" in cur.get("Status", ""):
                    name, ver, arch = cur["Package"], cur.get("Version", ""), cur.get("Architecture", "")
                    # Debian advisories are keyed by source package ("Source: util-linux (2.38.1-5)").
                    src = cur.get("Source", name).split()
                    src_name = src[0]
                    src_ver = src[1].strip("()") if len(src) > 1 else ver
                    out.append({"type": "library", "name": name, "version": ver,
                                "purl": f"pkg:deb/debian/{name}@{ver}?arch={arch}&distro=debian-{_debian_version()}",
                                "properties": [{"name": "sc:source", "value": "dpkg"},
                                               {"name": "aquasecurity:trivy:SrcName", "value": src_name},
                                               {"name": "aquasecurity:trivy:SrcVersion", "value": src_ver}]})
                cur = {}
            elif not line.startswith(" ") and ":" in line:
                k, v = line.split(":", 1)
                cur[k] = v.strip()
    return out


def _python():
    out = {}
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        lic = dist.metadata.get("License-Expression") or dist.metadata.get("License") or ""
        comp = {"type": "library", "name": name, "version": dist.version,
                "purl": f"pkg:pypi/{name.lower().replace('_', '-')}@{dist.version}",
                "properties": [{"name": "sc:source", "value": "python-site-packages"}]}
        if lic and len(lic) < 120:
            comp["licenses"] = [{"license": {"name": lic}}]
        out[(name.lower(), dist.version)] = comp
    return sorted(out.values(), key=lambda c: c["name"].lower())


def _version(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def main():
    chrome = os.getenv("SCWB_PLOTLY_BROWSER_PATH", "/opt/chrome-linux64/chrome")
    chrome_version = (_version([chrome, "--version"]).split() or [""])[-1]
    runtimes = [
        {"type": "application", "name": "chrome-for-testing", "version": chrome_version,
         "purl": "pkg:generic/chrome-for-testing", "properties": [{"name": "sc:path", "value": chrome}]},
        {"type": "application", "name": "julia", "version": _version(["julia", "--version"]).replace("julia version ", ""),
         "purl": "pkg:generic/julia", "properties": [{"name": "sc:path", "value": "/usr/local/julia"}]},
        {"type": "application", "name": "cpython", "version": sys.version.split()[0], "purl": f"pkg:generic/cpython@{sys.version.split()[0]}"},
    ]
    os_component = {"type": "operating-system", "name": "debian", "version": _debian_version(),
                    "purl": f"pkg:generic/debian@{_debian_version()}"}
    components = [os_component] + runtimes + _python() + _debian()
    for c in components:
        c["bom-ref"] = c["purl"] if "@" in c["purl"] else f"{c['purl']}@{c['version']}"
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "tools": {"components": [{"type": "application", "name": "sc-workbench-staging-sbom", "version": "1.0"}]},
            "component": {"type": "container", "name": "sc-workbench-staging", "version": os.getenv("SBOM_IMAGE_TAG", "")},
        },
        "components": components,
    }
    json.dump(bom, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
