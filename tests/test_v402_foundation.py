from backend.app.v402 import (
    GraphIntegrityRequest, CheckpointRequest, ReconciliationRequest, SyncJournalRequest,
    ReceiptVerificationRequest, RecoveryPlanRequest, RetentionPlanRequest, StressEvaluationRequest,
    audit_graph_integrity, build_recovery_checkpoint, build_sync_reconciliation,
    build_sync_journal, verify_sync_receipt, build_interrupted_sync_recovery,
    build_tombstone_retention_plan, evaluate_graph_sync_stress, stable_hash, status,
)


def test_status_declares_hardening_and_safety_boundaries():
    result = status()
    assert result["version"] == "4.0.2"
    assert result["expectedStudioCount"] == 22
    assert result["automaticExecutionAuthorized"] is False
    assert result["automaticRollbackAuthorized"] is False


def test_graph_integrity_passes_connected_acyclic_graph():
    result = audit_graph_integrity(GraphIntegrityRequest(nodes=[{"id":"p"},{"id":"r"}], edges=[{"id":"e","source":"p","target":"r"}], required_roots=["p"]))
    assert result["ok"] is True
    assert result["report"]["componentCount"] == 1


def test_graph_integrity_detects_dangling_and_duplicate_nodes():
    result = audit_graph_integrity(GraphIntegrityRequest(nodes=[{"id":"a"},{"id":"a"}], edges=[{"source":"a","target":"missing"}]))
    codes = {finding["code"] for finding in result["report"]["findings"]}
    assert result["ok"] is False
    assert {"duplicate-node-id", "dangling-edge"}.issubset(codes)


def test_graph_integrity_detects_cycle():
    result = audit_graph_integrity(GraphIntegrityRequest(nodes=[{"id":"a"},{"id":"b"}], edges=[{"source":"a","target":"b"},{"source":"b","target":"a"}]))
    assert result["ok"] is False
    assert result["report"]["cycles"]


def test_checkpoint_is_content_addressed_and_chained():
    result = build_recovery_checkpoint(CheckpointRequest(project_id="p1", records=[{"id":"r1","value":2}], graph={"graphHash":"g"}, previous_checkpoint_hash="old"))
    checkpoint = result["checkpoint"]
    assert checkpoint["previousCheckpointHash"] == "old"
    assert checkpoint["checkpointHash"]
    assert checkpoint["merkleRoot"]


def test_three_way_reconciliation_detects_true_conflict():
    base = [{"id":"r1","value":1}]
    local = [{"id":"r1","value":2}]
    remote = [{"id":"r1","value":3}]
    result = build_sync_reconciliation(ReconciliationRequest(local_records=local, remote_records=remote, base_records=base))
    assert result["ok"] is False
    assert result["plan"]["conflicts"][0]["state"] == "conflict"


def test_reconciliation_allows_safe_non_destructive_copy():
    result = build_sync_reconciliation(ReconciliationRequest(local_records=[{"id":"r1","value":1}], remote_records=[], base_records=[]))
    assert result["plan"]["actions"][0]["action"] == "create-remote"
    assert result["plan"]["actions"][0]["idempotencyKey"]


def test_reconciliation_blocks_overwrite_without_backup():
    base=[{"id":"r1","value":1}]
    result = build_sync_reconciliation(ReconciliationRequest(local_records=[{"id":"r1","value":2}], remote_records=[{"id":"r1","value":3}], base_records=base, strategy="keep-local", backup_verified=False))
    assert result["plan"]["blockedActions"][0]["blockedBy"] == "verified-backup-required"


def test_sync_journal_has_stable_idempotency_and_checkpoint():
    result = build_sync_journal(SyncJournalRequest(project_id="p1", checkpoint_hash="cp", operations=[{"recordId":"r1","action":"update-remote"}]))
    journal = result["journal"]
    assert result["ok"] is True
    assert journal["operations"][0]["idempotencyKey"]
    assert journal["state"] == "prepared"


def test_receipt_verification_accepts_matching_committed_receipt():
    journal = build_sync_journal(SyncJournalRequest(project_id="p1", checkpoint_hash="cp", operations=[{"recordId":"r1","action":"update-remote"}]))["journal"]
    receipt = {"transactionId":journal["transactionId"],"journalHash":journal["journalHash"],"checkpointHash":"cp","state":"committed","operations":[{"status":"verified"}]}
    result = verify_sync_receipt(ReceiptVerificationRequest(journal=journal, receipt=receipt, checkpoint={"checkpointHash":"cp"}))
    assert result["ok"] is True


def test_receipt_verification_rejects_hash_mismatch():
    result = verify_sync_receipt(ReceiptVerificationRequest(journal={"transactionId":"t","journalHash":"j","operationCount":0}, receipt={"transactionId":"t","journalHash":"wrong","state":"committed","operations":[]}))
    assert result["ok"] is False
    assert "journal-hash-mismatch" in result["report"]["findings"]


def test_interrupted_sync_recovery_resumes_idempotently():
    journal={"transactionId":"t","state":"applying","checkpointHash":"cp","journalHash":"j","operationCount":0}
    result=build_interrupted_sync_recovery(RecoveryPlanRequest(journal=journal, checkpoint={"checkpointHash":"cp"}))
    actions={item["action"] for item in result["plan"]["actions"]}
    assert "resume-idempotent-operations" in actions
    assert result["plan"]["automaticRollbackAuthorized"] is False


def test_rollback_requires_backup_and_explicit_authorization():
    journal={"transactionId":"t","state":"applying","checkpointHash":"cp","journalHash":"j","operationCount":0}
    blocked=build_interrupted_sync_recovery(RecoveryPlanRequest(journal=journal, checkpoint={"checkpointHash":"cp"}, backup_verified=False, allow_rollback=True))
    assert blocked["plan"]["blockedActions"]
    allowed=build_interrupted_sync_recovery(RecoveryPlanRequest(journal=journal, checkpoint={"checkpointHash":"cp"}, backup_verified=True, allow_rollback=True))
    assert any(item["action"] == "rollback" for item in allowed["plan"]["actions"])


def test_tombstone_purge_is_blocked_without_backup():
    result=build_tombstone_retention_plan(RetentionPlanRequest(tombstones=[{"id":"r1","ageDays":90}], retention_days=30, backup_verified=False))
    assert result["ok"] is False
    assert result["plan"]["automaticPurgeAuthorized"] is False


def test_stress_evaluation_enforces_duration_and_memory_budgets():
    result=evaluate_graph_sync_stress(StressEvaluationRequest(nodes=100, edges=200, records=100, conflicts=1, duration_seconds=40, peak_memory_mb=600))
    assert result["ok"] is False
    assert len(result["report"]["findings"]) >= 2
