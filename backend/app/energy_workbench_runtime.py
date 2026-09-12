from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
try:
    from pint import UnitRegistry
except ImportError:  # validation environments may not install optional scientific dependencies
    UnitRegistry = None  # type: ignore[assignment]

from .energy_runtime_consumer import _unwrap, _validate, CONSUMER_CONTRACT, HANDOFF_SCHEMA

RUNTIME_VERSION = "6.2.0"
ENERGY_SYSTEMS_VERSION = "1.3.0"
EXECUTION_SCHEMA = "sc-energy-workbench-execution-result/1.0"
RESULT_PACKET_SCHEMA = "sc-energy-workbench-result-packet/1.0"
PLAN_SCHEMA = "sc-energy-workbench-execution-plan/1.0"
REQUEST_SCHEMA = "sc-energy-workbench-calculation-request/1.0"
BOUNDARY = (
    "Workbench executes only explicit caller-supplied arithmetic. It does not infer missing inputs, "
    "select technology assumptions, rank alternatives, recommend a winner, claim avoided emissions, "
    "create carbon credits, fetch market prices, or persist the study automatically."
)

router = APIRouter(prefix="/v1/energy-runtime", tags=["energy-workbench-runtime"])
_UREG = UnitRegistry(autoconvert_offset_to_baseunit=True) if UnitRegistry is not None else None
_EXACT_ENERGY_TO_JOULE = {
    "j": Decimal("1"), "joule": Decimal("1"), "joules": Decimal("1"),
    "kj": Decimal("1000"), "kilojoule": Decimal("1000"), "kilojoules": Decimal("1000"),
    "mj": Decimal("1000000"), "megajoule": Decimal("1000000"), "megajoules": Decimal("1000000"),
    "gj": Decimal("1000000000"), "gigajoule": Decimal("1000000000"), "gigajoules": Decimal("1000000000"),
    "wh": Decimal("3600"), "watt_hour": Decimal("3600"), "watt-hour": Decimal("3600"),
    "kwh": Decimal("3600000"), "kilowatt_hour": Decimal("3600000"), "kilowatt-hour": Decimal("3600000"),
    "mwh": Decimal("3600000000"), "megawatt_hour": Decimal("3600000000"), "megawatt-hour": Decimal("3600000000"),
    "gwh": Decimal("3600000000000"), "gigawatt_hour": Decimal("3600000000000"), "gigawatt-hour": Decimal("3600000000000"),
}

SECTIONS = ("numeric_registry", "energy_balance", "economics", "bioenergy_and_carbon")

