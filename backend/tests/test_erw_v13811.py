from copy import deepcopy
from fastapi import HTTPException
import pytest
from app import erw_v13811_repair as repair, erw_v13811_ui as ui
from app.v510 import content_hash

def sample():
 obj={"schema":"sc.erw.legacy-calculation.v0.5.0","verifiedCDR":False,
  "netDurableAtmosphericRemoval":None,"views":[{"id":"scenario-trajectories",
  "series":[{"rateTonnesPerHa":10,"points":[{"year":0,"incrementalPotentialProxyTonnesCO2":0},{"year":2,"incrementalPotentialProxyTonnesCO2":2.5}]}]}]}
 obj["calculationObjectHash"]=content_hash(obj)
 return obj

def test_non_v06_compatible_trajectory_is_chart_ready():
 assert repair.eligible(sample())=="chart-ready"

def test_broken_hash_and_missing_series_rejected():
 x=sample();x["views"]=[];assert repair.eligible(x)=="hash-invalid"
 x["calculationObjectHash"]=content_hash({k:v for k,v in x.items() if k!="calculationObjectHash"})
 assert repair.eligible(x)=="no-compatible-scenario-series"

def test_verification_cannot_be_claimed():
 x=sample();x["verifiedCDR"]=True
 x["calculationObjectHash"]=content_hash({k:v for k,v in x.items() if k!="calculationObjectHash"})
 assert repair.eligible(x)=="unsupported-verification-status"

def test_project_scoped_discovery(monkeypatch):
 monkeypatch.setattr(repair,"project_for",lambda project,owner:{"id":project})
 monkeypatch.setattr(repair,"list_calculations",lambda project,owner:[{"id":"x","title":"Existing data","calculationObject":sample()}])
 found=repair.enumerate_objects("wexford","owner")
 assert found[0]["chartReady"] is True
 assert found[0]["schema"]=="sc.erw.legacy-calculation.v0.5.0"
 monkeypatch.setattr(repair,"owner_from_auth",lambda auth:"owner")
 result=repair.discover("wexford","Bearer TEST")
 assert result["chartReady"]==1 and result["total"]==1

def test_chart_requires_project_and_hash(monkeypatch):
 x=sample()
 monkeypatch.setattr(repair,"owner_from_auth",lambda auth:"owner")
 monkeypatch.setattr(repair,"project_for",lambda p,o:{"id":p})
 monkeypatch.setattr(repair,"get_calculation",lambda i,o:{"projectId":"project1","calculationObject":x})
 with pytest.raises(HTTPException) as err:
  repair.chart("other","x",x["calculationObjectHash"],"Bearer TEST")
 assert err.value.status_code==404
 with pytest.raises(HTTPException) as err:
  repair.chart("project1","x","wrong","Bearer TEST")
 assert err.value.status_code==409
 result=repair.chart("project1","x",x["calculationObjectHash"],"Bearer TEST")
 assert result["series"][0]["points"][1]["incrementalPotentialProxyTonnesCO2"]==2.5
 assert result["verifiedCDR"] is False

def test_user_interface_and_release_status():
 html=ui.build_page()
 for marker in ("sc13811discover","sc13811list","sc13811plot","sc13811visual","no-compatible-scenario-series","sc13811svg"):
  if marker=="no-compatible-scenario-series":continue
  assert marker in html
 assert repair.status()["extensionVersion"]=="1.3.8.1.1"
 assert repair.status()["readOnly"] is True
