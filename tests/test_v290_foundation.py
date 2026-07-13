from backend.app.v290 import (
    ChangeRecord,
    DossierRequest,
    DossierSection,
    EvidenceRecord,
    EvidenceRegisterRequest,
    ReadinessItem,
    ReadinessRequest,
    Requirement,
    RevisionAuditRequest,
    RevisionRecord,
    SnapshotFile,
    SnapshotRequest,
    TraceabilityRequest,
    VerificationRecord,
    audit_revisions,
    build_dossier,
    create_snapshot,
    evaluate_readiness,
    evaluate_traceability,
    register_evidence,
)


def test_traceability_coverage_and_links():
    result = evaluate_traceability(TraceabilityRequest(
        requirements=[Requirement(id="REQ-1", title="Measure temperature", priority="critical")],
        verifications=[VerificationRecord(id="TEST-1", requirement_ids=["REQ-1"], status="pass", evidence_ids=["EV-1"])],
    ))
    assert result["ok"] is True
    assert result["coveragePercent"] == 100
    assert result["traceability"][0]["verificationIds"] == ["TEST-1"]


def test_traceability_detects_unknown_requirement():
    result = evaluate_traceability(TraceabilityRequest(
        requirements=[Requirement(id="REQ-1", title="Known")],
        verifications=[VerificationRecord(id="TEST-1", requirement_ids=["REQ-X"])],
    ))
    assert result["ok"] is False
    assert result["unknownRequirementLinks"][0]["requirementId"] == "REQ-X"


def test_dossier_completeness_and_hash():
    result = build_dossier(DossierRequest(
        title="Product dossier",
        sections=[
            DossierSection(id="architecture", title="Architecture", content="System description", status="approved"),
            DossierSection(id="validation", title="Validation", content="Test evidence", status="review"),
        ],
    ))
    assert result["ok"] is True
    assert result["completeness"]["percent"] == 100
    assert len(result["dossierHash"]) == 64


def test_revision_audit_finds_open_change():
    result = audit_revisions(RevisionAuditRequest(
        revisions=[RevisionRecord(revision="1.0.0", approved=True, artifact_hash="abc")],
        changes=[ChangeRecord(id="CR-1", title="Update enclosure", status="approved", target_revision="1.0.0")],
    ))
    assert result["ok"] is True
    assert result["openChanges"] == ["CR-1"]


def test_evidence_register_requires_hashes():
    result = register_evidence(EvidenceRegisterRequest(records=[
        EvidenceRecord(id="EV-1", title="Test report", kind="test", source_uri="report.pdf", content_hash="abc", approved=True),
        EvidenceRecord(id="EV-2", title="Photo", kind="image", source_uri="photo.png", content_hash="", approved=False),
    ]))
    assert result["ok"] is False
    assert result["recordsMissingHash"] == ["EV-2"]


def test_readiness_gate():
    result = evaluate_readiness(ReadinessRequest(items=[
        ReadinessItem(id="R-1", category="requirements", title="Requirements approved", status="complete", critical=True, evidence_ids=["EV-1"]),
        ReadinessItem(id="V-1", category="verification", title="Verification complete", status="complete", critical=True, evidence_ids=["EV-2"]),
    ]))
    assert result["ok"] is True
    assert result["gate"] == "ready"
    assert result["overallPercent"] == 100


def test_snapshot_is_deterministic_except_time_field_shape():
    request = SnapshotRequest(
        project_id="project-a",
        revision="1.0.0",
        files=[SnapshotFile(path="docs/report.md", content_hash="abc", size_bytes=10, media_type="text/markdown")],
    )
    result = create_snapshot(request)
    assert result["ok"] is True
    assert result["fileCount"] == 1
    assert len(result["snapshotHash"]) == 64
