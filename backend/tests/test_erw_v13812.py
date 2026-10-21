from decimal import Decimal
from fastapi import HTTPException
import pytest
from app import erw_v13812_model as m, erw_v13812_ui as ui
from app.v510 import content_hash
from app.erw_v1381_source import extract_series
def params():
 return m.ScenarioParameters(assumptionNote="Only an illustrative model, not field data.")
def test_model_outputs_and_hash():
 o=m.calculate(params(),"wexford")
 assert o["schema"]==m.SCHEMA
 assert o["verifiedCDR"] is False and o["netDurableAtmosphericRemoval"] is None
 assert o["calculationObjectHash"]==content_hash({k:v for k,v in o.items() if k!="calculationObjectHash"})
 s=extract_series(o)
 assert len(s)==3
 assert s[0]["rateTonnesPerHa"]==0
 assert s[1]["points"][0]["incrementalPotentialProxyTonnesCO2"]==15
 assert s[2]["points"][0]["incrementalPotentialProxyTonnesCO2"]==30
 assert s[1]["points"][1]["incrementalPotentialProxyTonnesCO2"]==pytest.approx(14.25)
def test_changes_to_inputs_change_hash_and_curves():
 a=m.calculate(params(),"wexford")
 x=params().model_copy(update={"annualRealizationFraction":Decimal("0.2")})
 b=m.calculate(x,"wexford")
 assert a["calculationObjectHash"]!=b["calculationObjectHash"]
 assert extract_series(b)[1]["points"][0]["incrementalPotentialProxyTonnesCO2"]==30
def test_invalid_rates():
 with pytest.raises(HTTPException):m.calculate(params().model_copy(update={"ratesTonnesPerHa":[Decimal(10),Decimal(20)]}),"p")
 with pytest.raises(HTTPException):m.calculate(params().model_copy(update={"ratesTonnesPerHa":[Decimal(0),Decimal(0)]}),"p")
def test_preview_never_writes_and_save_creates_snapshot(monkeypatch):
 monkeypatch.setattr(m,"owner_from_auth",lambda v:"owner")
 monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
 saved=[]
 monkeypatch.setattr(m,"save_calculation",lambda req,owner:(saved.append((req,owner)) or {"id":"saved123"}))
 req=params()
 preview=m.preview("wexford",req,"Bearer simulated")
 assert not saved and preview["saved"] is False
 output=m.save("wexford",req,"Bearer simulated")
 assert len(saved)==1 and output["immutableSnapshot"] is True
 assert output["id"]=="saved123" and output["sourceHash"]==preview["visual"]["calculationObjectHash"]
 assert saved[0][0].projectId=="wexford"
def test_ui_integrates_preview_save_and_downloads():
 page=ui.build_page()
 for key in ('id="mpreview"','id="msave"','id="mrefresh"','id="mload"','id="msvg"','id="mpng"','id="mcsv"'):
  assert key in page
 assert "#sc138,#sc1381,#sc13811{display:none}" in page
 assert m.status()["fieldCalibrated"] is False

def test_saved_model_reload_is_hash_and_owner_scoped(monkeypatch):
 obj=m.calculate(params(),"wexford")
 monkeypatch.setattr(m,"owner_from_auth",lambda auth:"owner")
 monkeypatch.setattr(m,"project_for",lambda project,owner:{"id":project})
 monkeypatch.setattr(m,"get_calculation",lambda identifier,owner:{"projectId":"wexford","calculationObject":obj})
 response=m.saved_model("wexford","saved123",obj["calculationObjectHash"],"Bearer simulated")
 assert response["visual"]["calculationObjectHash"]==obj["calculationObjectHash"]
 with pytest.raises(HTTPException) as exc:
  m.saved_model("wexford","saved123","tampered","Bearer simulated")
 assert exc.value.status_code==409
 with pytest.raises(HTTPException) as exc:
  m.saved_model("other","saved123",obj["calculationObjectHash"],"Bearer simulated")
 assert exc.value.status_code==404
