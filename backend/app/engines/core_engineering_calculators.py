from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np
import matplotlib.pyplot as plt

from .common import result, svg_from_figure

G = 9.80665


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        out = float(value)
        if math.isfinite(out):
            return out
    except Exception:
        pass
    return default


def _positive(value: Any, default: float = 1.0, minimum: float = 1e-12) -> float:
    out = _num(value, default)
    return out if out > minimum else default


def _eff(value: Any, default: float = 0.75) -> float:
    out = _num(value, default)
    if out > 1.0:
        out = out / 100.0
    return min(max(out, 1e-6), 1.0)


def _bar(labels: list[str], values: list[float], title: str, ylabel: str = "Value") -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(7.8, 4.5))
    ax.bar(range(len(values)), values)
    ax.set_xticks(range(len(labels)), labels, rotation=18, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.24)
    fig.tight_layout()
    svg = svg_from_figure(fig)
    plt.close(fig)
    return {"title": title, "type": "engineering_bar", "svg": svg}


def _line(x: np.ndarray, y: np.ndarray, title: str, xlabel: str, ylabel: str) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(x, y, linewidth=2.25)
    ax.axhline(0, linewidth=0.85, color="black", alpha=0.25)
    ax.grid(alpha=0.24)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    svg = svg_from_figure(fig)
    plt.close(fig)
    return {"title": title, "type": "engineering_sensitivity", "svg": svg}


def _fmt(value: float, unit: str = "") -> str:
    if abs(value) >= 1e6 or (0 < abs(value) < 1e-3):
        text = f"{value:.4e}"
    elif abs(value) >= 1000:
        text = f"{value:,.3f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:.6g}"
    return (text + (" " + unit if unit else "")).strip()


def _note(title: str, formula: str, inputs: dict[str, Any], results: dict[str, Any], assumptions: list[str], checks: list[str]) -> dict[str, Any]:
    return {
        "calculation_title": title,
        "formula": formula,
        "inputs": inputs,
        "results": results,
        "assumptions": assumptions,
        "validation_checks": checks,
        "calculation_note_sections": [
            "Purpose and selected calculator",
            "Inputs and units",
            "Formula",
            "Computed result",
            "Sensitivity or graph review",
            "Assumptions",
            "Validation checks and professional review",
        ],
    }


def _common_warnings(extra: list[str] | None = None) -> list[str]:
    warnings = [
        "Use consistent units. These calculators assume the units listed beside each input.",
        "This is an educational first-pass engineering calculator, not a stamped, code-compliant, safety-critical, or licensed professional engineering calculation.",
    ]
    if extra:
        warnings.extend(extra)
    return list(dict.fromkeys(warnings))


def calc_force_mass_acceleration(inputs: dict[str, Any]) -> dict[str, Any]:
    m = _positive(inputs.get("mass_kg"), 12.0)
    a = _num(inputs.get("acceleration_m_s2"), 3.5)
    F = m * a
    xs = np.linspace(max(0, a * 0.1), max(abs(a) * 2.0, 10.0), 120)
    graphs = [_line(xs, m * xs, "Force sensitivity to acceleration", "Acceleration (m/s²)", "Force (N)")]
    values = {
        "calculator_id": "force-mass-acceleration",
        "formula": "F = m a",
        "inputs": {"mass_kg": m, "acceleration_m_s2": a},
        "results": {"force_N": F, "force_display": _fmt(F, "N")},
        "engineering_note": _note(
            "Force from mass and acceleration",
            "F = m a",
            {"m": _fmt(m, "kg"), "a": _fmt(a, "m/s²")},
            {"F": _fmt(F, "N")},
            ["Mass is treated as constant.", "Acceleration is applied along the direction of interest."],
            ["Confirm whether acceleration is peak, RMS, steady, transient, or shock loading.", "Check load path and support reactions before design use."],
        ),
    }
    return result("Force, Mass, and Acceleration", "Computed force from Newton's second law and generated an acceleration sensitivity graph.", values, _common_warnings(), graphs, ["Applied F = m a.", "Varied acceleration to show force sensitivity."], "python/numpy/matplotlib")


