"""Workbench v9.9.0 — Research Package Exchange & Portability.

Content-addressed export/import packaging for Workbench research objects. A portable
package contains a canonical manifest, selected object payloads, dependency/reference
inventory, per-file hashes, runtime compatibility metadata, and provenance. Imports
are validated before they can be explicitly staged; staging never mutates native
Workbench research stores or creates governed Platform Core objects automatically.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v900 import load_study as load_scientific_study, list_studies as list_scientific_studies
from .v910 import load_protocol, list_protocols
from .v920 import load_campaign, list_campaigns
from .v930 import load_analysis as load_statistical_analysis, list_analyses as list_statistical_analyses
from .v940 import load_study as load_uncertainty_study, list_studies as list_uncertainty_studies
from .v950 import load_calibration, list_calibrations
from .v960 import load_synthesis, list_syntheses
from .v970 import load_workflow, list_workflows
from .v980 import load_analysis as load_meta_analysis, list_analyses as list_meta_analyses

VERSION = APP_VERSION
SCHEMA = "sc-workbench-research-package-exchange-portability/1.0"
PACKAGE_SCHEMA = "sc-workbench-portable-research-package/1.0"
VALIDATION_SCHEMA = "sc-workbench-portable-package-validation/1.0"
STAGING_SCHEMA = "sc-workbench-portable-package-staging/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-research-package-core-plan/1.0"
router = APIRouter(tags=["workbench-v990-research-package-exchange-portability"])

ObjectType = Literal[
    "scientific-study",
    "research-protocol",
    "computational-campaign",
    "statistical-analysis",
    "uncertainty-sensitivity-study",
    "model-calibration",
    "results-synthesis",
    "reproduction-replication-workflow",
    "cross-study-meta-analysis",
]

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _package_dir(project_key: str, package_hash: str) -> Path:
    return _store_root() / "portable-research-packages" / _stable_id(project_key) / package_hash


def _package_manifest_path(project_key: str, package_hash: str) -> Path:
    return _package_dir(project_key, package_hash) / "manifest.json"


def _package_archive_path(project_key: str, package_hash: str) -> Path:
    return _package_dir(project_key, package_hash) / f"{package_hash}.zip"


def _staging_dir(target_project_key: str) -> Path:
    return _store_root() / "portable-import-staging" / _stable_id(target_project_key)


def _semver(value: str) -> tuple[int, int, int]:
    try:
        parts = value.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
    except Exception:
        return (0, 0, 0)


class ObjectSelection(BaseModel):
    objectType: ObjectType
    objectHash: str = Field(min_length=64, max_length=64)
    sourceProjectKey: str = Field(default="", max_length=160)
    label: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _HASH_RE.match(self.objectHash):
            raise ValueError("objectHash must be a 64-character hexadecimal content hash")
        self.sourceProjectKey = self.sourceProjectKey.strip()
        self.label = self.label.strip()
        return self


class BuildPackageRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    packageKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=12000)
    selections: List[ObjectSelection] = Field(default_factory=list, max_length=500)
    includeProjectWorkspace: bool = True
    strictDependencyClosure: bool = False
    license: str = Field(default="", max_length=500)
    createdBy: str = Field(default="workbench", max_length=160)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def normalize(self):
        self.projectKey = self.projectKey.strip()
        self.packageKey = self.packageKey.strip()
        self.title = self.title.strip()
        seen = set()
        for item in self.selections:
            key = (item.objectType, item.sourceProjectKey or self.projectKey, item.objectHash)
            if key in seen:
                raise ValueError("duplicate object selection")
            seen.add(key)
        if not self.includeProjectWorkspace and not self.selections:
            raise ValueError("a package must include the project workspace or at least one selected object")
        return self


class ValidateImportRequest(BaseModel):
    archiveBase64: str = Field(min_length=1)
    requireDependencyClosure: bool = False


class StageImportRequest(ValidateImportRequest):
    targetProjectKey: str = Field(min_length=1, max_length=160)
    stagedBy: str = Field(default="workbench", max_length=160)
    confirmStage: bool = False


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    packageHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


_LOADERS = {
    "scientific-study": load_scientific_study,
    "research-protocol": load_protocol,
    "computational-campaign": load_campaign,
    "statistical-analysis": load_statistical_analysis,
    "uncertainty-sensitivity-study": load_uncertainty_study,
    "model-calibration": load_calibration,
    "results-synthesis": load_synthesis,
    "reproduction-replication-workflow": load_workflow,
    "cross-study-meta-analysis": load_meta_analysis,
}


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Research Package Exchange & Portability",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "packageSchema": PACKAGE_SCHEMA,
        "supportedObjectTypes": list(_LOADERS),
        "capabilities": {
            "contentAddressedPortablePackages": True,
            "realZipArchiveExport": True,
            "perObjectIntegrityHashes": True,
            "dependencyReferenceInventory": True,
            "runtimeCompatibilityAssessment": True,
            "nonMutatingImportValidation": True,
            "explicitImportStaging": True,
            "nativeStoreMutationOnStage": False,
            "crossProductExchangePlanning": True,
            "platformCorePackagePlanning": True,
        },
        "boundaries": {
            "automaticNativeObjectOverwrite": False,
            "automaticImportedObjectActivation": False,
            "automaticScientificValidityInference": False,
            "automaticEvidencePromotion": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
            "archiveExecutionAllowed": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _load_selection(owner_project: str, selection: ObjectSelection) -> Dict[str, Any]:
    project = selection.sourceProjectKey or owner_project
    loader = _LOADERS[selection.objectType]
    payload = loader(project, selection.objectHash)
    return {
        "objectType": selection.objectType,
        "sourceProjectKey": project,
        "sourceObjectHash": selection.objectHash,
        "label": selection.label,
        "payloadHash": content_hash(payload),
        "payload": payload,
    }


def _walk_hash_refs(value: Any, path: str = "$") -> List[Dict[str, str]]:
    refs: List[Dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str) and _HASH_RE.match(child) and key.lower().endswith("hash"):
                refs.append({"path": child_path, "hash": child.lower(), "field": key})
            refs.extend(_walk_hash_refs(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            refs.extend(_walk_hash_refs(child, f"{path}[{idx}]") )
    return refs


def _dependency_inventory(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    included = set()
    for obj in objects:
        included.add(obj["sourceObjectHash"].lower())
        included.add(obj["payloadHash"].lower())
        for key in ("recordHash", "studyHash", "protocolHash", "campaignHash", "analysisHash", "calibrationHash", "synthesisHash", "workflowHash"):
            val = obj["payload"].get(key) if isinstance(obj.get("payload"), dict) else None
            if isinstance(val, str) and _HASH_RE.match(val):
                included.add(val.lower())
    refs: List[Dict[str, Any]] = []
    seen = set()
    for obj in objects:
        for ref in _walk_hash_refs(obj["payload"]):
            key = (obj["objectType"], obj["sourceObjectHash"], ref["path"], ref["hash"])
            if key in seen:
                continue
            seen.add(key)
            refs.append({
                "fromObjectType": obj["objectType"],
                "fromObjectHash": obj["sourceObjectHash"],
                **ref,
                "resolvedInPackage": ref["hash"] in included,
            })
    unresolved = [x for x in refs if not x["resolvedInPackage"]]
    return {
        "referenceCount": len(refs),
        "resolvedReferenceCount": len(refs) - len(unresolved),
        "unresolvedReferenceCount": len(unresolved),
        "references": refs,
        "dependencyClosureComplete": len(unresolved) == 0,
    }


def _package_seed(req: BuildPackageRequest, objects: List[Dict[str, Any]], project_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    portable_objects: List[Dict[str, Any]] = []
    if project_payload is not None:
        portable_objects.append({
            "objectType": "research-project-workspace",
            "sourceProjectKey": req.projectKey,
            "sourceObjectHash": content_hash(project_payload),
            "label": project_payload.get("title", req.projectKey) if isinstance(project_payload, dict) else req.projectKey,
            "payloadHash": content_hash(project_payload),
            "payload": project_payload,
        })
    portable_objects.extend(objects)
    deps = _dependency_inventory(portable_objects)
    return {
        "packageSchema": PACKAGE_SCHEMA,
        "packageFormatVersion": "1.0",
        "sourceProduct": PRODUCT_KEY,
        "sourceRuntime": RUNTIME_KIND,
        "sourceWorkbenchVersion": VERSION,
        "minimumCompatibleWorkbenchMajor": _semver(VERSION)[0],
        "projectKey": req.projectKey,
        "packageKey": req.packageKey,
        "title": req.title,
        "description": req.description,
        "license": req.license,
        "objects": portable_objects,
        "objectCount": len(portable_objects),
        "dependencyInventory": deps,
        "strictDependencyClosure": req.strictDependencyClosure,
        "notes": req.notes,
    }


def _write_archive(package_dir: Path, package_manifest: Dict[str, Any]) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest_for_archive = dict(package_manifest)
    manifest_for_archive.pop("archivePath", None)
    files: Dict[str, bytes] = {}
    object_index: List[Dict[str, Any]] = []
    for idx, obj in enumerate(package_manifest["objects"], start=1):
        safe_type = obj["objectType"].replace("/", "-")
        name = f"objects/{idx:04d}-{safe_type}-{obj['sourceObjectHash'][:12]}.json"
        data = _canonical_bytes(obj["payload"])
        files[name] = data
        object_index.append({
            "path": name,
            "objectType": obj["objectType"],
            "sourceProjectKey": obj["sourceProjectKey"],
            "sourceObjectHash": obj["sourceObjectHash"],
            "payloadHash": obj["payloadHash"],
            "sha256": _sha256_bytes(data),
            "sizeBytes": len(data),
        })
    manifest_for_archive["objectFiles"] = object_index
    manifest_for_archive["archiveIntegrity"] = {
        "algorithm": "sha256",
        "fileCount": len(object_index) + 1,
        "objectFilesHash": content_hash(object_index),
    }
    manifest_bytes = _canonical_bytes(manifest_for_archive)
    files["manifest.json"] = manifest_bytes
    archive = package_dir / f"{package_manifest['packageHash']}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[name])
    return archive


def build_package(req: BuildPackageRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey)
    objects = [_load_selection(req.projectKey, item) for item in req.selections]
    seed = _package_seed(req, objects, project if req.includeProjectWorkspace else None)
    if req.strictDependencyClosure and not seed["dependencyInventory"]["dependencyClosureComplete"]:
        raise ValueError("strictDependencyClosure requested but unresolved hash references remain")
    package_hash = content_hash(seed)
    package_dir = _package_dir(req.projectKey, package_hash)
    existing = _package_manifest_path(req.projectKey, package_hash)
    if existing.exists():
        old = _json_read(existing)
        return {**old, "idempotent": True}
    record = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        **seed,
        "packageHash": package_hash,
        "packageRef": f"sc://workbench/research-package/{req.projectKey}/{package_hash}",
        "createdBy": req.createdBy,
        "createdAt": _now(),
        "boundaries": manifest()["boundaries"],
    }
    archive = _write_archive(package_dir, record)
    record["archiveSha256"] = _sha256_bytes(archive.read_bytes())
    record["archiveSizeBytes"] = archive.stat().st_size
    record["archiveDownloadPath"] = f"/research-package-exchange/packages/{req.projectKey}/{package_hash}/download"
    _atomic_json_write(existing, record)
    return {**record, "idempotent": False}


def load_package(project_key: str, package_hash: str) -> Dict[str, Any]:
    path = _package_manifest_path(project_key, package_hash)
    if not path.exists():
        raise FileNotFoundError(f"portable research package not found: {package_hash}")
    return _json_read(path)


def list_packages(project_key: str) -> Dict[str, Any]:
    root = _store_root() / "portable-research-packages" / _stable_id(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for p in sorted(root.glob("*/manifest.json")):
            try:
                r = _json_read(p)
                rows.append({k: r.get(k) for k in ("packageKey", "title", "packageHash", "packageRef", "objectCount", "sourceWorkbenchVersion", "archiveSha256", "createdAt", "createdBy")})
            except Exception:
                continue
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "packageCount": len(rows), "packages": rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    catalogs = {
        "scientificStudies": list_scientific_studies(project_key),
        "researchProtocols": list_protocols(project_key),
        "computationalCampaigns": list_campaigns(project_key),
        "statisticalAnalyses": list_statistical_analyses(project_key),
        "uncertaintySensitivityStudies": list_uncertainty_studies(project_key),
        "modelCalibrations": list_calibrations(project_key),
        "resultsSyntheses": list_syntheses(project_key),
        "reproductionReplicationWorkflows": list_workflows(project_key),
        "crossStudyMetaAnalyses": list_meta_analyses(project_key),
    }
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "catalogs": catalogs,
        "portablePackageCount": list_packages(project_key)["packageCount"],
        "boundaries": {"catalogExportsAutomatically": False, "catalogInfersScientificQuality": False},
    }
    out["catalogHash"] = content_hash(out)
    return out


def _safe_zip_names(zf: zipfile.ZipFile) -> None:
    for info in zf.infolist():
        p = PurePosixPath(info.filename)
        if p.is_absolute() or ".." in p.parts or info.filename.startswith(("/", "\\")):
            raise ValueError(f"unsafe archive path: {info.filename}")
        if info.file_size > 64 * 1024 * 1024:
            raise ValueError(f"archive entry exceeds 64 MiB safety limit: {info.filename}")


def validate_archive_bytes(data: bytes, require_dependency_closure: bool = False) -> Dict[str, Any]:
    archive_sha = _sha256_bytes(data)
    try:
        zf = zipfile.ZipFile(io.BytesIO(data), "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("archiveBase64 is not a valid ZIP archive") from exc
    with zf:
        _safe_zip_names(zf)
        names = set(zf.namelist())
        if "manifest.json" not in names:
            raise ValueError("portable package is missing manifest.json")
        try:
            package = json.loads(zf.read("manifest.json"))
        except Exception as exc:
            raise ValueError("manifest.json is not valid JSON") from exc
        if package.get("packageSchema") != PACKAGE_SCHEMA:
            raise ValueError(f"unsupported package schema: {package.get('packageSchema')}")
        if package.get("sourceProduct") != PRODUCT_KEY:
            raise ValueError(f"unsupported source product: {package.get('sourceProduct')}")
        object_files = package.get("objectFiles") or []
        checks: List[Dict[str, Any]] = []
        errors: List[str] = []
        seed_keys = (
            "packageSchema", "packageFormatVersion", "sourceProduct", "sourceRuntime",
            "sourceWorkbenchVersion", "minimumCompatibleWorkbenchMajor", "projectKey",
            "packageKey", "title", "description", "license", "objects", "objectCount",
            "dependencyInventory", "strictDependencyClosure", "notes",
        )
        recalculated_package_hash = content_hash({k: package.get(k) for k in seed_keys})
        package_hash_valid = recalculated_package_hash == package.get("packageHash")
        if not package_hash_valid:
            errors.append("packageHash mismatch")
        for item in object_files:
            path = item.get("path", "")
            if path not in names:
                errors.append(f"missing object file: {path}")
                continue
            raw = zf.read(path)
            actual_sha = _sha256_bytes(raw)
            sha_ok = actual_sha == item.get("sha256")
            try:
                payload = json.loads(raw)
                payload_hash = content_hash(payload)
                content_ok = payload_hash == item.get("payloadHash")
            except Exception:
                payload_hash = None
                content_ok = False
            if not sha_ok:
                errors.append(f"sha256 mismatch: {path}")
            if not content_ok:
                errors.append(f"payloadHash mismatch: {path}")
            checks.append({"path": path, "sha256Valid": sha_ok, "payloadHashValid": content_ok, "payloadHash": payload_hash})
        deps = package.get("dependencyInventory") or {}
        closure = bool(deps.get("dependencyClosureComplete", False))
        if require_dependency_closure and not closure:
            errors.append("dependency closure is incomplete")
        source_version = str(package.get("sourceWorkbenchVersion", "0.0.0"))
        source_semver = _semver(source_version)
        current_semver = _semver(VERSION)
        major_compatible = source_semver[0] == current_semver[0] and source_semver[0] != 0
        future_minor = source_semver[:2] > current_semver[:2] if major_compatible else False
        compatibility = {
            "currentWorkbenchVersion": VERSION,
            "sourceWorkbenchVersion": source_version,
            "majorCompatible": major_compatible,
            "sourceMinorIsNewer": future_minor,
            "packageFormatSupported": package.get("packageFormatVersion") == "1.0",
            "nativeActivationAutomaticallyAllowed": False,
        }
        compatible = major_compatible and compatibility["packageFormatSupported"] and not future_minor
        return {
            "ok": len(errors) == 0,
            "schema": VALIDATION_SCHEMA,
            "version": VERSION,
            "archiveSha256": archive_sha,
            "archiveSizeBytes": len(data),
            "packageHash": package.get("packageHash"),
            "recalculatedPackageHash": recalculated_package_hash,
            "packageHashValid": package_hash_valid,
            "packageKey": package.get("packageKey"),
            "projectKey": package.get("projectKey"),
            "objectCount": len(object_files),
            "integrityChecks": checks,
            "dependencyInventory": deps,
            "compatibility": compatibility,
            "compatible": compatible,
            "errors": errors,
            "boundaries": manifest()["boundaries"],
        }


def validate_import(req: ValidateImportRequest) -> Dict[str, Any]:
    try:
        data = base64.b64decode(req.archiveBase64, validate=True)
    except Exception as exc:
        raise ValueError("archiveBase64 is not valid base64") from exc
    return validate_archive_bytes(data, req.requireDependencyClosure)


def stage_import(req: StageImportRequest) -> Dict[str, Any]:
    if not req.confirmStage:
        raise ValueError("confirmStage must be true to persist an imported package in staging")
    try:
        data = base64.b64decode(req.archiveBase64, validate=True)
    except Exception as exc:
        raise ValueError("archiveBase64 is not valid base64") from exc
    validation = validate_archive_bytes(data, req.requireDependencyClosure)
    if not validation["ok"]:
        raise ValueError("package integrity validation failed")
    if not validation["compatible"]:
        raise ValueError("package is not compatible with the current Workbench runtime")
    target = req.targetProjectKey.strip()
    load_project(target)
    staging_hash = content_hash({
        "targetProjectKey": target,
        "archiveSha256": validation["archiveSha256"],
        "packageHash": validation.get("packageHash"),
    })
    root = _staging_dir(target) / staging_hash
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "package.zip"
    meta = root / "staging.json"
    if archive.exists() and meta.exists():
        old = _json_read(meta)
        return {**old, "idempotent": True}
    archive.write_bytes(data)
    record = {
        "ok": True,
        "schema": STAGING_SCHEMA,
        "version": VERSION,
        "targetProjectKey": target,
        "stagingHash": staging_hash,
        "packageHash": validation.get("packageHash"),
        "archiveSha256": validation["archiveSha256"],
        "validation": validation,
        "stagedBy": req.stagedBy,
        "stagedAt": _now(),
        "activationState": "staged-only",
        "boundaries": {
            "nativeResearchStoresMutated": False,
            "importedObjectsActivated": False,
            "existingObjectsOverwritten": False,
            "automaticCoreDispatch": False,
        },
    }
    _atomic_json_write(meta, record)
    return {**record, "idempotent": False}


def list_staged_imports(target_project_key: str) -> Dict[str, Any]:
    root = _staging_dir(target_project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for p in sorted(root.glob("*/staging.json")):
            try:
                r = _json_read(p)
                rows.append({k: r.get(k) for k in ("stagingHash", "packageHash", "archiveSha256", "stagedBy", "stagedAt", "activationState")})
            except Exception:
                continue
    return {"ok": True, "schema": STAGING_SCHEMA, "version": VERSION, "targetProjectKey": target_project_key, "stagingCount": len(rows), "imports": rows}


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    package = load_package(req.projectKey, req.packageHash)
    cfg = core_config()
    binding = {
        "objectType": "workbench.portable-research-package",
        "objectHash": req.packageHash,
        "objectRef": package.get("packageRef"),
        "archiveSha256": package.get("archiveSha256"),
        "sourceWorkbenchVersion": package.get("sourceWorkbenchVersion"),
        "objectCount": package.get("objectCount"),
        "coreProjectEntityId": req.coreProjectEntityId,
        "coreSessionId": req.coreSessionId,
        "visibility": req.visibility,
        "createdBy": req.createdBy,
    }
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "packageHash": req.packageHash,
        "bindingPlan": binding,
        "core": {"enabled": bool(cfg.get("enabled")), "baseUrlConfigured": bool(cfg.get("baseUrl"))},
        "boundaries": {
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
            "nativeImportActivated": False,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def _wrap(fn, *args):
    try:
        return fn(*args)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/research-package-exchange/manifest")
def route_manifest(): return manifest()

@router.get("/research-package-exchange/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/research-package-exchange/packages")
def route_build(req: BuildPackageRequest): return _wrap(build_package, req)

@router.get("/research-package-exchange/packages/{project_key}")
def route_list(project_key: str): return list_packages(project_key)

@router.get("/research-package-exchange/packages/{project_key}/{package_hash}")
def route_get(project_key: str, package_hash: str): return _wrap(load_package, project_key, package_hash)

@router.get("/research-package-exchange/packages/{project_key}/{package_hash}/download")
def route_download(project_key: str, package_hash: str):
    _wrap(load_package, project_key, package_hash)
    path = _package_archive_path(project_key, package_hash)
    if not path.exists():
        raise HTTPException(status_code=404, detail="portable research package archive not found")
    return FileResponse(path, media_type="application/zip", filename=f"sc-workbench-research-package-{package_hash}.zip")

@router.post("/research-package-exchange/import/validate")
def route_validate(req: ValidateImportRequest): return _wrap(validate_import, req)

@router.post("/research-package-exchange/import/stage")
def route_stage(req: StageImportRequest): return _wrap(stage_import, req)

@router.get("/research-package-exchange/imports/{target_project_key}")
def route_staged(target_project_key: str): return list_staged_imports(target_project_key)

@router.post("/integration/core/research-package-exchange/plan")
def route_core(req: CorePlanRequest): return _wrap(core_plan, req)

@router.get("/v990/status")
def status():
    m = manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": m["release"],
        "researchPackageExchangePortability": True,
        "contentAddressedPortablePackages": True,
        "realZipArchiveExport": True,
        "nonMutatingImportValidation": True,
        "explicitImportStaging": True,
        "nativeStoreMutationOnStage": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }
