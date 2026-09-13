from app.energy_runtime_consumer import CONSUMER_CONTRACT
from app.energy_workbench_runtime import execute, framework, validate_result


def handoff(*requests):
    payload={"identity":{"study_id":"grid-v160","question":"Explicit adequacy scenario"},"numeric_registry":{"calculation_requests":[]},"energy_balance":{"calculation_requests":[]},"economics":{"calculation_requests":[]},"bioenergy_and_carbon":{"calculation_requests":[]},"grid_storage_reliability":{"calculation_requests":[]},"provenance":[{"source_ref":"scenario:test"}],"review":{"human_review_required":True}}
    for request in requests: payload["grid_storage_reliability"]["calculation_requests"].append(request)
    return {"schema":"sc-energy-runtime-handoff/1.0","version":"1.6.0","packet":{"handoff_id":"grid-v160-test","source":{"product":"Library","subsystem":"Energy Systems Intelligence","version":"1.6.0"},"target":{"key":"workbench","product":"Workbench","consumer_contract":CONSUMER_CONTRACT},"contract_refs":["energy-grid-storage-reliability/1.0"],"payload":payload}}


def req(op,inputs): return {"operation":op,"inputs":inputs}


def outputs(*requests):
    p=execute(handoff(*requests)); assert validate_result(p)["valid"] is True
    return {r["operation"]:r["output"] for r in p["results"]}


def test_framework_v630_grid_operations():
    f=framework(); assert f["workbench_version"]=="6.3.0"; assert f["energy_systems_version"]=="1.6.0"
    grid=[x for x in f["operations"] if x["section"]=="grid_storage_reliability"]
    assert len(grid)==7
    assert f["capabilities"]["automatic_execution_on_consume"] is False


def test_storage_round_trip_and_soc_trajectory():
    o=outputs(req("storage-round-trip",{"charged_energy_kwh":100,"charge_efficiency_pct":90,"discharge_efficiency_pct":90}),req("storage-soc-trajectory",{"energy_capacity_kwh":100,"initial_soc_kwh":50,"minimum_soc_kwh":10,"maximum_charge_kw":50,"maximum_discharge_kw":50,"charge_efficiency_pct":90,"discharge_efficiency_pct":90,"timestep_hours":1,"net_surplus_kw_series":[20,-30,-40,50]}))
    assert o["storage-round-trip"]["delivered_energy_kwh"]=="81"
    assert o["storage-round-trip"]["round_trip_efficiency_pct"]=="81"
    assert len(o["storage-soc-trajectory"]["steps"])==4
    assert float(o["storage-soc-trajectory"]["ending_soc_kwh"]) >= 10


def test_reserve_and_peak_coverage():
    o=outputs(req("reserve-margin",{"dependable_capacity_kw":120,"peak_demand_kw":100}),req("peak-demand-coverage",{"available_generation_kw":90,"storage_discharge_kw":15,"peak_demand_kw":100}))
    assert o["reserve-margin"]["reserve_margin_pct"]=="20"
    assert o["peak-demand-coverage"]["peak_covered"] is True
    assert o["peak-demand-coverage"]["headroom_kw"]=="5"


def test_loss_of_load_ens_and_adequacy():
    inputs={"demand_kw_series":[100,120,130,90,110],"available_capacity_kw_series":[110,100,100,100,100],"timestep_hours":1}
    o=outputs(req("loss-of-load-events",inputs),req("energy-not-served",inputs),req("adequacy-timeseries",inputs))
    assert o["loss-of-load-events"]["loss_of_load_events"]==2
    assert o["loss-of-load-events"]["loss_of_load_hours"]=="3"
    assert o["energy-not-served"]["energy_not_served_kwh"]=="60"
    assert o["adequacy-timeseries"]["reliability_declaration_performed"] is False
    assert o["adequacy-timeseries"]["outage_prediction_performed"] is False