def calc_normal_stress(inputs: dict[str, Any]) -> dict[str, Any]:
    F = _num(inputs.get("force_N"), 1000.0)
    A = _positive(inputs.get("area_m2"), 0.02)
    sigma = F / A
    areas = np.linspace(max(A * 0.25, 1e-6), max(A * 2.5, A + 1e-3), 140)
    graphs = [_line(areas, F / areas / 1e6, "Stress sensitivity to area", "Area (m²)", "Stress (MPa)")]
    values = {
        "calculator_id": "normal-stress",
        "formula": "σ = F / A",
        "inputs": {"force_N": F, "area_m2": A},
        "results": {"stress_Pa": sigma, "stress_MPa": sigma / 1e6, "stress_display": _fmt(sigma / 1e6, "MPa")},
        "engineering_note": _note(
            "Normal stress from axial force and area",
            "σ = F / A",
            {"F": _fmt(F, "N"), "A": _fmt(A, "m²")},
            {"σ": _fmt(sigma, "Pa"), "σ_MPa": _fmt(sigma / 1e6, "MPa")},
            ["Uniform axial stress distribution is assumed.", "Area is the net load-bearing area."],
            ["Check stress concentration, buckling, fatigue, shear, and combined loading where relevant.", "Compare against allowable stress or material yield/ultimate values with an appropriate factor of safety."],
        ),
    }
    return result("Normal Stress", "Computed normal stress from force and area with an area sensitivity graph.", values, _common_warnings(), graphs, ["Applied σ = F/A.", "Converted Pa to MPa for engineering readability."], "python/numpy/matplotlib")


def calc_axial_strain(inputs: dict[str, Any]) -> dict[str, Any]:
    delta = _num(inputs.get("elongation_m"), 0.001)
    L = _positive(inputs.get("length_m"), 2.0)
    strain = delta / L
    lengths = np.linspace(max(L * 0.25, 1e-6), max(L * 2.5, L + 1e-3), 120)
    graphs = [_line(lengths, delta / lengths, "Strain sensitivity to original length", "Original length (m)", "Strain")]
    values = {
        "calculator_id": "axial-strain",
        "formula": "ε = ΔL / L",
        "inputs": {"elongation_m": delta, "length_m": L},
        "results": {"strain": strain, "microstrain": strain * 1e6, "strain_display": _fmt(strain)},
        "engineering_note": _note(
            "Axial strain from elongation and original length",
            "ε = ΔL / L",
            {"ΔL": _fmt(delta, "m"), "L": _fmt(L, "m")},
            {"ε": _fmt(strain), "microstrain": _fmt(strain * 1e6, "με")},
            ["Small deformation and one-dimensional axial extension are assumed."],
            ["Confirm measurement resolution and whether strain is engineering strain or true strain.", "For materials work, pair strain with stress and material model assumptions."],
        ),
    }
    return result("Axial Strain", "Computed axial strain and microstrain from elongation and original length.", values, _common_warnings(), graphs, ["Applied ε = ΔL/L.", "Converted strain to microstrain."], "python/numpy/matplotlib")


