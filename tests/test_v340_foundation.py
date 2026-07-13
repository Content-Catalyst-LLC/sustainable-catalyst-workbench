from app.v340 import (
    Reviewer, ReviewItem, ReviewComment, ChangeRequest, ReviewBuildRequest,
    QueueRequest, RevisionCompareRequest, TraceabilityRequest, SnapshotRequest,
    SignoffRequest, DossierRequest, build_review_record, build_review_queue,
    compare_revisions, build_traceability_matrix, build_review_snapshot,
    build_signoff, build_review_dossier,
)


def review_request():
    return ReviewBuildRequest(
        project_id="project-1", title="Engineering review", revision="2", state="in-review",
        reviewers=[Reviewer(reviewer_id="reviewer-1", display_name="Reviewer", role="reviewer")],
        items=[ReviewItem(record_id="calc-1", record_type="calculation", revision="2", criticality="high", requirement_ids=["REQ-1"])],
        comments=[ReviewComment(reviewer_id="reviewer-1", target_record_id="calc-1", body="Check units")],
        change_requests=[ChangeRequest(title="Correct units", target_record_id="calc-1", priority="high")],
        requirement_ids=["REQ-1", "REQ-2"],
    )


def test_review_record_is_hashed_and_counts_open_work():
    result = build_review_record(review_request())
    assert result["review"]["reviewHash"]
    assert result["review"]["metrics"]["openCommentCount"] == 1
    assert result["review"]["metrics"]["openChangeCount"] == 1
    assert result["review"]["professionalCertification"] is False


def test_review_queue_prioritizes_critical_changes():
    a = build_review_record(review_request())["review"]
    critical_req = review_request()
    critical_req.title = "Critical review"
    critical_req.change_requests = [ChangeRequest(title="Safety issue", priority="critical")]
    b = build_review_record(critical_req)["review"]
    queue = build_review_queue(QueueRequest(reviews=[a, b], states=["in-review"]))
    assert queue["reviews"][0]["title"] == "Critical review"
    assert queue["queueHash"]


def test_revision_comparison_reports_modified_and_added_paths():
    result = compare_revisions(RevisionCompareRequest(left={"a": 1}, right={"a": 2, "b": 3}))
    assert result["changeCount"] == 2
    assert {item["change"] for item in result["changes"]} == {"modified", "added"}


def test_traceability_flags_uncovered_requirement():
    review = build_review_record(review_request())["review"]
    result = build_traceability_matrix(TraceabilityRequest(requirements=[{"id": "REQ-1"}, {"id": "REQ-2", "critical": True}], reviews=[review]))
    assert result["coveragePercent"] == 50.0
    assert result["criticalUncoveredRequirementIds"] == ["req-2"]


def test_snapshot_is_immutable_and_chained():
    result = build_review_snapshot(SnapshotRequest(review=review_request(), previous_snapshot_hash="previous", locked_by="reviewer-1"))
    assert result["snapshot"]["immutable"] is True
    assert result["snapshot"]["previousSnapshotHash"] == "previous"
    assert result["snapshotHash"]


def test_internal_signoff_is_not_professional_certification():
    snap = build_review_snapshot(SnapshotRequest(review=review_request()))["snapshotHash"]
    result = build_signoff(SignoffRequest(snapshot_hash=snap, reviewer=Reviewer(reviewer_id="approver", display_name="Approver", role="approver"), decision="returned-for-changes", rationale="Revise units"))
    assert result["signoff"]["professionalCertification"] is False


def test_qualified_review_requires_credential_reference():
    snap = build_review_snapshot(SnapshotRequest(review=review_request()))["snapshotHash"]
    try:
        build_signoff(SignoffRequest(snapshot_hash=snap, reviewer=Reviewer(reviewer_id="engineer", display_name="Engineer", role="approver"), decision="approved", rationale="Reviewed", scope="qualified-professional-review"))
    except ValueError as error:
        assert "credential_reference" in str(error)
    else:
        raise AssertionError("credential requirement was not enforced")


def test_approval_is_blocked_by_critical_changes():
    snap = build_review_snapshot(SnapshotRequest(review=review_request()))["snapshotHash"]
    try:
        build_signoff(SignoffRequest(snapshot_hash=snap, reviewer=Reviewer(reviewer_id="approver", display_name="Approver", role="approver"), decision="approved", rationale="Approved", unresolved_critical_changes=1))
    except ValueError as error:
        assert "critical change" in str(error)
    else:
        raise AssertionError("critical-change safeguard was not enforced")


def test_review_dossier_includes_review_and_hash():
    result = build_review_dossier(DossierRequest(review=review_request()))
    assert result["dossier"]["review"]["title"] == "Engineering review"
    assert result["dossierHash"]