OPERATION_SPECS: dict[str, dict[str, Any]] = {
    "unit-conversion": {
        "section": "numeric_registry",
        "required": ("value", "from_unit", "to_unit"),
        "formula": "result = convert(value, from_unit, to_unit)",
        "contract": "energy-conversion-contract",
    },
    "conversion-chain": {
        "section": "energy_balance",
        "required": ("input_kwh", "stage_efficiencies_pct"),
        "formula": "stage_output = stage_input × efficiency; loss = stage_input − stage_output",
        "contract": "conversion-chain-model",
    },
    "supply-demand-balance": {
        "section": "energy_balance",
        "required": ("domestic_supply_kwh", "imports_kwh", "storage_discharge_kwh", "final_demand_kwh", "exports_kwh", "storage_charge_kwh", "losses_kwh", "tolerance_kwh"),
        "formula": "available_supply = domestic + imports + discharge; residual = available_supply − accounted_outflows",
        "contract": "energy-balance-calculation-contract",
    },
    "capacity-factor-generation": {
        "section": "energy_balance",
        "required": ("capacity_kw", "capacity_factor_pct", "hours"),
        "formula": "generation_kwh = capacity_kw × hours × capacity_factor_pct / 100",
        "contract": "capacity-factor-generation-estimate",
    },
    "energy-cost-comparison": {
        "section": "economics",
        "required": ("baseline_energy_kwh", "baseline_price_per_kwh", "candidate_energy_kwh", "candidate_price_per_kwh", "baseline_fixed_cost", "candidate_fixed_cost", "currency"),
        "formula": "cost = energy × unit_price + fixed_cost",
        "contract": "energy-cost-comparison-result",
    },
    "simple-payback": {
        "section": "economics",
        "required": ("initial_cost", "annual_net_savings", "currency"),
        "formula": "payback_years = initial_cost / annual_net_savings when savings > 0",
        "contract": "energy-simple-payback-result",
    },
    "net-present-value": {
        "section": "economics",
        "required": ("initial_cost", "annual_net_cash_flow", "discount_rate_pct", "years", "residual_value", "currency"),
        "formula": "NPV = −initial_cost + Σ(cash_flow/(1+r)^t) + residual/(1+r)^n",
        "contract": "energy-npv-result",
    },
    "cost-benefit": {
        "section": "economics",
        "required": ("initial_cost", "annual_cost", "annual_benefit", "discount_rate_pct", "years", "residual_value", "currency"),
        "formula": "net_present_benefit = PV(benefits + residual) − PV(initial + annual costs)",
        "contract": "energy-cost-benefit-result",
    },
    "cost-efficiency": {
        "section": "economics",
        "required": ("total_cost", "energy_saved_kwh", "co2e_avoided_kg", "currency"),
        "formula": "unit_cost = total_cost / explicit outcome denominator",
        "contract": "energy-cost-efficiency-result",
    },
    "levelized-energy-cost": {
        "section": "economics",
        "required": ("initial_cost", "annual_operating_cost", "annual_energy_kwh", "discount_rate_pct", "years", "residual_value", "currency"),
        "formula": "levelized_cost = PV(costs − residual_credit) / PV(energy)",
        "contract": "energy-levelized-cost-result",
    },
    "feedstock-energy": {
        "section": "bioenergy_and_carbon",
        "required": ("mass_tonnes", "energy_content_kwh_per_tonne", "conversion_efficiency_pct"),
        "formula": "useful_energy = mass × energy_content × efficiency / 100",
        "contract": "bioenergy-explicit-input-calculation-contract",
    },
    "anaerobic-digestion-energy": {
        "section": "bioenergy_and_carbon",
        "required": ("feedstock_mass_tonnes", "biogas_yield_m3_per_tonne", "methane_fraction_pct", "methane_energy_kwh_per_m3", "conversion_efficiency_pct"),
        "formula": "useful_energy = mass × biogas_yield × methane_fraction × methane_energy × efficiency",
        "contract": "bioenergy-explicit-input-calculation-contract",
    },
    "biochar-carbon": {
        "section": "bioenergy_and_carbon",
        "required": ("biochar_mass_kg", "carbon_fraction_pct", "stable_fraction_pct"),
        "formula": "stoichiometric_CO2e = biochar_mass × carbon_fraction × stable_fraction × 44/12",
        "contract": "bioenergy-explicit-input-calculation-contract",
    },
    "biomass-to-oil-energy": {
        "section": "bioenergy_and_carbon",
        "required": ("feedstock_mass_tonnes", "oil_yield_mass_pct", "oil_energy_content_kwh_per_tonne", "downstream_conversion_efficiency_pct"),
        "formula": "useful_energy = feedstock_mass × oil_yield × oil_energy_content × downstream_efficiency",
        "contract": "bioenergy-explicit-input-calculation-contract",
    },
}


def _decimal(value: Any, *, label: str, nonnegative: bool = False, positive: bool = False) -> Decimal:
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite decimal number") from exc
    if not number.is_finite():
        raise ValueError(f"{label} must be a finite decimal number")
    if positive and number <= 0:
        raise ValueError(f"{label} must be greater than zero")
    if nonnegative and number < 0:
        raise ValueError(f"{label} must be zero or greater")
    return number


def _pct(value: Any, *, label: str) -> Decimal:
    number = _decimal(value, label=label, nonnegative=True)
    if number > 100:
        raise ValueError(f"{label} must be between 0 and 100")
    return number


def _years(value: Any) -> int:
    try:
        n = int(str(value).strip())
    except Exception as exc:
        raise ValueError("years must be an integer") from exc
    if n < 1 or n > 200:
        raise ValueError("years must be between 1 and 200")
    return n