def calc_factor_of_safety(inputs: dict[str, Any]) -> dict[str, Any]:
    allowable = _positive(inputs.get("allowable_value"), 250.0)
    applied = _positive(inputs.get("applied_value"), 100.0)
    fos = allowable / applied
    applied_range = np.linspace(max(applied * 0.25, 1e-6), max(applied * 2.5, applied + 1), 120)
    graphs = [_line(applied_range, allowable / applied_range, "Factor of safety sensitivity", "Applied demand", "Factor of safety")]
    flags = []
    if fos < 1.0:
        flags.append("Computed factor of safety is below 1.0; applied demand exceeds allowable capacity.")
    elif fos < 1.5:
        flags.append("Computed factor of safety is low for many design contexts; compare against governing standard.")
    values = {
        "calculator_id": "factor-of-safety",
        "formula": "FoS = allowable / applied",
        "inputs": {"allowable_value": allowable, "applied_value": applied},
        "results": {"factor_of_safety": fos, "status": "fail" if fos < 1 else "review" if fos < 1.5 else "initially acceptable"},
        "engineering_note": _note(
            "Factor of safety",
            "FoS = allowable / applied",
            {"allowable": _fmt(allowable), "applied": _fmt(applied)},
            {"FoS": _fmt(fos)},
            ["Allowable and applied values must use the same units and same demand/capacity basis."],
            ["Confirm whether values are nominal, factored, characteristic, allowable, ultimate, or service-level.", "Check the governing code-required safety factor for the specific material/system."],
        ),
    }
    return result("Factor of Safety", "Computed a demand-capacity factor of safety and flagged low margins.", values, _common_warnings(flags), graphs, ["Divided allowable capacity by applied demand.", "Generated a demand sensitivity graph."], "python/numpy/matplotlib")


def calc_beam_deflection(inputs: dict[str, Any]) -> dict[str, Any]:
    support = str(inputs.get("beam_case") or "cantilever_point").strip() or "cantilever_point"
    P = _num(inputs.get("load_N"), 500.0)
    L = _positive(inputs.get("length_m"), 2.0)
    E = _positive(inputs.get("elastic_modulus_GPa"), 200.0) * 1e9
    I = _positive(inputs.get("second_moment_m4"), 8.0e-6)
    if support == "simply_supported_center":
        denom = 48 * E * I
        formula = "δ_max = P L³ / (48 E I)"
        case_title = "Simply supported beam, center point load"
    else:
        support = "cantilever_point"
        denom = 3 * E * I
        formula = "δ_tip = P L³ / (3 E I)"
        case_title = "Cantilever beam, end point load"
    delta = P * L**3 / denom
    loads = np.linspace(0, max(P * 2.0, 100.0), 130)
    graphs = [_line(loads, loads * L**3 / denom * 1000.0, "Beam deflection sensitivity to load", "Load (N)", "Deflection (mm)")]
    values = {
        "calculator_id": "beam-deflection",
        "formula": formula,
        "inputs": {"beam_case": support, "load_N": P, "length_m": L, "elastic_modulus_GPa": E / 1e9, "second_moment_m4": I},
        "results": {"deflection_m": delta, "deflection_mm": delta * 1000, "deflection_display": _fmt(delta * 1000, "mm")},
        "engineering_note": _note(
            case_title,
            formula,
            {"P": _fmt(P, "N"), "L": _fmt(L, "m"), "E": _fmt(E / 1e9, "GPa"), "I": _fmt(I, "m⁴")},
            {"δ": _fmt(delta, "m"), "δ_mm": _fmt(delta * 1000, "mm")},
            ["Euler-Bernoulli beam behavior is assumed.", "Linear elastic, small-deflection behavior is assumed.", "Load case is simplified and support conditions must match the selected case."],
            ["Check shear deflection, local buckling, lateral torsional buckling, stress, vibration, fatigue, and code serviceability limits where relevant.", "Confirm that I corresponds to the correct bending axis."],
        ),
    }
    return result("Beam Deflection", "Computed simplified beam deflection and generated a load sensitivity graph.", values, _common_warnings(), graphs, ["Selected the beam formula from the requested support/load case.", "Computed deflection using SI units."], "python/numpy/matplotlib")


