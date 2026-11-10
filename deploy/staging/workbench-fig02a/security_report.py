"""Summarize the staging security scan and compare a CI rebuild with the Contabo staging image.

    python security_report.py compare <ref image.json> <ci docker-inspect.json> <ref sbom> <ci sbom>
    python security_report.py trivy <trivy json> [<trivy json> ...]

Both commands print JSON to stdout. Equivalence is claimed only when the image ID matches; matching
layers and matching component sets are reported separately and never treated as identity.
"""
import json
import sys
from collections import Counter

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


def _components(path):
    bom = json.load(open(path))
    return {(c.get("name", "").lower(), c.get("version", "")) for c in bom.get("components", [])}


def compare(ref_path, inspect_path, ref_sbom, ci_sbom):
    ref = json.load(open(ref_path))
    ci = json.load(open(inspect_path))
    ci = ci[0] if isinstance(ci, list) else ci
    ci_layers = ci["RootFS"]["Layers"]
    layers = []
    for i, (origin, digest) in enumerate(zip(ref["layerOrigins"], ref["rootfsLayers"])):
        other = ci_layers[i] if i < len(ci_layers) else None
        layers.append({"index": i, "origin": origin, "match": digest == other, "contabo": digest, "ci": other})
    a, b = _components(ref_sbom), _components(ci_sbom)
    return {
        "imageIdMatch": ci["Id"] == ref["imageId"],
        "contaboImageId": ref["imageId"],
        "ciImageId": ci["Id"],
        "revisionLabel": ci["Config"]["Labels"].get("org.opencontainers.image.revision"),
        "layerCount": {"contabo": len(ref["rootfsLayers"]), "ci": len(ci_layers)},
        "layersMatching": sum(layer["match"] for layer in layers),
        "layers": layers,
        "sbom": {
            "contaboComponents": len(a), "ciComponents": len(b), "identicalComponentSet": a == b,
            "onlyInContabo": sorted(f"{n}@{v}" for n, v in a - b),
            "onlyInCi": sorted(f"{n}@{v}" for n, v in b - a),
        },
        "verdict": ("IDENTICAL_IMAGE" if ci["Id"] == ref["imageId"] else
                    "NOT_BYTE_IDENTICAL; " + ("same component set" if a == b else "component sets differ")),
    }


def trivy(paths):
    out = {}
    for path in paths:
        report = json.load(open(path))
        findings, counts = [], Counter()
        for result in report.get("Results", []) or []:
            for v in result.get("Vulnerabilities", []) or []:
                counts[v.get("Severity", "UNKNOWN")] += 1
                findings.append({
                    "id": v.get("VulnerabilityID"), "severity": v.get("Severity"),
                    "package": v.get("PkgName"), "installed": v.get("InstalledVersion"),
                    "fixed": v.get("FixedVersion") or None, "status": v.get("Status"),
                    "target": result.get("Target"), "class": result.get("Class"), "type": result.get("Type"),
                    "title": (v.get("Title") or "")[:160],
                })
        findings.sort(key=lambda f: (SEVERITIES.index(f["severity"]) if f["severity"] in SEVERITIES else 9, f["package"] or "", f["id"] or ""))
        out[path] = {
            "artifact": report.get("ArtifactName"), "artifactType": report.get("ArtifactType"),
            "createdAt": report.get("CreatedAt"), "trivyVersion": (report.get("Trivy") or {}).get("Version"),
            "counts": {s: counts.get(s, 0) for s in SEVERITIES},
            "withFix": sum(1 for f in findings if f["fixed"]),
            "findings": findings,
        }
    return out


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    result = compare(*args) if cmd == "compare" else trivy(args)
    print(json.dumps(result, indent=1))
