from backend.app.v430 import (
    SourceInput, ConnectorPlanInput, ConnectorHealthInput, DatasetManifestInput,
    PipelineInput, PipelineStep, ValidationInput, FreshnessInput, CacheInput,
    RefreshInput, SnapshotInput, ProvenanceInput, PackageInput,
    status_record, normalize_source, connector_plan, connector_health,
    dataset_manifest, pipeline_plan, validate_dataset, freshness_report,
    cache_plan, refresh_plan, build_snapshot, build_provenance, build_package,
)


def test_status_boundaries():
    result=status_record(); assert result["version"]=="4.3.0"; assert result["expectedStudioCount"]==25; assert not result["automaticNetworkFetchAuthorized"]

def test_source_https_and_allowlist():
    result=normalize_source(SourceInput(title="A",connectorType="https-json",url="https://data.example/a",allowedHosts=["data.example"],license="CC0")); assert result["ready"]; assert len(result["sourceHash"])==64

def test_source_blocks_http():
    result=normalize_source(SourceInput(title="A",connectorType="https-json",url="http://data.example/a")); assert not result["ready"]; assert any(x["code"]=="https-required" for x in result["findings"])

def test_source_blocks_embedded_secret_flag():
    result=normalize_source(SourceInput(title="A",connectorType="manual-snapshot",containsSecrets=True)); assert not result["ready"]

def test_connector_plan_is_explicit():
    source=SourceInput(title="A",connectorType="https-csv",url="https://data.example/a.csv",allowedHosts=["data.example"]); result=connector_plan(ConnectorPlanInput(source=source,previousEtag='"abc"')); assert result["conditionalHeaders"]["If-None-Match"]=='"abc"'; assert not result["automaticNetworkFetchAuthorized"]

def test_health_states():
    assert connector_health(ConnectorHealthInput(sourceId="a",statusCode=200))["status"]=="healthy"; assert connector_health(ConnectorHealthInput(sourceId="a",error="timeout"))["status"]=="unavailable"

def test_manifest_stable_hash():
    payload=DatasetManifestInput(title="D",sourceIds=["b","a"],columns=[{"name":"v"}],rowCount=2,generatedAt="2026-01-01T00:00:00+00:00"); assert dataset_manifest(payload)["manifestHash"]==dataset_manifest(payload)["manifestHash"]

def test_pipeline_detects_duplicate_steps():
    payload=PipelineInput(datasetId="d",steps=[PipelineStep(stepId="x",operation="select"),PipelineStep(stepId="x",operation="sort")]); result=pipeline_plan(payload); assert not result["ready"]; assert any(x["code"]=="duplicate-step" for x in result["findings"])

def test_pipeline_detects_cycle():
    payload=PipelineInput(datasetId="d",steps=[PipelineStep(stepId="a",operation="select",dependsOn=["b"]),PipelineStep(stepId="b",operation="sort",dependsOn=["a"])]); assert not pipeline_plan(payload)["ready"]

def test_validation_required_and_duplicate_key():
    payload=ValidationInput(records=[{"id":1},{"id":1,"v":2}],schemaFields=[{"name":"v","required":True}],primaryKey="id"); result=validate_dataset(payload); assert not result["valid"]; assert result["errorCount"]==2

def test_freshness_states():
    result=freshness_report(FreshnessInput(observedAt="2026-01-01T00:00:00+00:00",evaluatedAt="2026-01-01T00:30:00+00:00",maxAgeSeconds=3600)); assert result["state"]=="fresh"; assert not result["automaticRefreshAuthorized"]

def test_cache_plan_safety():
    result=cache_plan(CacheInput(sourceId="a",etag="e")); assert result["conditionalRequest"]; assert not result["automaticCacheDeletionAuthorized"]

def test_refresh_dependency_order():
    result=refresh_plan(RefreshInput(sourceIds=["derived","base"],dependencies={"derived":["base"]})); assert result["refreshOrder"].index("base")<result["refreshOrder"].index("derived")

def test_snapshot_and_provenance_hashes():
    snap=build_snapshot(SnapshotInput(manifest={"datasetId":"d"},records=[{"x":1}])); assert snap["recordCount"]==1 and len(snap["snapshotHash"])==64; prov=build_provenance(ProvenanceInput(datasetId="d",sourceRecords=[{"id":"s"}],outputRecords=[{"id":"o"}])); assert prov["complete"]

def test_package_is_portable_and_nonexecuting():
    result=build_package(PackageInput(manifest={},pipeline={},provenance={},validation={})); assert result["portable"]; assert not result["automaticPublicationAuthorized"]; assert not result["automaticExecutionAuthorized"]