def calc_ohms_law_power(inputs: dict[str, Any]) -> dict[str, Any]:
    V = _num(inputs.get("voltage_V"), 12.0)
    R = _positive(inputs.get("resistance_ohm"), 6.0)
    I = V / R
    P = V * I
    volts = np.linspace(0, max(abs(V) * 2, 24.0), 130)
    graphs = [_line(volts, volts / R, "Current sensitivity to voltage", "Voltage (V)", "Current (A)")]
    values = {
        "calculator_id": "ohms-law-power",
        "formula": "I = V / R; P = V I = V²/R",
        "inputs": {"voltage_V": V, "resistance_ohm": R},
        "results": {"current_A": I, "power_W": P, "current_display": _fmt(I, "A"), "power_display": _fmt(P, "W")},
        "engineering_note": _note(
            "Ohm's law and resistive power",
            "I = V/R; P = VI",
            {"V": _fmt(V, "V"), "R": _fmt(R, "Ω")},
            {"I": _fmt(I, "A"), "P": _fmt(P, "W")},
            ["Purely resistive DC or equivalent steady-state behavior is assumed."],
            ["Check component power rating, voltage rating, thermal dissipation, tolerances, and derating.", "For AC/reactive circuits, use impedance and RMS conventions rather than this simplified DC model."],
        ),
    }
    return result("Ohm's Law and Power", "Computed current and power for a simplified resistive circuit.", values, _common_warnings(), graphs, ["Applied I=V/R.", "Computed P=VI."], "python/numpy/matplotlib")


def calc_rc_response(inputs: dict[str, Any]) -> dict[str, Any]:
    R = _positive(inputs.get("resistance_ohm"), 10000.0)
    C = _positive(inputs.get("capacitance_F"), 1e-6)
    V0 = _num(inputs.get("initial_voltage_V"), 0.0)
    Vinf = _num(inputs.get("final_voltage_V"), 5.0)
    t_eval = max(_num(inputs.get("time_s"), R * C), 0.0)
    tau = R * C
    Vt = Vinf + (V0 - Vinf) * math.exp(-t_eval / tau)
    ts = np.linspace(0, max(5 * tau, t_eval * 1.2, tau), 160)
    vs = Vinf + (V0 - Vinf) * np.exp(-ts / tau)
    graphs = [_line(ts, vs, "RC voltage response", "Time (s)", "Voltage (V)")]
    values = {
        "calculator_id": "rc-time-constant",
        "formula": "τ = R C; V(t)=V∞+(V0−V∞)e^(−t/τ)",
        "inputs": {"resistance_ohm": R, "capacitance_F": C, "initial_voltage_V": V0, "final_voltage_V": Vinf, "time_s": t_eval},
        "results": {"tau_s": tau, "voltage_at_time_V": Vt, "tau_display": _fmt(tau, "s"), "voltage_display": _fmt(Vt, "V")},
        "engineering_note": _note(
            "First-order RC response",
            "τ = RC; V(t)=V∞+(V0−V∞)e^(−t/τ)",
            {"R": _fmt(R, "Ω"), "C": _fmt(C, "F"), "V0": _fmt(V0, "V"), "V∞": _fmt(Vinf, "V"), "t": _fmt(t_eval, "s")},
            {"τ": _fmt(tau, "s"), "V(t)": _fmt(Vt, "V")},
            ["Ideal resistor and capacitor are assumed.", "The model is first-order and lumped."],
            ["Check ESR, leakage, tolerance, source impedance, load effects, temperature, and voltage ratings for real circuits."],
        ),
    }
    return result("RC Time Constant and Response", "Computed RC time constant and first-order voltage response.", values, _common_warnings(), graphs, ["Computed τ=RC.", "Evaluated first-order exponential response."], "python/numpy/matplotlib")


