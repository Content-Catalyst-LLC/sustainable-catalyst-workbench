from backend.app.v450 import (
    ExtensionManifestInput, CompatibilityInput, RegistryEntryInput,
    PermissionAuditInput, HookContractInput, LifecyclePlanInput,
    SDKScaffoldInput, ExtensionAuditInput, ExtensionPackageInput,
    status_record, normalize_manifest, evaluate_compatibility,
    build_registry_entry, audit_permissions, build_hook_contract,
    build_lifecycle_plan, build_sdk_scaffold, audit_extension,
    build_extension_package, parse_version, version_in_range,
)


def manifest(**kwargs):
    data=dict(name="Example Panel",version="0.1.0",publisher="Developer",minimumCoreVersion="4.5.0",capabilities=["project.read","ui.panel"],hooks=["workbench.ready"],packageHash="a"*64,signature="sig",publicKeyId="developer-key")
    data.update(kwargs)
    return normalize_manifest(ExtensionManifestInput(**data))


def compatibility(record=None, **kwargs):
    return evaluate_compatibility(CompatibilityInput(manifest=record or manifest(), **kwargs))


def test_status_boundaries_and_studio_count():
    result=status_record(); assert result["version"]=="4.5.0"; assert result["expectedStudioCount"]==27; assert not result["automaticExtensionInstallationAuthorized"]; assert not result["arbitraryCodeExecutionAuthorized"]; assert not result["remoteShellAuthorized"]


def test_semver_parser_and_range():
    assert parse_version("v4.5.0")== (4,5,0); assert version_in_range("4.5.0","4.4.0","4.6.0"); assert not version_in_range("4.3.9","4.4.0")


def test_manifest_stable_hash_and_ready():
    first=manifest(); second=manifest(); assert first["manifestHash"]==second["manifestHash"]; assert first["readyForCompatibilityReview"]


def test_manifest_blocks_forbidden_capabilities():
    result=manifest(capabilities=["project.read","shell.execute"]); assert not result["readyForCompatibilityReview"]; assert any(x["code"]=="forbidden-capability" for x in result["findings"])


def test_manifest_blocks_unknown_hook_and_wildcard():
    result=manifest(hooks=["workbench.ready","unknown.event"],permissions=["*"]); codes={x["code"] for x in result["findings"]}; assert "unknown-hook" in codes; assert "wildcard-permission-denied" in codes


def test_manifest_marks_high_risk_for_review():
    result=manifest(capabilities=["project.write","ui.panel"]); assert result["highRisk"]; assert any(x["code"]=="security-review-required" for x in result["findings"])


def test_compatibility_passes_supported_core():
    result=compatibility(); assert result["compatible"]; assert result["coreCompatible"]; assert not result["automaticExtensionInstallationAuthorized"]


def test_compatibility_blocks_missing_capability_and_dependency():
    record=manifest(dependencies={"other-extension":"1.2.0"}); result=compatibility(record,availableCapabilities=["ui.panel"],installedExtensions={"other-extension":"1.1.0"}); codes={x["code"] for x in result["blockers"]}; assert not result["compatible"]; assert "capability-unavailable" in codes; assert "dependency-unsatisfied" in codes


def test_registry_approval_requires_compatibility_integrity_signature_and_reviewer():
    result=build_registry_entry(RegistryEntryInput(manifest=manifest(),state="approved",trustTier="verified")); assert result["state"]=="blocked"; assert len(result["blockers"])==4


def test_registry_approval_is_human_controlled():
    comp=compatibility(); result=build_registry_entry(RegistryEntryInput(manifest=manifest(),state="approved",trustTier="verified",reviewer="Reviewer",compatibility=comp,integrityVerified=True,signatureVerified=True)); assert result["state"]=="approved"; assert not result["automaticRegistryPublicationAuthorized"]; assert not result["automaticExtensionActivationAuthorized"]