def _text(value: Decimal | None, places: int = 12) -> str | None:
    if value is None:
        return None
    quantum = Decimal(1).scaleb(-places)
    value = value.quantize(quantum)
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _discount_factor(rate_pct: Decimal, year: int) -> Decimal:
    return Decimal("1") / ((Decimal("1") + rate_pct / Decimal("100")) ** year)


def _request_id(section: str, index: int, request: dict[str, Any]) -> str:
    explicit = str(request.get("request_id") or request.get("id") or "").strip()
    if explicit:
        return explicit[:160]
    return "ewq-" + sha256(_canonical({"section": section, "index": index, "request": request}).encode()).hexdigest()[:16]


def _extract_requests(packet: dict[str, Any]) -> list[dict[str, Any]]:
    payload = packet.get("payload") or {}
    rows: list[dict[str, Any]] = []
    for section in SECTIONS:
        block = payload.get(section)
        if not isinstance(block, dict):
            continue
        requests = block.get("calculation_requests", [])
        if requests is None:
            continue
        if not isinstance(requests, list):
            rows.append({"section": section, "index": 0, "request": None, "shape_error": f"{section}.calculation_requests must be an array"})
            continue
        for idx, request in enumerate(requests):
            rows.append({"section": section, "index": idx, "request": request})
    return rows


def _validate_request(section: str, index: int, request: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(request, dict):
        return {"request_id": f"invalid-{section}-{index}", "section": section, "operation": "", "executable": False, "errors": ["calculation request must be an object"]}
    request_id = _request_id(section, index, request)
    operation = str(request.get("operation") or "").strip()
    spec = OPERATION_SPECS.get(operation)
    if spec is None:
        errors.append("unsupported operation")
    elif spec["section"] != section:
        errors.append(f"operation {operation} must be declared under {spec['section']}.calculation_requests")
    inputs = request.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be an object")
        inputs = {}
    if spec is not None:
        missing = [name for name in spec["required"] if name not in inputs or inputs[name] is None or (isinstance(inputs[name], str) and not inputs[name].strip())]
        if missing:
            errors.append("missing explicit input(s): " + ", ".join(missing))
    source_refs = request.get("source_refs", [])
    if not isinstance(source_refs, list):
        errors.append("source_refs must be an array")
    assumptions = request.get("assumptions", [])
    if not isinstance(assumptions, list):
        errors.append("assumptions must be an array")
    return {
        "request_id": request_id,
        "section": section,
        "operation": operation,
        "inputs": inputs,
        "source_refs": source_refs if isinstance(source_refs, list) else [],
        "assumptions": assumptions if isinstance(assumptions, list) else [],
        "executable": not errors,
        "errors": errors,
        "method_contract": spec["contract"] if spec else None,
        "formula": spec["formula"] if spec else None,
    }


def framework() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-energy-workbench-execution-framework/1.0",
        "workbench_version": RUNTIME_VERSION,
        "energy_systems_version": ENERGY_SYSTEMS_VERSION,
        "accepted_handoff_schema": HANDOFF_SCHEMA,
        "accepted_consumer_contract": CONSUMER_CONTRACT,
        "request_schema": REQUEST_SCHEMA,
        "plan_schema": PLAN_SCHEMA,
        "result_schema": EXECUTION_SCHEMA,
        "result_packet_schema": RESULT_PACKET_SCHEMA,
        "mode": "explicit-input-ephemeral-execution",
        "operations": [{"key": key, **value} for key, value in OPERATION_SPECS.items()],
        "capabilities": {
            "handoff_intake": True,
            "execution_planning": True,
            "explicit_input_execution": True,
            "unit_conversion_via_pint": _UREG is not None,
            "exact_energy_unit_fallback": True,
            "energy_balance_arithmetic": True,
            "energy_economic_arithmetic": True,
            "bioenergy_carbon_arithmetic": True,
            "deterministic_result_ids": True,
            "provenance_preservation": True,
            "automatic_execution_on_consume": False,
            "hidden_default_substitution": False,
            "automatic_persistence": False,
            "automatic_ranking": False,
            "automatic_recommendation": False,
            "external_market_data_fetch": False,
            "carbon_credit_claiming": False,
        },
        "boundary": BOUNDARY,
    }


