import pytest
from fastapi import HTTPException
from app import erw_v1381_source as s
from app import erw_v1381_ui as ui

def object_with_series():
 return {"views":[{"id":"scenario-trajectories","series":[{"rateTonnesPerHa":0,"points":[{"year":0,"incrementalPotentialProxyTonnesCO2":0},{"year":1,"incrementalPotentialProxyTonnesCO2":0}]},{"rateTonnesPerHa":10,"points":[{"year":0,"incrementalPotentialProxyTonnesCO2":0},{"year":1,"incrementalPotentialProxyTonnesCO2":3.2}]}]}]}

def test_saved_series_only():
 data=s.extract_series(object_with_series())
 assert data[1]["points"][1]["incrementalPotentialProxyTonnesCO2"]==3.2
 assert data[0]["rateTonnesPerHa"]==0

@pytest.mark.parametrize("bad",[-1,float('nan'),float('inf')])
def test_reject_bad_values(bad):
 obj=object_with_series()
 obj["views"][0]["series"][1]["points"][1]["incrementalPotentialProxyTonnesCO2"]=bad
 with pytest.raises(HTTPException):s.extract_series(obj)

def test_missing_view_and_malformed_year():
 with pytest.raises(HTTPException):s.extract_series({"views":[]})
 obj=object_with_series()
 obj["views"][0]["series"][1]["points"][1]["year"]=0
 with pytest.raises(HTTPException):s.extract_series(obj)

def test_ui_and_status():
 page=ui.build_page()
 assert "sc1381sources" in page and "sc1381chart" in page
 assert "sc1381svg" in page and "sc1381csv" in page
 assert "sourceHash" in page
 assert s.status()["verifiedCDR"] is False
 assert s.status()["readOnly"] is True