def calc_conduction_heat_transfer(inputs: dict[str, Any]) -> dict[str, Any]:
    k = _positive(inputs.get("thermal_conductivity_W_mK"), 0.8)
    A = _positive(inputs.get("area_m2"), 10.0)
    dT = _num(inputs.get("delta_T_K"), 20.0)
    L = _positive(inputs.get("thickness_m"), 0.1)
    q = k * A * dT / L
    dTs = np.linspace(0, max(abs(dT) * 2, 50.0), 130)
    graphs = [_line(dTs, k * A * dTs / L, "Conduction heat-transfer sensitivity", "Temperature difference (K)", "Heat rate (W)")]
    values = {
        "calculator_id": "conduction-heat-transfer",
        "formula": "q̇ = k A ΔT / L",
        "inputs": {"thermal_conductivity_W_mK": k, "area_m2": A, "delta_T_K": dT, "thickness_m": L},
        "results": {"heat_rate_W": q, "heat_rate_display": _fmt(q, "W")},
        "engineering_note": _note(
            "One-dimensional conductive heat transfer",
            "q̇ = k A ΔT / L",
            {"k": _fmt(k, "W/(m·K)"), "A": _fmt(A, "m²"), "ΔT": _fmt(dT, "K"), "L": _fmt(L, "m")},
            {"q̇": _fmt(q, "W")},
            ["Steady, one-dimensional conduction is assumed.", "Thermal conductivity is assumed constant across the temperature range."],
            ["Check convection, radiation, thermal bridges, moisture, contact resistance, and multi-layer assemblies where relevant."],
        ),
    }
    return result("Conduction Heat Transfer", "Computed steady one-dimensional conductive heat-transfer rate.", values, _common_warnings(), graphs, ["Applied q̇=kAΔT/L.", "Generated a ΔT sensitivity graph."], "python/numpy/matplotlib")


def calc_pump_power(inputs: dict[str, Any]) -> dict[str, Any]:
    rho = _positive(inputs.get("fluid_density_kg_m3"), 1000.0)
    Q = _positive(inputs.get("flow_rate_m3_s"), 0.02)
    H = _positive(inputs.get("head_m"), 10.0)
    eta = _eff(inputs.get("efficiency"), 0.70)
    hydraulic = rho * G * Q * H
    shaft = hydraulic / eta
    flows = np.linspace(0, max(Q * 2.0, 0.05), 130)
    graphs = [_line(flows, rho * G * flows * H / eta / 1000.0, "Pump power sensitivity to flow", "Flow rate (m³/s)", "Required power (kW)")]
    values = {
        "calculator_id": "pump-power",
        "formula": "P = ρ g Q H / η",
        "inputs": {"fluid_density_kg_m3": rho, "flow_rate_m3_s": Q, "head_m": H, "efficiency": eta},
        "results": {"hydraulic_power_W": hydraulic, "shaft_power_W": shaft, "shaft_power_kW": shaft / 1000, "power_display": _fmt(shaft / 1000, "kW")},
        "engineering_note": _note(
            "Pump hydraulic and shaft power",
            "P = ρ g Q H / η",
            {"ρ": _fmt(rho, "kg/m³"), "g": _fmt(G, "m/s²"), "Q": _fmt(Q, "m³/s"), "H": _fmt(H, "m"), "η": _fmt(eta)},
            {"P_hydraulic": _fmt(hydraulic, "W"), "P_required": _fmt(shaft / 1000, "kW")},
            ["Single operating point and constant efficiency are assumed."],
            ["Check pump curve, NPSH, cavitation, pipe losses, motor efficiency, control strategy, and operating range."],
        ),
    }
    return result("Pump Power", "Computed hydraulic and required shaft power for a simplified pump case.", values, _common_warnings(), graphs, ["Applied P=ρgQH/η.", "Converted W to kW for readability."], "python/numpy/matplotlib")