def plan(body: dict[str, Any]) -> dict[str, Any]:
    packet, source_version = _unwrap(body)
    consumer_errors, _, _, consumer_warnings = _validate(packet)
    if consumer_errors:
        raise HTTPException(status_code=422, detail={"errors": consumer_errors, "target": "workbench"})
    rows = _extract_requests(packet)
    planned: list[dict[str, Any]] = []
    for row in rows:
        if row.get("shape_error"):
            planned.append({"request_id": f"invalid-{row['section']}", "section": row["section"], "operation": "", "executable": False, "errors": [row["shape_error"]]})
        else:
            planned.append(_validate_request(row["section"], row["index"], row["request"]))
    executable = [x for x in planned if x["executable"]]
    rejected = [x for x in planned if not x["executable"]]
    plan_key = {"handoff_id": packet.get("handoff_id"), "requests": planned}
    plan_id = "ewp-" + sha256(_canonical(plan_key).encode()).hexdigest()[:20]
    warnings = list(consumer_warnings)
    if not planned:
        warnings.append({"key": "no-calculation-requests", "message": "No calculation_requests were supplied in executable Workbench sections."})
    return {
        "ok": True,
        "schema": PLAN_SCHEMA,
        "version": ENERGY_SYSTEMS_VERSION,
        "workbench_version": RUNTIME_VERSION,
        "plan_id": plan_id,
        "handoff_id": packet.get("handoff_id"),
        "source_energy_systems_version": source_version or (packet.get("source") or {}).get("version"),
        "request_count": len(planned),
        "executable_count": len(executable),
        "rejected_count": len(rejected),
        "requests": planned,
        "warnings": warnings,
        "execution_ready": bool(planned) and not rejected,
        "execution_is_automatic": False,
        "boundary": BOUNDARY,
    }


def _unit_conversion(inputs: dict[str, Any]) -> dict[str, Any]:
    value = _decimal(inputs["value"], label="value")
    from_unit = str(inputs["from_unit"]).strip()
    to_unit = str(inputs["to_unit"]).strip()
    if _UREG is not None:
        try:
            result = (float(value) * _UREG(from_unit)).to(to_unit)
        except Exception as exc:
            raise ValueError(f"unit conversion failed: {exc}") from exc
        magnitude = Decimal(str(result.magnitude))
        return {"value": _text(magnitude), "unit": str(result.units), "from_unit": from_unit, "to_unit": to_unit, "engine": "pint"}
    source_key = from_unit.lower().replace(" ", "_")
    target_key = to_unit.lower().replace(" ", "_")
    if source_key not in _EXACT_ENERGY_TO_JOULE or target_key not in _EXACT_ENERGY_TO_JOULE:
        raise ValueError("unit conversion requires Pint for units outside the exact energy fallback registry")
    magnitude = value * _EXACT_ENERGY_TO_JOULE[source_key] / _EXACT_ENERGY_TO_JOULE[target_key]
    return {"value": _text(magnitude), "unit": to_unit, "from_unit": from_unit, "to_unit": to_unit, "engine": "exact-energy-fallback"}


def _conversion_chain(inputs: dict[str, Any]) -> dict[str, Any]:
    current = _decimal(inputs["input_kwh"], label="input_kwh", positive=True)
    raw = inputs["stage_efficiencies_pct"]
    if not isinstance(raw, list) or not raw:
        raise ValueError("stage_efficiencies_pct must be a non-empty array")
    if len(raw) > 20:
        raise ValueError("at most 20 conversion stages are supported")
    labels = inputs.get("stage_labels", [])
    if labels is not None and not isinstance(labels, list):
        raise ValueError("stage_labels must be an array when supplied")
    labels = labels or []
    start = current
    stages = []
    with localcontext() as ctx:
        ctx.prec = 40
        for i, item in enumerate(raw):
            eff = _pct(item, label=f"stage_efficiencies_pct[{i}]")
            output = current * eff / Decimal("100")
            loss = current - output
            stages.append({"stage": i + 1, "label": str(labels[i]) if i < len(labels) and labels[i] else f"Stage {i+1}", "input_kwh": _text(current), "efficiency_pct": _text(eff), "output_kwh": _text(output), "loss_kwh": _text(loss)})
            current = output
        overall = current / start * Decimal("100")
    return {"stage_outputs": stages, "final_output_kwh": _text(current), "total_loss_kwh": _text(start-current), "overall_efficiency_pct": _text(overall)}


