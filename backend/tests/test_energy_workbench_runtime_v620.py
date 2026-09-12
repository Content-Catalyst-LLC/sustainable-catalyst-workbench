import copy
import pytest
from fastapi import HTTPException

from app.energy_runtime_consumer import CONSUMER_CONTRACT
from app.energy_workbench_runtime import framework, plan, execute, validate_result


def handoff(*requests):
    payload = {
        "identity": {"study_id": "study:energy-v130", "question": "Compare explicit energy scenarios"},
        "numeric_registry": {"calculation_requests": []},
        "energy_balance": {"calculation_requests": []},
        "economics": {"calculation_requests": []},
        "bioenergy_and_carbon": {"calculation_requests": []},
        "provenance": [{"source_ref": "source:course-material"}],
        "review": {"human_review_required": True},
    }
    for section, request in requests:
        payload[section]["calculation_requests"].append(request)
    return {
        "schema": "sc-energy-runtime-handoff/1.0",
        "version": "1.3.0",
        "packet": {
            "handoff_id": "es-v130-test",
            "source": {"product": "Library", "subsystem": "Energy Systems Intelligence", "version": "1.3.0"},
            "target": {"key": "workbench", "product": "Workbench", "consumer_contract": CONSUMER_CONTRACT},
            "contract_refs": ["integrated-energy-study-contract", "energy-workbench-runtime/1.0"],
            "payload": payload,
        },
    }


def req(operation, inputs, **extra):
    return {"schema": "sc-energy-workbench-calculation-request/1.0", "operation": operation, "inputs": inputs, **extra}


def test_framework_exposes_fourteen_guarded_operations():
    x = framework()
    assert x["workbench_version"] == "6.2.0"
    assert x["energy_systems_version"] == "1.3.0"
    assert len(x["operations"]) == 14
    assert x["capabilities"]["explicit_input_execution"] is True
    assert x["capabilities"]["automatic_execution_on_consume"] is False
    assert x["capabilities"]["automatic_persistence"] is False
    assert x["capabilities"]["automatic_ranking"] is False
    assert x["capabilities"]["automatic_recommendation"] is False


def test_plan_rejects_missing_explicit_inputs_without_executing():
    body = handoff(("energy_balance", req("capacity-factor-generation", {"capacity_kw": 100, "capacity_factor_pct": 40})))
    x = plan(body)
    assert x["execution_ready"] is False
    assert x["rejected_count"] == 1
    assert "hours" in x["requests"][0]["errors"][0]


def test_unit_conversion_is_deterministic():
    body = handoff(("numeric_registry", req("unit-conversion", {"value": 1, "from_unit": "MWh", "to_unit": "kWh"})))
    a = execute(body)
    b = execute(copy.deepcopy(body))
    assert a["results"][0]["output"]["value"] == "1000"
    assert a["results"][0]["result_id"] == b["results"][0]["result_id"]
    assert a["result_packet_id"] == b["result_packet_id"]


def test_energy_balance_and_generation_arithmetic():
    body = handoff(
        ("energy_balance", req("conversion-chain", {"input_kwh": 1000, "stage_efficiencies_pct": [90, 80]})),
        ("energy_balance", req("capacity-factor-generation", {"capacity_kw": 100, "capacity_factor_pct": 50, "hours": 8760})),
    )
    x = execute(body)
    by_op = {r["operation"]: r["output"] for r in x["results"]}
    assert by_op["conversion-chain"]["final_output_kwh"] == "720"
    assert by_op["capacity-factor-generation"]["generation_kwh"] == "438000"


def test_economics_arithmetic_and_no_ranking():
    body = handoff(
        ("economics", req("simple-payback", {"initial_cost": 10000, "annual_net_savings": 2500, "currency": "USD"})),
        ("economics", req("net-present-value", {"initial_cost": 10000, "annual_net_cash_flow": 3000, "discount_rate_pct": 5, "years": 5, "residual_value": 0, "currency": "USD"})),
    )
    x = execute(body)
    by_op = {r["operation"]: r["output"] for r in x["results"]}
    assert by_op["simple-payback"]["payback_years"] == "4"
    assert float(by_op["net-present-value"]["npv"]) > 0
    assert x["ranking"]["performed"] is False
    assert x["recommendation"]["performed"] is False
    assert x["persistence"]["performed"] is False


def test_bioenergy_and_biochar_boundary():
    body = handoff(
        ("bioenergy_and_carbon", req("feedstock-energy", {"mass_tonnes": 10, "energy_content_kwh_per_tonne": 4000, "conversion_efficiency_pct": 75})),
        ("bioenergy_and_carbon", req("biochar-carbon", {"biochar_mass_kg": 100, "carbon_fraction_pct": 80, "stable_fraction_pct": 70})),
    )
    x = execute(body)
    by_op = {r["operation"]: r["output"] for r in x["results"]}
    assert by_op["feedstock-energy"]["useful_energy_kwh"] == "30000"
    assert by_op["biochar-carbon"]["stable_carbon_mass_kg_c"] == "56"
    assert "not a removal" in by_op["biochar-carbon"]["claim_boundary"]


def test_cost_efficiency_requires_explicit_nonzero_denominator():
    body = handoff(("economics", req("cost-efficiency", {"total_cost": 100, "energy_saved_kwh": 0, "co2e_avoided_kg": 0, "currency": "USD"})))
    with pytest.raises(HTTPException) as exc:
        execute(body)
    assert exc.value.status_code == 422
    assert "denominator" in str(exc.value.detail)


def test_validate_result_accepts_runtime_output():
    body = handoff(("energy_balance", req("supply-demand-balance", {"domestic_supply_kwh": 100, "imports_kwh": 10, "storage_discharge_kwh": 0, "final_demand_kwh": 100, "exports_kwh": 0, "storage_charge_kwh": 0, "losses_kwh": 10, "tolerance_kwh": 0})))
    packet = execute(body)
    validation = validate_result(packet)
    assert validation["valid"] is True
    assert validation["result_count"] == 1