def calc_energy_emissions(inputs: dict[str, Any]) -> dict[str, Any]:
    energy = _positive(inputs.get("energy_kwh"), 10000.0)
    factor = _positive(inputs.get("emission_factor_kg_per_kwh"), 0.40)
    emissions = energy * factor
    energies = np.linspace(0, max(energy * 2, 1000), 120)
    graphs = [_line(energies, energies * factor / 1000.0, "Emissions sensitivity to energy use", "Energy (kWh)", "Emissions (metric tons CO₂e)")]
    values = {
        "calculator_id": "energy-emissions",
        "formula": "Emissions = energy × emission factor",
        "inputs": {"energy_kwh": energy, "emission_factor_kg_per_kwh": factor},
        "results": {"emissions_kg_co2e": emissions, "emissions_metric_tons_co2e": emissions / 1000, "emissions_display": _fmt(emissions / 1000, "metric tons CO₂e")},
        "engineering_note": _note(
            "Energy-use emissions estimate",
            "E_CO2e = kWh × kgCO2e/kWh",
            {"energy": _fmt(energy, "kWh"), "factor": _fmt(factor, "kg CO₂e/kWh")},
            {"emissions": _fmt(emissions / 1000, "metric tons CO₂e")},
            ["Emission factor is assumed representative for the energy source and time period."],
            ["Confirm market/location-based accounting method, grid region, time period, scope boundary, and factor source.", "Do not treat this as certified greenhouse-gas reporting without appropriate methodology review."],
        ),
    }
    return result("Energy Emissions", "Estimated emissions from energy use and an emission factor.", values, _common_warnings(), graphs, ["Multiplied energy by emission factor.", "Converted kg CO₂e to metric tons CO₂e."], "python/numpy/matplotlib")


def calc_rpn(inputs: dict[str, Any]) -> dict[str, Any]:
    severity = max(1, min(10, int(round(_num(inputs.get("severity"), 7)))))
    occurrence = max(1, min(10, int(round(_num(inputs.get("occurrence"), 4)))))
    detection = max(1, min(10, int(round(_num(inputs.get("detection"), 5)))))
    rpn = severity * occurrence * detection
    band = "high review priority" if rpn >= 200 else "medium review priority" if rpn >= 80 else "lower review priority"
    graphs = [_bar(["Severity", "Occurrence", "Detection"], [severity, occurrence, detection], "FMEA-style input scores", "Score (1–10)")]
    values = {
        "calculator_id": "fmea-rpn",
        "formula": "RPN = severity × occurrence × detection",
        "inputs": {"severity": severity, "occurrence": occurrence, "detection": detection},
        "results": {"rpn": rpn, "priority_band": band},
        "engineering_note": _note(
            "FMEA-style risk priority number",
            "RPN = S × O × D",
            {"S": severity, "O": occurrence, "D": detection},
            {"RPN": rpn, "priority": band},
            ["Scores are ordinal review aids, not precise probabilities or guaranteed risk estimates."],
            ["Review high-severity hazards even if the RPN is moderate.", "Use organization-specific FMEA scoring definitions, controls, owners, and residual-risk tracking."],
        ),
    }
    return result("FMEA Risk Priority Number", "Computed an FMEA-style risk priority number and priority band.", values, _common_warnings(), graphs, ["Clamped input scores to 1–10.", "Multiplied severity, occurrence, and detection."], "python/numpy/matplotlib")


CalculatorFn = Callable[[dict[str, Any]], dict[str, Any]]