def test_permission_audit_requires_host_allowlist_and_explicit_approval():
    result=audit_permissions(PermissionAuditInput(capabilities=["network.fetch","project.write"])); codes={x["code"] for x in result["blockers"]}; assert "network-host-allowlist-required" in codes; assert "explicit-approval-required" in codes; assert not result["ready"]


def test_permission_audit_passes_scoped_read_only_extension():
    result=audit_permissions(PermissionAuditInput(capabilities=["project.read","ui.panel"],dataScopes=["project:default"])); assert result["ready"]; assert not result["automaticPrivilegeEscalationAuthorized"]


def test_hook_contract_allows_published_hook_and_blocks_unknown_hook():
    good=build_hook_contract(HookContractInput(extensionId="example",hook="project.saved",handler="extension.onSaved",capabilityScopes=["project.read"])); assert good["ready"]; bad=build_hook_contract(HookContractInput(extensionId="example",hook="shell.ready",handler="extension.run")); assert not bad["ready"]; assert not bad["automaticHookExecutionAuthorized"]


def test_lifecycle_update_requires_backup_and_approval():
    result=build_lifecycle_plan(LifecyclePlanInput(action="update",manifest=manifest(),compatibility=compatibility(),integrityVerified=True,signatureVerified=True)); codes={x["code"] for x in result["blockers"]}; assert "backup-required" in codes; assert "explicit-approval-required" in codes; assert not result["ready"]


def test_lifecycle_uninstall_requires_exact_phrase():
    result=build_lifecycle_plan(LifecyclePlanInput(action="uninstall",manifest=manifest(),compatibility=compatibility(),backupVerified=True,explicitApproval=True,confirmationPhrase="NO")); assert any(x["code"]=="confirmation-required" for x in result["blockers"]); assert result["requiredConfirmationPhrase"]=="UNINSTALL WORKBENCH EXTENSION"; assert not result["automaticDataDeletionAuthorized"]


def test_sdk_scaffold_contains_manifest_source_tests_and_docs():
    result=build_sdk_scaffold(SDKScaffoldInput(extensionId="example-panel",name="Example Panel",publisher="Developer",language="typescript")); assert "example-panel/extension.json" in result["files"]; assert "example-panel/src/extension.ts" in result["files"]; assert any("tests/" in f for f in result["files"]); assert not result["automaticCodeExecutionAuthorized"]


def test_security_audit_blocks_restricted_source_patterns():
    result=audit_extension(ExtensionAuditInput(manifest=manifest(),sourceFiles=["extension.py"],sourceText="import subprocess; subprocess.run(['sh'])",integrityVerified=True,signatureVerified=True)); assert not result["ready"]; assert any(x["code"]=="shell-process-use" for x in result["findings"]); assert not result["remoteShellAuthorized"]


def test_security_audit_passes_clean_verified_package():
    result=audit_extension(ExtensionAuditInput(manifest=manifest(),sourceFiles=["extension.js"],sourceText="export function activate(api){ return api.project.read(); }",integrityVerified=True,signatureVerified=True)); assert result["ready"]; assert result["humanSecurityReviewRequired"]


def test_extension_package_requires_compatibility_audit_and_files():
    result=build_extension_package(ExtensionPackageInput(manifest=manifest())); assert not result["ready"]; codes={x["code"] for x in result["blockers"]}; assert "compatibility-required" in codes; assert "security-audit-required" in codes; assert "extension-files-required" in codes


def test_extension_package_is_portable_content_addressed_and_noninstalling():
    comp=compatibility(); audit={"ready":True,"auditHash":"a"*64}; result=build_extension_package(ExtensionPackageInput(manifest=manifest(),files={"src/extension.js":"export function activate(){}"},documentation={"README.md":"Example"},tests={"test.js":"ok"},audit=audit,compatibility=comp)); assert result["ready"]; assert result["portable"]; assert len(result["packageHash"])==64; assert len(result["fileHashes"]["src/extension.js"])==64; assert not result["automaticExtensionInstallationAuthorized"]; assert not result["automaticRegistryPublicationAuthorized"]
