from app.erw_v100 import CertificationRequest,certify,status
from app.erw_v080 import compose
from app.erw_v090 import audit,AuditRequest
from test_erw_v080 import fixture as report_fixture

def sample():
    r=report_fixture(); report=compose(r)
    a=audit(AuditRequest(report=report,sourceObjects=r.sourceObjects,
        reviewerNote="Internal synthetic test"))
    return CertificationRequest(objects={**r.sourceObjects,"report":report,"audit":a},
        sourceReference="Synthetic release test, not field verification")
def test_status():assert status()["extensionVersion"]=="1.0.0"
def test_eight_input_objects():assert len(certify(sample())["inputHashes"])==8
def test_deterministic():assert certify(sample())["calculationObjectHash"]==certify(sample())["calculationObjectHash"]
def test_publication_disabled():assert certify(sample())["publicationEnabled"] is False
def test_outbound_disabled():assert certify(sample())["outboundSubmissionEnabled"] is False
def test_not_external_validation():assert certify(sample())["independentScientificValidation"] is False
def test_not_cdr():assert certify(sample())["netDurableAtmosphericRemoval"] is None
def test_not_production_attestation():assert certify(sample())["productionPersistenceCertified"] is False
def test_hash_mutation_detected():
    x=sample();x.objects["scenario"]["scenarios"]="tampered"
    assert "hash-content-scenario" in certify(x)["failedGates"]
def test_lineage_mutation_detected():
    x=sample();x.objects["report"]["sourceHashes"]["scenario"]="invalid"
    assert "report-source-lineage" in certify(x)["failedGates"]
def test_publication_mutation_detected():
    x=sample();x.objects["report"]["publicationEnabled"]=True
    assert "report-unpublished" in certify(x)["failedGates"]
def test_audit_mutation_detected():
    x=sample();x.objects["audit"]["publicationReadiness"]="ready"
    assert "audit-unpublished" in certify(x)["failedGates"]
def test_missing_object_rejected():
    from fastapi import HTTPException
    x=sample();x.objects.pop("audit")
    try:certify(x)
    except HTTPException as e:assert e.status_code==422
    else:assert False
