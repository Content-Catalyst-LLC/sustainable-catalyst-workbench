from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.erw_v070 import DiagramRequest,Location,assemble,status
from app.erw_v010 import PROJECT_KEY

def fixture():
    v={"schema":"sc.erw.visual-research-package.v0.6.0",
       "researchId":PROJECT_KEY,"calculationObjectHash":"a"*64,
       "verifiedCDR":False,"netDurableAtmosphericRemoval":None,
       "views":[{"id":x} for x in ("scenario-trajectories","lifecycle-breakdown","uncertainty-intervals","sensitivity-ranking","mrv-evidence-matrix")]}
    return DiagramRequest(visualization=v,locations=[
      Location(locationId="wexford-demo",label="Illustrative Wexford marker",
       latitude="52.33",longitude="-6.46",coordinateSource="Synthetic sample point",
       evidenceClass="hypothetical",limitations="Not field validated")],
       sourceReference="Synthetic teaching scenario, no field evidence")

def test_status():assert status()["extensionVersion"]=="0.7.0"
def test_equations():assert len(assemble(fixture())["equations"])==4
def test_map():assert assemble(fixture())["map"]["crs"]=="EPSG:4326"
def test_flow():assert len(assemble(fixture())["materialFlow"]["edges"])==5
def test_no_cdr():
    obj=assemble(fixture())
    assert obj["netDurableAtmosphericRemoval"] is None
    assert obj["verifiedCDR"] is False
def test_repeat_hash():assert assemble(fixture())["calculationObjectHash"]==assemble(fixture())["calculationObjectHash"]
def test_source_reference():assert assemble(fixture())["sourceVisualHash"]=="a"*64
def test_out_of_range_lat():
    a=fixture();a.locations[0].latitude="91"
    with pytest.raises(HTTPException):assemble(a)
def test_out_of_range_lon():
    a=fixture();a.locations[0].longitude="181"
    with pytest.raises(HTTPException):assemble(a)
def test_nan_rejected():
    a=fixture();a.locations[0].longitude="NaN"
    with pytest.raises(HTTPException):assemble(a)
def test_duplicate_location_rejected():
    a=fixture();a.locations.append(a.locations[0])
    with pytest.raises(HTTPException):assemble(a)
def test_wrong_schema_rejected():
    a=fixture();a.visualization["schema"]="other"
    with pytest.raises(HTTPException):assemble(a)
def test_missing_view_rejected():
    a=fixture();a.visualization["views"].pop()
    with pytest.raises(HTTPException):assemble(a)
def test_verified_claim_rejected():
    a=fixture();a.visualization["verifiedCDR"]=True
    with pytest.raises(HTTPException):assemble(a)
def test_no_verified_geo():assert assemble(fixture())["map"]["siteLocationsVerified"] is False
def test_material_flow_not_certified():assert assemble(fixture())["materialFlow"]["noCertifiedRemovalFlow"] is True