def _supply_demand(inputs: dict[str, Any]) -> dict[str, Any]:
    names = ("domestic_supply_kwh", "imports_kwh", "storage_discharge_kwh", "final_demand_kwh", "exports_kwh", "storage_charge_kwh", "losses_kwh", "tolerance_kwh")
    v = {n: _decimal(inputs[n], label=n, nonnegative=True) for n in names}
    available = v["domestic_supply_kwh"] + v["imports_kwh"] + v["storage_discharge_kwh"]
    outflows = v["final_demand_kwh"] + v["exports_kwh"] + v["storage_charge_kwh"] + v["losses_kwh"]
    residual = available - outflows
    residual_pct = residual / available * Decimal("100") if available else None
    return {"available_supply_kwh": _text(available), "accounted_outflows_kwh": _text(outflows), "residual_kwh": _text(residual), "residual_pct_of_supply": _text(residual_pct), "balanced": abs(residual) <= v["tolerance_kwh"]}


def _generation(inputs: dict[str, Any]) -> dict[str, Any]:
    capacity = _decimal(inputs["capacity_kw"], label="capacity_kw", nonnegative=True)
    cf = _pct(inputs["capacity_factor_pct"], label="capacity_factor_pct")
    hours = _decimal(inputs["hours"], label="hours", positive=True)
    generation = capacity * hours * cf / Decimal("100")
    average = capacity * cf / Decimal("100")
    return {"generation_kwh": _text(generation), "average_output_kw": _text(average)}


def _cost_comparison(inputs: dict[str, Any]) -> dict[str, Any]:
    be=_decimal(inputs["baseline_energy_kwh"],label="baseline_energy_kwh",nonnegative=True); bp=_decimal(inputs["baseline_price_per_kwh"],label="baseline_price_per_kwh",nonnegative=True); ce=_decimal(inputs["candidate_energy_kwh"],label="candidate_energy_kwh",nonnegative=True); cp=_decimal(inputs["candidate_price_per_kwh"],label="candidate_price_per_kwh",nonnegative=True); bf=_decimal(inputs["baseline_fixed_cost"],label="baseline_fixed_cost",nonnegative=True); cf=_decimal(inputs["candidate_fixed_cost"],label="candidate_fixed_cost",nonnegative=True)
    baseline=be*bp+bf; candidate=ce*cp+cf; savings=baseline-candidate; pct=savings/baseline*Decimal("100") if baseline else None
    return {"baseline_cost":_text(baseline),"candidate_cost":_text(candidate),"absolute_savings":_text(savings),"savings_pct_of_baseline":_text(pct),"currency":str(inputs["currency"])}


def _simple_payback(inputs: dict[str, Any]) -> dict[str, Any]:
    initial=_decimal(inputs["initial_cost"],label="initial_cost",positive=True); savings=_decimal(inputs["annual_net_savings"],label="annual_net_savings")
    payback=None if savings<=0 else initial/savings
    return {"payback_years":_text(payback),"payback_status":"finite-payback" if payback is not None else "no-finite-payback-from-nonpositive-savings","currency":str(inputs["currency"])}


def _npv(inputs: dict[str, Any]) -> dict[str, Any]:
    initial=_decimal(inputs["initial_cost"],label="initial_cost",nonnegative=True); cash=_decimal(inputs["annual_net_cash_flow"],label="annual_net_cash_flow"); rate=_pct(inputs["discount_rate_pct"],label="discount_rate_pct"); n=_years(inputs["years"]); residual=_decimal(inputs["residual_value"],label="residual_value",nonnegative=True)
    with localcontext() as ctx:
        ctx.prec=40; pv_cash=sum((cash*_discount_factor(rate,t) for t in range(1,n+1)),Decimal("0")); pv_residual=residual*_discount_factor(rate,n); value=-initial+pv_cash+pv_residual
    return {"present_value_cash_flows":_text(pv_cash),"present_value_residual":_text(pv_residual),"npv":_text(value),"currency":str(inputs["currency"])}


