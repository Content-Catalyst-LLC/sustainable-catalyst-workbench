from app import erw_v138 as m
def test_page_contains_both_interactive_visualizations():
    h=m.build_page()
    for token in ("sc138plot","sc138path","sc138dose","sc138year","sc138decay","sc138svg","sc138pathsvg","sc138csv"):
        assert token in h
    assert h.count("el('addsection').onclick=")==1
def test_no_false_carbon_claims():
    h=m.build_page()
    assert "Dimensionless demonstration only" in h
    assert "NOT verified CDR" in h
    assert "Dissolution ≠ additional atmospheric capture" in h
    assert m.status()["empiricalCarbonEstimation"] is False
    assert m.status()["verifiedCDR"] is False
    assert m.status()["savedDataMutated"] is False
def test_status_and_http():
    assert m.report().status_code==200
    assert m.status()["extensionVersion"]=="1.3.8"
