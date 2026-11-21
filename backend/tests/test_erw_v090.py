import pytest
from fastapi import HTTPException
from app.erw_v090 import AuditRequest,Claim,audit,status
from app.erw_v080 import compose
from test_erw_v080 import fixture as report_fixture

def sample():
    r=report_fixture()
    report=compose(r)
    return AuditRequest(report=report,sourceObjects=r.sourceObjects,
       reviewerNote="Internal consistency audit; not external scientific validation",
       claims=[Claim(claimId="C1",statement="Modeled proxy is illustrative only",
          sourceKinds=["scenario","lifecycle"],evidenceStatus="derived",
          limitations="No direct atmospheric carbon flux measurement")])

def test_status():assert status()["extensionVersion"]=="0.9.0"
def test_report_hash():assert audit(sample())["reportHash"]
def test_claims():assert len(audit(sample())["claimTrace"])==1
def test_sources():assert len(audit(sample())["sourceHashes"])==6
def test_unpublished():assert audit(sample())["publicationEnabled"] is False
def test_readiness():assert audit(sample())["publicationReadiness"]=="not-ready"
def test_nonverification():assert audit(sample())["netDurableAtmosphericRemoval"] is None
def test_stable_hash():assert audit(sample())["calculationObjectHash"]==audit(sample())["calculationObjectHash"]
def test_source_tamper():
    a=sample();a.sourceObjects["scenario"]["inputs"]["compositionCalculationHash"]="changed"
    assert any(x["id"]=="source-hash-scenario" for x in audit(a)["findings"])
def test_report_tamper():
    a=sample();a.report["title"]="Altered title"
    assert any(x["id"]=="report-hash" for x in audit(a)["findings"])
def test_missing_source():
    a=sample();a.sourceObjects.pop("scenario")
    with pytest.raises(HTTPException):audit(a)
def test_unknown_claim_kind():
    a=sample();a.claims[0].sourceKinds=["fantasy"]
    with pytest.raises(HTTPException):audit(a)
def test_duplicate_claim_id():
    a=sample();a.claims.append(a.claims[0])
    with pytest.raises(HTTPException):audit(a)
def test_false_external_verification():
    a=sample();a.claims[0].evidenceStatus="independently-verified"
    assert any(x["id"]=="claim-C1" for x in audit(a)["findings"])
def test_claims_missing():
    a=sample();a.claims=[]
    assert any(x["id"]=="claims-missing" for x in audit(a)["findings"])
def test_publication_gate():
    a=sample();a.report["publicationEnabled"]=True
    assert any(x["id"]=="publication-gate" for x in audit(a)["findings"])
def test_lineage_mismatch():
    a=sample();a.report["sourceHashes"]["scenario"]="other"
    assert any(x["id"]=="report-lineage" for x in audit(a)["findings"])
def test_schema_rejected():
    a=sample();a.report["schema"]="invalid"
    with pytest.raises(HTTPException):audit(a)