CALCULATOR_SPECS: list[dict[str, Any]] = [
    {
        "id": "force-mass-acceleration", "title": "Force, Mass, and Acceleration", "domain": "Mechanical engineering", "family": "Core mechanics", "description": "Compute force from mass and acceleration using F = m a.",
        "inputs": [
            {"name": "mass_kg", "label": "Mass", "type": "number", "default": "12", "unit": "kg", "help": "Object or effective moving mass."},
            {"name": "acceleration_m_s2", "label": "Acceleration", "type": "number", "default": "3.5", "unit": "m/s²", "help": "Acceleration along the direction of interest."},
        ],
    },
    {
        "id": "normal-stress", "title": "Normal Stress", "domain": "Mechanical / structural engineering", "family": "Stress and strain", "description": "Compute axial normal stress from force and area using σ = F/A.",
        "inputs": [
            {"name": "force_N", "label": "Force", "type": "number", "default": "1000", "unit": "N", "help": "Axial force or load."},
            {"name": "area_m2", "label": "Area", "type": "number", "default": "0.02", "unit": "m²", "help": "Net load-bearing area."},
        ],
    },
    {
        "id": "axial-strain", "title": "Axial Strain", "domain": "Mechanical / structural engineering", "family": "Stress and strain", "description": "Compute engineering strain from elongation and original length.",
        "inputs": [
            {"name": "elongation_m", "label": "Elongation ΔL", "type": "number", "default": "0.001", "unit": "m", "help": "Change in length."},
            {"name": "length_m", "label": "Original length L", "type": "number", "default": "2", "unit": "m", "help": "Original gauge length."},
        ],
    },
    {
        "id": "factor-of-safety", "title": "Factor of Safety", "domain": "Engineering review", "family": "Margins", "description": "Compute a simple demand-capacity factor of safety.",
        "inputs": [
            {"name": "allowable_value", "label": "Allowable capacity", "type": "number", "default": "250", "unit": "same as applied", "help": "Capacity, allowable stress, allowable load, or limit value."},
            {"name": "applied_value", "label": "Applied demand", "type": "number", "default": "100", "unit": "same as allowable", "help": "Demand, applied stress, load, or actual value."},
        ],
    },
    {
        "id": "beam-deflection", "title": "Beam Deflection", "domain": "Structural engineering", "family": "Beam formulas", "description": "Compute simplified Euler-Bernoulli beam deflection for two common point-load cases.",
        "inputs": [
            {"name": "beam_case", "label": "Beam case", "type": "select", "default": "cantilever_point", "options": ["cantilever_point", "simply_supported_center"], "help": "Cantilever end load or simply supported center point load."},
            {"name": "load_N", "label": "Point load", "type": "number", "default": "500", "unit": "N", "help": "Applied point load."},
            {"name": "length_m", "label": "Span / length", "type": "number", "default": "2", "unit": "m", "help": "Beam length."},
            {"name": "elastic_modulus_GPa", "label": "Elastic modulus", "type": "number", "default": "200", "unit": "GPa", "help": "Young's modulus."},
            {"name": "second_moment_m4", "label": "Second moment of area", "type": "number", "default": "0.000008", "unit": "m⁴", "help": "Area moment of inertia about the bending axis."},
        ],
    },
    {
        "id": "ohms-law-power", "title": "Ohm's Law and Power", "domain": "Electrical engineering", "family": "Circuits", "description": "Compute current and power for a simplified resistive circuit.",
        "inputs": [
            {"name": "voltage_V", "label": "Voltage", "type": "number", "default": "12", "unit": "V", "help": "Applied voltage."},
            {"name": "resistance_ohm", "label": "Resistance", "type": "number", "default": "6", "unit": "Ω", "help": "Resistance."},
        ],
    },
    {
        "id": "rc-time-constant", "title": "RC Time Constant and Response", "domain": "Electrical engineering", "family": "Transient circuits", "description": "Compute RC time constant and first-order capacitor voltage response.",
        "inputs": [
            {"name": "resistance_ohm", "label": "Resistance", "type": "number", "default": "10000", "unit": "Ω", "help": "Resistance."},
            {"name": "capacitance_F", "label": "Capacitance", "type": "number", "default": "0.000001", "unit": "F", "help": "Capacitance."},
            {"name": "initial_voltage_V", "label": "Initial voltage", "type": "number", "default": "0", "unit": "V", "help": "Initial capacitor voltage."},
            {"name": "final_voltage_V", "label": "Final voltage", "type": "number", "default": "5", "unit": "V", "help": "Final/source voltage."},
            {"name": "time_s", "label": "Evaluation time", "type": "number", "default": "0.01", "unit": "s", "help": "Time at which to evaluate the response."},
        ],
    },
    {
        "id": "conduction-heat-transfer", "title": "Conduction Heat Transfer", "domain": "Thermal engineering", "family": "Heat transfer", "description": "Compute steady one-dimensional conduction heat-transfer rate.",
        "inputs": [
            {"name": "thermal_conductivity_W_mK", "label": "Thermal conductivity", "type": "number", "default": "0.8", "unit": "W/(m·K)", "help": "Material thermal conductivity."},
            {"name": "area_m2", "label": "Area", "type": "number", "default": "10", "unit": "m²", "help": "Heat-transfer area."},
            {"name": "delta_T_K", "label": "Temperature difference", "type": "number", "default": "20", "unit": "K", "help": "Temperature difference across the layer."},
            {"name": "thickness_m", "label": "Thickness", "type": "number", "default": "0.1", "unit": "m", "help": "Layer thickness."},
        ],
    },
    {
        "id": "pump-power", "title": "Pump Power", "domain": "Fluids / energy systems", "family": "Fluid power", "description": "Compute simplified hydraulic and required shaft power for a pump.",
        "inputs": [
            {"name": "fluid_density_kg_m3", "label": "Fluid density", "type": "number", "default": "1000", "unit": "kg/m³", "help": "Fluid density."},
            {"name": "flow_rate_m3_s", "label": "Flow rate", "type": "number", "default": "0.02", "unit": "m³/s", "help": "Volumetric flow rate."},
            {"name": "head_m", "label": "Head", "type": "number", "default": "10", "unit": "m", "help": "Total dynamic head."},
            {"name": "efficiency", "label": "Efficiency", "type": "number", "default": "0.7", "unit": "fraction or %", "help": "Use 0.7 or 70 for 70%."},
        ],
    },
    {
        "id": "energy-emissions", "title": "Energy Emissions", "domain": "Energy / sustainability engineering", "family": "Energy and emissions", "description": "Estimate emissions from energy use and an emission factor.",
        "inputs": [
            {"name": "energy_kwh", "label": "Energy use", "type": "number", "default": "10000", "unit": "kWh", "help": "Energy use over the reporting period."},
            {"name": "emission_factor_kg_per_kwh", "label": "Emission factor", "type": "number", "default": "0.4", "unit": "kg CO₂e/kWh", "help": "Emission factor for the energy source."},
        ],
    },
    {
        "id": "fmea-rpn", "title": "FMEA Risk Priority Number", "domain": "Reliability / risk engineering", "family": "Risk screening", "description": "Compute an FMEA-style RPN from severity, occurrence, and detection scores.",
        "inputs": [
            {"name": "severity", "label": "Severity", "type": "number", "default": "7", "unit": "1–10", "help": "Severity score."},
            {"name": "occurrence", "label": "Occurrence", "type": "number", "default": "4", "unit": "1–10", "help": "Occurrence likelihood score."},
            {"name": "detection", "label": "Detection", "type": "number", "default": "5", "unit": "1–10", "help": "Detection difficulty score; higher usually means harder to detect."},
        ],
    },
]

