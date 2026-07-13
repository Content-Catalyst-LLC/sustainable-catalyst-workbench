from app.v330 import (
    EvidenceRecord, EvidenceNormalizeRequest, HandoffRequest, CompatibilityRequest,
    BundleRequest, EvidenceMergeRequest, ReceiptRequest, ProjectLinkRequest,
    normalize_evidence, build_handoff_packet, compatibility_report,
    build_portable_bundle, merge_evidence, build_receipt, build_project_link,
)


def evidence(eid="ev-1", title="Indicator evidence", summary="A measured indicator"):
    return EvidenceRecord(
        evidence_id=eid, title=title, summary=summary, originating_app="site-intelligence",
        source_type="indicator", source_url="https://example.org/indicator", project_id="kenya-water",
        citations=[{"title": "Source", "url": "https://example.org/source"}],
        methods=["public API retrieval"], data_quality="reviewed", uncertainty="moderate",
    )


def handoff():
    return HandoffRequest(
        source_app="site-intelligence", target_app="workbench", project_id="kenya-water",
        handoff_type="site-intelligence-to-workbench", title="Water indicators",
        objective="Model monitoring options", evidence=[evidence()],
        payload={"capabilities": ["evidence", "datasets"], "dataset": {"rows": 12}},
        schema_versions={"site-intelligence": "2.0.0", "workbench": "3.3.0"},
    )


def test_normalize_evidence_hashes_and_preserves_provenance():
    result = normalize_evidence(evidence())
    assert result["schema"] == "sc-workbench-shared-evidence/1.0"
    assert result["evidence_hash"]
    assert result["provenance"][-1]["event"] == "normalized"
    assert result["originating_app"] == "site-intelligence"


def test_site_intelligence_handoff_is_compatible():
    report = compatibility_report(CompatibilityRequest(handoff=handoff()))
    assert report["compatible"] is True
    assert report["missingFromSource"] == []
    assert report["missingFromTarget"] == []
    assert report["compatibilityHash"]


def test_handoff_packet_contains_shared_evidence_and_hash():
    result = build_handoff_packet(handoff())
    packet = result["packet"]
    assert packet["sourceApp"] == "site-intelligence"
    assert packet["targetApp"] == "workbench"
    assert packet["evidenceIds"] == ["ev-1"]
    assert packet["reviewState"] == "human-review-required"
    assert packet["packetHash"]


def test_portable_bundle_links_manifest_to_packet():
    result = build_portable_bundle(BundleRequest(handoff=handoff()))
    bundle = result["bundle"]
    assert bundle["manifest"]["packetHash"] == bundle["handoff"]["packetHash"]
    assert bundle["manifest"]["manifestHash"]
    assert result["bundleHash"]


def test_evidence_merge_flags_same_id_with_different_content():
    result = merge_evidence(EvidenceMergeRequest(
        existing=[evidence(summary="First")], incoming=[evidence(summary="Changed")]
    ))
    assert result["manualReviewRequired"] is True
    assert result["conflicts"][0]["evidenceId"] == "ev-1"


def test_receipt_is_hashed_and_references_packet():
    packet = build_handoff_packet(handoff())["packet"]
    result = build_receipt(ReceiptRequest(
        packet_hash=packet["packetHash"], target_app="workbench", status="accepted",
        accepted_evidence_ids=["ev-1"], target_record_id="wb-project-1"
    ))
    assert result["receipt"]["packetHash"] == packet["packetHash"]
    assert result["receiptHash"]


def test_cross_application_project_link_is_hashed():
    result = build_project_link(ProjectLinkRequest(
        source_app="workbench", target_app="decision-studio",
        source_project_id="project-1", target_project_id="decision-9", packet_hash="abc123"
    ))
    assert result["link"]["sourceProjectId"] == "project-1"
    assert result["link"]["targetProjectId"] == "decision-9"
    assert result["linkHash"]