def _cost_benefit(inputs: dict[str, Any]) -> dict[str, Any]:
    initial=_decimal(inputs["initial_cost"],label="initial_cost",nonnegative=True); annual_cost=_decimal(inputs["annual_cost"],label="annual_cost",nonnegative=True); annual_benefit=_decimal(inputs["annual_benefit"],label="annual_benefit",nonnegative=True); rate=_pct(inputs["discount_rate_pct"],label="discount_rate_pct"); n=_years(inputs["years"]); residual=_decimal(inputs["residual_value"],label="residual_value",nonnegative=True)
    with localcontext() as ctx:
        ctx.prec=40; pv_costs=initial+sum((annual_cost*_discount_factor(rate,t) for t in range(1,n+1)),Decimal("0")); pv_benefits=sum((annual_benefit*_discount_factor(rate,t) for t in range(1,n+1)),Decimal("0"))+residual*_discount_factor(rate,n); net=pv_benefits-pv_costs; ratio=pv_benefits/pv_costs if pv_costs else None
    return {"present_value_costs":_text(pv_costs),"present_value_benefits":_text(pv_benefits),"net_present_benefit":_text(net),"benefit_cost_ratio":_text(ratio),"currency":str(inputs["currency"])}


def _cost_efficiency(inputs: dict[str, Any]) -> dict[str, Any]:
    cost=_decimal(inputs["total_cost"],label="total_cost",nonnegative=True); energy=_decimal(inputs["energy_saved_kwh"],label="energy_saved_kwh",nonnegative=True); co2=_decimal(inputs["co2e_avoided_kg"],label="co2e_avoided_kg",nonnegative=True)
    if energy==0 and co2==0:
        raise ValueError("at least one explicit outcome denominator must be greater than zero")
    per_kwh=cost/energy if energy else None; per_mwh=cost/(energy/Decimal("1000")) if energy else None; per_tonne=cost/(co2/Decimal("1000")) if co2 else None
    return {"cost_per_kwh_saved":_text(per_kwh),"cost_per_mwh_saved":_text(per_mwh),"cost_per_tonne_co2e_avoided":_text(per_tonne),"currency":str(inputs["currency"]),"co2e_value_role":"caller-supplied outcome denominator; Workbench does not calculate avoided emissions"}


def _levelized(inputs: dict[str, Any]) -> dict[str, Any]:
    initial=_decimal(inputs["initial_cost"],label="initial_cost",nonnegative=True); op=_decimal(inputs["annual_operating_cost"],label="annual_operating_cost",nonnegative=True); energy=_decimal(inputs["annual_energy_kwh"],label="annual_energy_kwh",positive=True); rate=_pct(inputs["discount_rate_pct"],label="discount_rate_pct"); n=_years(inputs["years"]); residual=_decimal(inputs["residual_value"],label="residual_value",nonnegative=True)
    with localcontext() as ctx:
        ctx.prec=40; pv_op=sum((op*_discount_factor(rate,t) for t in range(1,n+1)),Decimal("0")); pv_energy=sum((energy*_discount_factor(rate,t) for t in range(1,n+1)),Decimal("0")); pv_residual=residual*_discount_factor(rate,n); pv_costs=initial+pv_op-pv_residual; levelized=pv_costs/pv_energy
    return {"present_value_costs":_text(pv_costs),"present_value_energy_kwh":_text(pv_energy),"present_value_residual_credit":_text(pv_residual),"levelized_cost_per_kwh":_text(levelized),"currency":str(inputs["currency"])}