_CALCULATORS: dict[str, CalculatorFn] = {
    "force-mass-acceleration": calc_force_mass_acceleration,
    "normal-stress": calc_normal_stress,
    "axial-strain": calc_axial_strain,
    "factor-of-safety": calc_factor_of_safety,
    "beam-deflection": calc_beam_deflection,
    "ohms-law-power": calc_ohms_law_power,
    "rc-time-constant": calc_rc_response,
    "conduction-heat-transfer": calc_conduction_heat_transfer,
    "pump-power": calc_pump_power,
    "energy-emissions": calc_energy_emissions,
    "fmea-rpn": calc_rpn,
}


def list_core_engineering_calculators() -> list[dict[str, Any]]:
    return CALCULATOR_SPECS


def get_core_engineering_calculator(calculator_id: str) -> dict[str, Any] | None:
    for spec in CALCULATOR_SPECS:
        if spec["id"] == calculator_id:
            return spec
    return None


def run_core_engineering_calculator(calculator_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    calc = _CALCULATORS.get(calculator_id)
    if not calc:
        return {
            "ok": False,
            "tool": "Core Engineering Calculators",
            "error": f"Unknown engineering calculator: {calculator_id}",
            "available_calculators": [spec["id"] for spec in CALCULATOR_SPECS],
        }
    return calc(inputs)