def _feedstock(inputs: dict[str, Any]) -> dict[str, Any]:
    mass=_decimal(inputs["mass_tonnes"],label="mass_tonnes",nonnegative=True); content=_decimal(inputs["energy_content_kwh_per_tonne"],label="energy_content_kwh_per_tonne",nonnegative=True); eff=_pct(inputs["conversion_efficiency_pct"],label="conversion_efficiency_pct"); gross=mass*content; useful=gross*eff/Decimal("100")
    return {"gross_energy_kwh":_text(gross),"useful_energy_kwh":_text(useful),"conversion_loss_kwh":_text(gross-useful)}


def _ad(inputs: dict[str, Any]) -> dict[str, Any]:
    mass=_decimal(inputs["feedstock_mass_tonnes"],label="feedstock_mass_tonnes",nonnegative=True); yield_factor=_decimal(inputs["biogas_yield_m3_per_tonne"],label="biogas_yield_m3_per_tonne",nonnegative=True); methane_fraction=_pct(inputs["methane_fraction_pct"],label="methane_fraction_pct"); methane_energy=_decimal(inputs["methane_energy_kwh_per_m3"],label="methane_energy_kwh_per_m3",nonnegative=True); eff=_pct(inputs["conversion_efficiency_pct"],label="conversion_efficiency_pct"); biogas=mass*yield_factor; methane=biogas*methane_fraction/Decimal("100"); gross=methane*methane_energy; useful=gross*eff/Decimal("100")
    return {"biogas_volume_m3":_text(biogas),"methane_volume_m3":_text(methane),"gross_methane_energy_kwh":_text(gross),"useful_energy_kwh":_text(useful)}


def _biochar(inputs: dict[str, Any]) -> dict[str, Any]:
    mass=_decimal(inputs["biochar_mass_kg"],label="biochar_mass_kg",nonnegative=True); carbon=_pct(inputs["carbon_fraction_pct"],label="carbon_fraction_pct"); stable=_pct(inputs["stable_fraction_pct"],label="stable_fraction_pct"); carbon_mass=mass*carbon/Decimal("100"); stable_carbon=carbon_mass*stable/Decimal("100"); co2e=stable_carbon*Decimal("44")/Decimal("12")
    return {"carbon_mass_kg_c":_text(carbon_mass),"stable_carbon_mass_kg_c":_text(stable_carbon),"stoichiometric_co2_equivalent_kg":_text(co2e),"claim_boundary":"stoichiometric equivalence only; not a removal, permanence, additionality, lifecycle, verification, issuance, or carbon-credit result"}


def _biomass_oil(inputs: dict[str, Any]) -> dict[str, Any]:
    mass=_decimal(inputs["feedstock_mass_tonnes"],label="feedstock_mass_tonnes",nonnegative=True); yield_pct=_pct(inputs["oil_yield_mass_pct"],label="oil_yield_mass_pct"); content=_decimal(inputs["oil_energy_content_kwh_per_tonne"],label="oil_energy_content_kwh_per_tonne",nonnegative=True); eff=_pct(inputs["downstream_conversion_efficiency_pct"],label="downstream_conversion_efficiency_pct"); oil_mass=mass*yield_pct/Decimal("100"); gross=oil_mass*content; useful=gross*eff/Decimal("100")
    return {"oil_product_mass_tonnes":_text(oil_mass),"gross_product_energy_kwh":_text(gross),"useful_energy_kwh":_text(useful)}


EXECUTORS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "unit-conversion": _unit_conversion,
    "conversion-chain": _conversion_chain,
    "supply-demand-balance": _supply_demand,
    "capacity-factor-generation": _generation,
    "energy-cost-comparison": _cost_comparison,
    "simple-payback": _simple_payback,
    "net-present-value": _npv,
    "cost-benefit": _cost_benefit,
    "cost-efficiency": _cost_efficiency,
    "levelized-energy-cost": _levelized,
    "feedstock-energy": _feedstock,
    "anaerobic-digestion-energy": _ad,
    "biochar-carbon": _biochar,
    "biomass-to-oil-energy": _biomass_oil,
}


def execute(body: dict[str, Any]) -> dict[str, Any]:
    packet, source_version = _unwrap(body)
    execution_plan = plan(body)
    if not execution_plan["execution_ready"]:
        raise HTTPException(status_code=422, detail={"message": "Energy execution plan is not ready", "plan": execution_plan})
    results: list[dict[str, Any]] = []
    for item in execution_plan["requests"]:
        operation = item["operation"]
        try:
            output = EXECUTORS[operation](item["inputs"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"request_id": item["request_id"], "operation": operation, "error": str(exc)}) from exc
        identity = {"handoff_id": packet.get("handoff_id"), "request_id": item["request_id"], "operation": operation, "inputs": item["inputs"], "output": output}
        result_id = "ewr-" + sha256(_canonical(identity).encode()).hexdigest()[:20]
        results.append({
            "ok": True,
            "schema": EXECUTION_SCHEMA,
            "result_id": result_id,
            "request_id": item["request_id"],
            "operation": operation,
            "method_contract": item["method_contract"],
            "formula": item["formula"],
            "inputs": item["inputs"],
            "output": output,
            "assumptions": item["assumptions"],
            "source_refs": item["source_refs"],
            "provenance": {
                "source_handoff_id": packet.get("handoff_id"),
                "source_energy_systems_version": source_version or (packet.get("source") or {}).get("version"),
                "workbench_version": RUNTIME_VERSION,
                "execution_mode": "explicit-input-ephemeral",
                "hidden_defaults_used": False,
            },
            "boundary": BOUNDARY,
        })
    packet_basis = {"handoff_id": packet.get("handoff_id"), "plan_id": execution_plan["plan_id"], "result_ids": [r["result_id"] for r in results]}
    result_packet_id = "ewb-" + sha256(_canonical(packet_basis).encode()).hexdigest()[:20]
    return {
        "ok": True,
        "schema": RESULT_PACKET_SCHEMA,
        "version": ENERGY_SYSTEMS_VERSION,
        "workbench_version": RUNTIME_VERSION,
        "result_packet_id": result_packet_id,
        "plan_id": execution_plan["plan_id"],
        "handoff_id": packet.get("handoff_id"),
        "study_id": ((packet.get("payload") or {}).get("identity") or {}).get("study_id"),
        "result_count": len(results),
        "results": results,
        "provenance": list((packet.get("payload") or {}).get("provenance") or []),
        "review": (packet.get("payload") or {}).get("review") or {},
        "persistence": {"performed": False, "mode": "ephemeral"},
        "ranking": {"performed": False},
        "recommendation": {"performed": False},
        "boundary": BOUNDARY,
    }


def validate_result(body: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if body.get("schema") != RESULT_PACKET_SCHEMA:
        errors.append(f"schema must be {RESULT_PACKET_SCHEMA}")
    if str(body.get("workbench_version")) != RUNTIME_VERSION:
        errors.append(f"workbench_version must be {RUNTIME_VERSION}")
    results = body.get("results")
    if not isinstance(results, list):
        errors.append("results must be an array")
        results = []
    for idx, result in enumerate(results):
        if not isinstance(result, dict):
            errors.append(f"results[{idx}] must be an object")
            continue
        if result.get("schema") != EXECUTION_SCHEMA:
            errors.append(f"results[{idx}].schema must be {EXECUTION_SCHEMA}")
        if result.get("operation") not in OPERATION_SPECS:
            errors.append(f"results[{idx}].operation is unsupported")
        if not str(result.get("result_id") or "").startswith("ewr-"):
            errors.append(f"results[{idx}].result_id is invalid")
    return {
        "ok": not errors,
        "schema": "sc-energy-workbench-result-validation/1.0",
        "valid": not errors,
        "errors": errors,
        "result_count": len(results),
        "boundary": "Validation checks Workbench packet structure only; it is not scientific, engineering, economic, or carbon-accounting assurance.",
    }


@router.get("/execution-framework")
def energy_execution_framework() -> dict[str, Any]:
    return framework()


@router.post("/plan")
def energy_execution_plan(body: dict[str, Any]) -> dict[str, Any]:
    return plan(body)


@router.post("/execute")
def energy_execute(body: dict[str, Any]) -> dict[str, Any]:
    return execute(body)


@router.post("/validate-result")
def energy_validate_result(body: dict[str, Any]) -> dict[str, Any]:
    return validate_result(body)
