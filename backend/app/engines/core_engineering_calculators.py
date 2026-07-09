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


def _series_from_text(value: Any, default: list[float]) -> list[float]:
    """Parse comma/space separated numeric series for lightweight calculator inputs."""
    if value is None or value == "":
        return list(default)
    raw = str(value).replace("\n", ",").replace(";", ",")
    out: list[float] = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            x = float(part)
            if math.isfinite(x):
                out.append(x)
        except Exception:
            continue
    return out or list(default)


def _matrix_from_text(value: Any, default: list[list[float]]) -> list[list[float]]:
    """Parse rows like '1,2,3; 2,3,4; 4,5,6'."""
    if value is None or value == "":
        return [list(row) for row in default]
    rows: list[list[float]] = []
    for row in str(value).replace("\n", ";").split(';'):
        vals = []
        for part in row.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                x = float(part)
                if math.isfinite(x):
                    vals.append(x)
            except Exception:
                continue
        if vals:
            rows.append(vals)
    if not rows:
        return [list(row) for row in default]
    min_len = min(len(r) for r in rows)
    return [r[:min_len] for r in rows if len(r) >= min_len]


def _scatter_with_fit(x: np.ndarray, y: np.ndarray, yhat: np.ndarray, title: str, xlabel: str, ylabel: str) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.scatter(x, y, s=36, alpha=0.85)
    order = np.argsort(x)
    ax.plot(x[order], yhat[order], linewidth=2.25)
    ax.grid(alpha=0.24)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    svg = svg_from_figure(fig)
    plt.close(fig)
    return {"title": title, "type": "scatter_with_fit", "svg": svg}


def calc_econometrics_ols(inputs: dict[str, Any]) -> dict[str, Any]:
    x = np.array(_series_from_text(inputs.get("x_values"), [1, 2, 3, 4, 5, 6, 7, 8]), dtype=float)
    y = np.array(_series_from_text(inputs.get("y_values"), [2.1, 2.9, 3.7, 4.4, 5.2, 5.8, 6.7, 7.4]), dtype=float)
    n = int(min(len(x), len(y)))
    x, y = x[:n], y[:n]
    if n < 2 or float(np.var(x)) <= 1e-12:
        return {"ok": False, "tool": "Econometrics: Simple OLS", "error": "Provide at least two paired x/y observations with variation in x."}
    slope, intercept = np.polyfit(x, y, 1)
    yhat = intercept + slope * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    graphs = [_scatter_with_fit(x, y, yhat, "OLS fit with observed points", "x", "y")]
    values = {
        "calculator_id": "econometrics-simple-ols",
        "formula": "y = β0 + β1 x + ε",
        "inputs": {"x_values": x.tolist(), "y_values": y.tolist(), "observations": n},
        "results": {"intercept_beta0": float(intercept), "slope_beta1": float(slope), "r_squared": float(r2), "equation": f"y = {_fmt(intercept)} + {_fmt(slope)} x"},
        "engineering_note": _note(
            "Simple ordinary least squares regression",
            "y = β0 + β1 x + ε",
            {"n": n, "x": "paired numeric series", "y": "paired numeric series"},
            {"β0": _fmt(float(intercept)), "β1": _fmt(float(slope)), "R²": _fmt(float(r2))},
            ["Single predictor linear relationship is assumed for this first-pass calculator.", "Observations are treated as paired and independent."],
            ["Inspect residuals, leverage, outliers, omitted variables, nonlinearity, heteroskedasticity, autocorrelation, and causal identification before relying on the model."]
        ),
    }
    return result("Econometrics: Simple OLS", "Estimated an ordinary least squares line, R², and fit graph from paired observations.", values, _common_warnings(["Econometric outputs are descriptive unless a research design supports causal interpretation."]), graphs, ["Parsed paired numeric series.", "Fit y = β0 + β1x using least squares."], "python/numpy/matplotlib")


def calc_econometrics_difference_in_differences(inputs: dict[str, Any]) -> dict[str, Any]:
    t0 = _num(inputs.get("treated_pre"), 100.0)
    t1 = _num(inputs.get("treated_post"), 122.0)
    c0 = _num(inputs.get("control_pre"), 98.0)
    c1 = _num(inputs.get("control_post"), 107.0)
    treated_change = t1 - t0
    control_change = c1 - c0
    did = treated_change - control_change
    graphs = [_bar(["Treated pre", "Treated post", "Control pre", "Control post"], [t0, t1, c0, c1], "Difference-in-differences means", "Outcome")]
    values = {
        "calculator_id": "econometrics-difference-in-differences",
        "formula": "DiD = (T_post - T_pre) - (C_post - C_pre)",
        "inputs": {"treated_pre": t0, "treated_post": t1, "control_pre": c0, "control_post": c1},
        "results": {"treated_change": treated_change, "control_change": control_change, "difference_in_differences": did},
        "engineering_note": _note(
            "Difference-in-differences estimate",
            "DiD = (T_post - T_pre) - (C_post - C_pre)",
            {"T_pre": _fmt(t0), "T_post": _fmt(t1), "C_pre": _fmt(c0), "C_post": _fmt(c1)},
            {"treated_change": _fmt(treated_change), "control_change": _fmt(control_change), "DiD": _fmt(did)},
            ["Two-period, two-group comparison is assumed.", "The control change is treated as the counterfactual trend for the treated group."],
            ["Parallel trends is an identification assumption and cannot be proven by this calculator.", "Use full panel data, uncertainty estimates, placebo checks, and domain review for serious econometric work."]
        ),
    }
    return result("Econometrics: Difference-in-Differences", "Computed a first-pass two-group/two-period difference-in-differences contrast.", values, _common_warnings(["Do not interpret as causal without validating the research design and assumptions."]), graphs, ["Computed treated and control changes.", "Subtracted the control change from the treated change."], "python/numpy/matplotlib")


def calc_psychometrics_cronbach_alpha(inputs: dict[str, Any]) -> dict[str, Any]:
    default = [[4, 5, 4, 5], [3, 4, 4, 4], [5, 5, 5, 4], [2, 3, 3, 3], [4, 4, 5, 4], [3, 4, 3, 4]]
    rows = _matrix_from_text(inputs.get("item_scores"), default)
    arr = np.array(rows, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 2:
        return {"ok": False, "tool": "Psychometrics: Cronbach's Alpha", "error": "Provide at least two respondents and two items, for example: 4,5,4; 3,4,4; 5,5,5."}
    k = arr.shape[1]
    item_vars = np.var(arr, axis=0, ddof=1)
    total_scores = np.sum(arr, axis=1)
    total_var = float(np.var(total_scores, ddof=1))
    alpha = float(k / (k - 1) * (1 - float(np.sum(item_vars)) / total_var)) if total_var > 1e-12 else 0.0
    graphs = [_bar([f"Item {i+1}" for i in range(k)], [float(v) for v in item_vars], "Item score variances", "Variance")]
    band = "high internal consistency" if alpha >= 0.9 else "acceptable/review" if alpha >= 0.7 else "low or heterogeneous scale"
    values = {
        "calculator_id": "psychometrics-cronbach-alpha",
        "formula": "α = k/(k-1) · (1 - Σσ_i² / σ_total²)",
        "inputs": {"respondents": int(arr.shape[0]), "items": int(k), "item_scores": rows},
        "results": {"cronbach_alpha": alpha, "interpretation_band": band},
        "engineering_note": _note(
            "Cronbach's alpha internal-consistency estimate",
            "α = k/(k-1) · (1 - Σσ_i² / σ_total²)",
            {"respondents": arr.shape[0], "items": k},
            {"α": _fmt(alpha), "band": band},
            ["Items are treated as a scale intended to measure a related construct.", "Rows are respondents and columns are items."],
            ["Alpha is not proof of validity, unidimensionality, fairness, or clinical appropriateness.", "Review item wording, dimensionality, measurement invariance, sample size, and intended use."]
        ),
    }
    return result("Psychometrics: Cronbach's Alpha", "Estimated scale internal consistency from item-score rows.", values, _common_warnings(["Psychometric outputs are educational and must not be used for diagnosis, hiring, eligibility, or clinical decisions without validated instruments and qualified review."]), graphs, ["Computed item variances and total-score variance.", "Applied Cronbach's alpha formula."], "python/numpy/matplotlib")


def calc_psychometrics_standard_error_measurement(inputs: dict[str, Any]) -> dict[str, Any]:
    sd = _positive(inputs.get("observed_sd"), 10.0)
    reliability = min(max(_num(inputs.get("reliability"), 0.85), 0.0), 0.999999)
    score = _num(inputs.get("observed_score"), 75.0)
    sem = sd * math.sqrt(max(0.0, 1 - reliability))
    lo, hi = score - 1.96 * sem, score + 1.96 * sem
    rels = np.linspace(0.1, 0.99, 130)
    graphs = [_line(rels, sd * np.sqrt(1 - rels), "SEM sensitivity to reliability", "Reliability", "SEM")]
    values = {
        "calculator_id": "psychometrics-standard-error-measurement",
        "formula": "SEM = SD · √(1-r)",
        "inputs": {"observed_score": score, "observed_sd": sd, "reliability": reliability},
        "results": {"sem": sem, "approx_95_low": lo, "approx_95_high": hi},
        "engineering_note": _note(
            "Standard error of measurement",
            "SEM = SD · √(1-r)",
            {"score": _fmt(score), "SD": _fmt(sd), "reliability": _fmt(reliability)},
            {"SEM": _fmt(sem), "approx_95_interval": f"{_fmt(lo)} to {_fmt(hi)}"},
            ["Reliability is treated as an externally estimated coefficient for the same measurement context."],
            ["SEM is not a validity argument. Interpret with instrument documentation, sampling context, and ethical constraints."]
        ),
    }
    return result("Psychometrics: Standard Error of Measurement", "Computed SEM and an approximate measurement interval from observed SD and reliability.", values, _common_warnings(["Use only with validated measurement instruments and appropriate human review."]), graphs, ["Applied SEM formula.", "Generated reliability sensitivity curve."], "python/numpy/matplotlib")


def calc_biology_logistic_growth(inputs: dict[str, Any]) -> dict[str, Any]:
    N0 = _positive(inputs.get("initial_population"), 10.0)
    r = _num(inputs.get("growth_rate"), 0.4)
    K = _positive(inputs.get("carrying_capacity"), 1000.0)
    t = max(_num(inputs.get("time"), 10.0), 0.0)
    Nt = K / (1 + ((K - N0) / N0) * math.exp(-r * t))
    ts = np.linspace(0, max(t * 1.5, 20.0), 180)
    Ns = K / (1 + ((K - N0) / N0) * np.exp(-r * ts))
    graphs = [_line(ts, Ns, "Logistic growth trajectory", "Time", "Population / concentration")]
    values = {
        "calculator_id": "computational-biology-logistic-growth",
        "formula": "N(t)=K/[1+((K-N0)/N0)e^{-rt}]",
        "inputs": {"initial_population": N0, "growth_rate": r, "carrying_capacity": K, "time": t},
        "results": {"N_t": Nt, "fraction_of_capacity": Nt / K},
        "engineering_note": _note("Logistic growth model", "N(t)=K/[1+((K-N0)/N0)e^{-rt}]", {"N0": _fmt(N0), "r": _fmt(r), "K": _fmt(K), "t": _fmt(t)}, {"N(t)": _fmt(Nt), "N/K": _fmt(Nt/K)}, ["Growth rate and carrying capacity are treated as constant."], ["Validate against data, uncertainty, model residuals, and biological mechanism before interpretation."])
    }
    return result("Computational Biology: Logistic Growth", "Simulated logistic growth and plotted the trajectory.", values, _common_warnings(["Biological models are simplified and parameter-sensitive."]), graphs, ["Applied logistic closed-form solution."], "python/numpy/matplotlib")


def calc_biology_michaelis_menten(inputs: dict[str, Any]) -> dict[str, Any]:
    vmax = _positive(inputs.get("vmax"), 100.0)
    Km = _positive(inputs.get("km"), 5.0)
    S = _positive(inputs.get("substrate_concentration"), 3.0)
    v = vmax * S / (Km + S)
    ss = np.linspace(0, max(S * 4, Km * 6, 10), 180)
    rates = vmax * ss / (Km + ss)
    graphs = [_line(ss, rates, "Michaelis-Menten rate curve", "Substrate concentration", "Reaction rate")]
    values = {"calculator_id": "computational-biology-michaelis-menten", "formula": "v = Vmax[S]/(Km+[S])", "inputs": {"vmax": vmax, "km": Km, "substrate_concentration": S}, "results": {"rate": v, "fraction_of_vmax": v / vmax}, "engineering_note": _note("Michaelis-Menten enzyme kinetics", "v = Vmax[S]/(Km+[S])", {"Vmax": _fmt(vmax), "Km": _fmt(Km), "[S]": _fmt(S)}, {"v": _fmt(v), "v/Vmax": _fmt(v/vmax)}, ["Single-substrate Michaelis-Menten kinetics are assumed."], ["Check enzyme conditions, inhibition, cooperativity, assay error, and unit consistency."])}
    return result("Computational Biology: Michaelis-Menten", "Computed enzyme reaction rate from Vmax, Km, and substrate concentration.", values, _common_warnings(["Lab and biological interpretation require experimental context and qualified review."]), graphs, ["Applied Michaelis-Menten equation."], "python/numpy/matplotlib")


def calc_chemistry_arrhenius(inputs: dict[str, Any]) -> dict[str, Any]:
    A = _positive(inputs.get("pre_exponential_factor"), 1e7)
    Ea = _positive(inputs.get("activation_energy_kJ_mol"), 50.0) * 1000.0
    T = _positive(inputs.get("temperature_K"), 298.15)
    R = 8.314462618
    k = A * math.exp(-Ea / (R * T))
    temps = np.linspace(max(1, T * 0.75), max(T * 1.35, T + 50), 160)
    rates = A * np.exp(-Ea / (R * temps))
    graphs = [_line(temps, rates, "Arrhenius rate sensitivity to temperature", "Temperature (K)", "Rate constant")]
    values = {"calculator_id": "computational-chemistry-arrhenius", "formula": "k = A e^{-Ea/(RT)}", "inputs": {"A": A, "Ea_kJ_mol": Ea/1000, "temperature_K": T}, "results": {"rate_constant": k}, "engineering_note": _note("Arrhenius rate constant", "k = A e^{-Ea/(RT)}", {"A": _fmt(A), "Ea": _fmt(Ea/1000, "kJ/mol"), "T": _fmt(T, "K")}, {"k": _fmt(k)}, ["Activation energy and pre-exponential factor are assumed fixed."], ["Use appropriate reaction order, units, catalyst state, solvent/phase conditions, and experimental uncertainty."])}
    return result("Computational Chemistry: Arrhenius Rate", "Computed an Arrhenius rate constant and temperature sensitivity curve.", values, _common_warnings(["Computational chemistry outputs are simplified first-pass calculations."]), graphs, ["Applied k=A exp(-Ea/RT)."], "python/numpy/matplotlib")


def calc_chemistry_nernst(inputs: dict[str, Any]) -> dict[str, Any]:
    E0 = _num(inputs.get("standard_potential_V"), 1.10)
    n = _positive(inputs.get("electrons"), 2.0)
    T = _positive(inputs.get("temperature_K"), 298.15)
    Q = _positive(inputs.get("reaction_quotient"), 1.0)
    R = 8.314462618
    F_const = 96485.33212
    E = E0 - (R * T / (n * F_const)) * math.log(Q)
    qs = np.logspace(-3, 3, 180)
    Es = E0 - (R * T / (n * F_const)) * np.log(qs)
    graphs = [_line(qs, Es, "Nernst potential vs reaction quotient", "Reaction quotient Q", "Cell potential (V)")]
    values = {"calculator_id": "computational-chemistry-nernst", "formula": "E = E° - (RT/nF)ln(Q)", "inputs": {"E0_V": E0, "electrons": n, "temperature_K": T, "reaction_quotient": Q}, "results": {"cell_potential_V": E}, "engineering_note": _note("Nernst equation", "E = E° - (RT/nF)ln(Q)", {"E°": _fmt(E0, "V"), "n": _fmt(n), "T": _fmt(T, "K"), "Q": _fmt(Q)}, {"E": _fmt(E, "V")}, ["Ideal activity approximation may be implicit if concentrations are used."], ["Check activities, phase state, temperature, electrode definitions, sign conventions, and reaction quotient construction."])}
    return result("Computational Chemistry: Nernst Potential", "Computed electrochemical potential from the Nernst equation.", values, _common_warnings(["Electrochemical calculations require correct reaction stoichiometry and activity assumptions."]), graphs, ["Applied E = E° - RT/(nF) ln Q."], "python/numpy/matplotlib")


def calc_physics_harmonic_oscillator(inputs: dict[str, Any]) -> dict[str, Any]:
    m = _positive(inputs.get("mass_kg"), 1.0)
    k = _positive(inputs.get("spring_constant_N_m"), 25.0)
    Aamp = _positive(inputs.get("amplitude_m"), 0.1)
    t = max(_num(inputs.get("time_s"), 1.0), 0.0)
    omega = math.sqrt(k / m)
    x_t = Aamp * math.cos(omega * t)
    energy = 0.5 * k * Aamp ** 2
    ts = np.linspace(0, max(t * 2, 4 * math.pi / omega), 200)
    xs = Aamp * np.cos(omega * ts)
    graphs = [_line(ts, xs, "Simple harmonic oscillator displacement", "Time (s)", "Displacement (m)")]
    values = {"calculator_id": "computational-physics-harmonic-oscillator", "formula": "ω = √(k/m); x(t)=A cos(ωt)", "inputs": {"mass_kg": m, "spring_constant_N_m": k, "amplitude_m": Aamp, "time_s": t}, "results": {"omega_rad_s": omega, "period_s": 2*math.pi/omega, "x_t_m": x_t, "total_energy_J": energy}, "engineering_note": _note("Undamped simple harmonic oscillator", "ω = √(k/m); x(t)=A cos(ωt)", {"m": _fmt(m, "kg"), "k": _fmt(k, "N/m"), "A": _fmt(Aamp, "m"), "t": _fmt(t, "s")}, {"ω": _fmt(omega, "rad/s"), "T": _fmt(2*math.pi/omega, "s"), "x(t)": _fmt(x_t, "m"), "E": _fmt(energy, "J")}, ["No damping, forcing, nonlinear stiffness, or friction is included."], ["For real systems, estimate damping, resonance, boundary conditions, fatigue, and measurement uncertainty."])}
    return result("Computational Physics: Harmonic Oscillator", "Computed oscillator frequency, period, displacement, energy, and trajectory.", values, _common_warnings(["Physical models are simplified and require experimental or engineering validation."]), graphs, ["Computed natural angular frequency and displacement."], "python/numpy/matplotlib")


def calc_physics_projectile_motion(inputs: dict[str, Any]) -> dict[str, Any]:
    v0 = _positive(inputs.get("initial_speed_m_s"), 30.0)
    angle = math.radians(_num(inputs.get("angle_deg"), 45.0))
    y0 = max(_num(inputs.get("initial_height_m"), 0.0), 0.0)
    g = _positive(inputs.get("gravity_m_s2"), G)
    vx, vy = v0 * math.cos(angle), v0 * math.sin(angle)
    flight = (vy + math.sqrt(vy**2 + 2*g*y0)) / g
    rng = vx * flight
    hmax = y0 + vy**2/(2*g)
    ts = np.linspace(0, flight, 180)
    xs = vx * ts
    ys = y0 + vy * ts - 0.5 * g * ts**2
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(xs, ys, linewidth=2.25)
    ax.axhline(0, linewidth=0.85, color="black", alpha=0.25)
    ax.grid(alpha=0.24); ax.set_xlabel("Horizontal distance (m)"); ax.set_ylabel("Height (m)"); ax.set_title("Projectile trajectory"); fig.tight_layout(); svg=svg_from_figure(fig); plt.close(fig)
    graphs = [{"title": "Projectile trajectory", "type": "trajectory", "svg": svg}]
    values = {"calculator_id": "computational-physics-projectile-motion", "formula": "x=v0 cosθ t; y=y0+v0 sinθ t - 1/2 gt²", "inputs": {"initial_speed_m_s": v0, "angle_deg": math.degrees(angle), "initial_height_m": y0, "gravity_m_s2": g}, "results": {"time_of_flight_s": flight, "range_m": rng, "max_height_m": hmax}, "engineering_note": _note("Ideal projectile motion", "x=v0 cosθ t; y=y0+v0 sinθ t - 1/2 gt²", {"v0": _fmt(v0, "m/s"), "θ": _fmt(math.degrees(angle), "deg"), "y0": _fmt(y0, "m"), "g": _fmt(g, "m/s²")}, {"flight_time": _fmt(flight, "s"), "range": _fmt(rng, "m"), "max_height": _fmt(hmax, "m")}, ["No drag, wind, lift, spin, or terrain variation is included."], ["Use more complete dynamics for safety-critical, ballistic, aerospace, or field-operation analysis."])}
    return result("Computational Physics: Projectile Motion", "Computed ideal projectile range, flight time, peak height, and trajectory.", values, _common_warnings(["Ideal projectile equations ignore drag and environmental effects."]), graphs, ["Resolved initial velocity into horizontal and vertical components.", "Solved the vertical motion for flight time."], "python/numpy/matplotlib")


def calc_architecture_floor_area_efficiency(inputs: dict[str, Any]) -> dict[str, Any]:
    gross = _positive(inputs.get("gross_floor_area_m2"), 1000.0)
    net = _positive(inputs.get("net_usable_area_m2"), 720.0)
    occupants = _positive(inputs.get("occupants"), 80.0)
    eff = min(net / gross, 10.0)
    area_per_occ = net / occupants
    graphs = [_bar(["Gross floor area", "Net usable area"], [gross, net], "Gross vs net usable area", "m²")]
    values = {"calculator_id": "architecture-floor-area-efficiency", "formula": "efficiency = net usable area / gross floor area", "inputs": {"gross_floor_area_m2": gross, "net_usable_area_m2": net, "occupants": occupants}, "results": {"area_efficiency": eff, "net_area_per_occupant_m2": area_per_occ}, "engineering_note": _note("Architectural area efficiency", "η_area = A_net/A_gross", {"A_gross": _fmt(gross, "m²"), "A_net": _fmt(net, "m²"), "occupants": _fmt(occupants)}, {"η_area": _fmt(eff), "net area/occupant": _fmt(area_per_occ, "m²/person")}, ["Gross and net area definitions must be consistent."], ["Check local codes, accessibility, egress, occupancy classification, program requirements, and professional architectural review."])}
    return result("Architecture: Floor-Area Efficiency", "Computed net-to-gross area efficiency and net area per occupant.", values, _common_warnings(["Architecture outputs are planning aids and not code review, life-safety certification, or professional design approval."]), graphs, ["Divided usable area by gross area.", "Computed area per occupant."], "python/numpy/matplotlib")


def calc_architecture_daylight_aperture(inputs: dict[str, Any]) -> dict[str, Any]:
    floor = _positive(inputs.get("floor_area_m2"), 100.0)
    glazing = _positive(inputs.get("glazing_area_m2"), 18.0)
    visible = min(max(_num(inputs.get("visible_transmittance"), 0.6), 0.0), 1.0)
    ratio = glazing / floor
    effective = ratio * visible
    graphs = [_bar(["Glazing/floor ratio", "Effective aperture"], [ratio, effective], "Daylight aperture indicators", "Ratio")]
    values = {"calculator_id": "architecture-daylight-aperture", "formula": "effective aperture = (glazing area / floor area) × visible transmittance", "inputs": {"floor_area_m2": floor, "glazing_area_m2": glazing, "visible_transmittance": visible}, "results": {"glazing_to_floor_ratio": ratio, "effective_aperture": effective}, "engineering_note": _note("Daylight aperture screening", "EA = (A_glazing/A_floor) · VT", {"A_floor": _fmt(floor, "m²"), "A_glazing": _fmt(glazing, "m²"), "VT": _fmt(visible)}, {"GFR": _fmt(ratio), "EA": _fmt(effective)}, ["This is a simplified aperture screening metric, not a daylight simulation."], ["Review orientation, shading, climate, room depth, reflectance, glare, thermal gains, and code/standard requirements."])}
    return result("Architecture: Daylight Aperture", "Computed glazing-to-floor ratio and an effective aperture proxy.", values, _common_warnings(["Use daylight simulation and professional design review for real projects."]), graphs, ["Computed glazing/floor ratio.", "Adjusted by visible transmittance."], "python/numpy/matplotlib")


def calc_infrastructure_peak_water_demand(inputs: dict[str, Any]) -> dict[str, Any]:
    population = _positive(inputs.get("population"), 10000.0)
    per_capita = _positive(inputs.get("per_capita_L_day"), 180.0)
    peak = _positive(inputs.get("peak_factor"), 2.5)
    avg_m3_day = population * per_capita / 1000.0
    peak_m3_day = avg_m3_day * peak
    peak_L_s = peak_m3_day * 1000 / 86400
    pops = np.linspace(max(1, population*0.25), max(population*2, 1000), 130)
    graphs = [_line(pops, pops * per_capita / 1000 * peak, "Peak demand sensitivity to population", "Population", "Peak demand (m³/day)")]
    values = {"calculator_id": "infrastructure-peak-water-demand", "formula": "Q_peak = population × per-capita demand × peak factor", "inputs": {"population": population, "per_capita_L_day": per_capita, "peak_factor": peak}, "results": {"average_demand_m3_day": avg_m3_day, "peak_demand_m3_day": peak_m3_day, "peak_demand_L_s": peak_L_s}, "engineering_note": _note("Peak water demand screening", "Q_peak = P · q · PF", {"P": _fmt(population), "q": _fmt(per_capita, "L/person/day"), "PF": _fmt(peak)}, {"Q_avg": _fmt(avg_m3_day, "m³/day"), "Q_peak": _fmt(peak_m3_day, "m³/day"), "Q_peak": _fmt(peak_L_s, "L/s")}, ["Per-capita demand and peak factor are treated as planning-level inputs."], ["Check local design standards, fire flow, leakage, pressure zones, storage, seasonal patterns, and hydraulic model results."])}
    return result("Infrastructure: Peak Water Demand", "Estimated average and peak water demand for infrastructure planning.", values, _common_warnings(["Infrastructure calculators are planning screens, not design certification."]), graphs, ["Computed average daily demand.", "Applied peak factor and converted to L/s."], "python/numpy/matplotlib")


def calc_infrastructure_rational_runoff(inputs: dict[str, Any]) -> dict[str, Any]:
    C = min(max(_num(inputs.get("runoff_coefficient"), 0.6), 0.0), 1.0)
    i = _positive(inputs.get("rainfall_intensity_mm_hr"), 50.0)
    A_ha = _positive(inputs.get("drainage_area_ha"), 2.0)
    Q = 0.00278 * C * i * A_ha  # m3/s when i mm/hr and A ha
    intensities = np.linspace(0, max(i*2, 100), 130)
    graphs = [_line(intensities, 0.00278 * C * intensities * A_ha, "Runoff sensitivity to rainfall intensity", "Rainfall intensity (mm/hr)", "Peak runoff (m³/s)")]
    values = {"calculator_id": "infrastructure-rational-runoff", "formula": "Q = 0.00278 C i A", "inputs": {"runoff_coefficient": C, "rainfall_intensity_mm_hr": i, "drainage_area_ha": A_ha}, "results": {"peak_runoff_m3_s": Q}, "engineering_note": _note("Rational method runoff estimate", "Q = 0.00278 C i A", {"C": _fmt(C), "i": _fmt(i, "mm/hr"), "A": _fmt(A_ha, "ha")}, {"Q": _fmt(Q, "m³/s")}, ["Small catchment rational-method screening is assumed."], ["Check time of concentration, rainfall IDF curve, local standards, detention, inlet capacity, pipe hydraulics, and downstream constraints."])}
    return result("Infrastructure: Rational Runoff", "Estimated peak stormwater runoff with the rational method.", values, _common_warnings(["Stormwater calculations require local design standards and professional civil review."]), graphs, ["Applied rational method unit conversion for mm/hr and hectares."], "python/numpy/matplotlib")


def calc_pattern_cosine_similarity(inputs: dict[str, Any]) -> dict[str, Any]:
    a = np.array(_series_from_text(inputs.get("pattern_a"), [1, 0, 1, 1, 0, 1]), dtype=float)
    b = np.array(_series_from_text(inputs.get("pattern_b"), [1, 1, 1, 0, 0, 1]), dtype=float)
    n = int(min(len(a), len(b)))
    a, b = a[:n], b[:n]
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    sim = float(np.dot(a, b) / denom) if denom > 1e-12 else 0.0
    graphs = [_bar([f"p{i+1}" for i in range(n)], (a-b).tolist(), "Pattern difference vector", "A - B")]
    values = {"calculator_id": "pattern-recognition-cosine-similarity", "formula": "cos(θ)=A·B/(||A||||B||)", "inputs": {"pattern_a": a.tolist(), "pattern_b": b.tolist()}, "results": {"cosine_similarity": sim, "cosine_distance": 1 - sim}, "engineering_note": _note("Pattern cosine similarity", "cos(θ)=A·B/(||A||||B||)", {"A": "numeric feature vector", "B": "numeric feature vector"}, {"similarity": _fmt(sim), "distance": _fmt(1-sim)}, ["Patterns are represented as equal-length numeric feature vectors."], ["Feature design determines meaning. For art/music/math comparisons, document how features were derived."])}
    return result("Pattern Recognition: Cosine Similarity", "Computed vector similarity for mathematical, visual, or musical pattern features.", values, _common_warnings(["Pattern-recognition outputs depend strongly on feature representation and preprocessing."]), graphs, ["Aligned the two vectors to common length.", "Computed normalized dot-product similarity."], "python/numpy/matplotlib")


def calc_pattern_harmonic_centroid(inputs: dict[str, Any]) -> dict[str, Any]:
    amps = np.array(_series_from_text(inputs.get("harmonic_amplitudes"), [1.0, 0.5, 0.25, 0.125, 0.08]), dtype=float)
    base = _positive(inputs.get("base_frequency_hz"), 220.0)
    idx = np.arange(1, len(amps)+1, dtype=float)
    freqs = base * idx
    total_amp = float(np.sum(np.abs(amps)))
    centroid = float(np.sum(freqs * np.abs(amps)) / total_amp) if total_amp > 1e-12 else base
    brightness = centroid / base
    graphs = [_bar([f"H{i}" for i in range(1, len(amps)+1)], amps.tolist(), "Harmonic amplitude pattern", "Amplitude")]
    values = {"calculator_id": "pattern-recognition-harmonic-centroid", "formula": "centroid = Σ(f_i a_i)/Σa_i", "inputs": {"base_frequency_hz": base, "harmonic_amplitudes": amps.tolist()}, "results": {"spectral_centroid_hz": centroid, "centroid_multiple_of_base": brightness}, "engineering_note": _note("Harmonic centroid / pattern brightness", "centroid = Σ(f_i a_i)/Σa_i", {"f0": _fmt(base, "Hz"), "harmonics": len(amps)}, {"centroid": _fmt(centroid, "Hz"), "centroid/f0": _fmt(brightness)}, ["Harmonic amplitudes are treated as feature weights."], ["For real audio, use windowing, sampling-rate-aware FFT, normalization, and perceptual weighting."])}
    return result("Pattern Recognition: Harmonic Centroid", "Computed a harmonic-pattern centroid useful for music/math/art pattern interpretation.", values, _common_warnings(["This is symbolic/audio-feature screening, not full audio analysis."]), graphs, ["Mapped harmonic index to frequency.", "Computed weighted frequency centroid."], "python/numpy/matplotlib")


def calc_astrophysics_kepler_orbit(inputs: dict[str, Any]) -> dict[str, Any]:
    a_au = _positive(inputs.get("semi_major_axis_AU"), 1.0)
    mass_solar = _positive(inputs.get("central_mass_solar"), 1.0)
    period_years = math.sqrt(a_au**3 / mass_solar)
    axes = np.linspace(max(0.01, a_au*0.2), max(a_au*2.5, 5.0), 160)
    periods = np.sqrt(axes**3 / mass_solar)
    graphs = [_line(axes, periods, "Keplerian orbital period vs semi-major axis", "Semi-major axis (AU)", "Period (years)")]
    values = {"calculator_id": "astrophysics-kepler-orbit", "formula": "P² = a³/M", "inputs": {"semi_major_axis_AU": a_au, "central_mass_solar": mass_solar}, "results": {"period_years": period_years, "period_days": period_years*365.25}, "engineering_note": _note("Kepler orbit period", "P² = a³/M", {"a": _fmt(a_au, "AU"), "M": _fmt(mass_solar, "solar masses")}, {"P": _fmt(period_years, "years"), "P": _fmt(period_years*365.25, "days")}, ["Two-body Keplerian orbit and solar-system units are assumed."], ["Perturbations, eccentricity effects on instantaneous speed, relativity, and non-point-mass effects are not included."])}
    return result("Astrophysics: Kepler Orbit", "Computed orbital period from semi-major axis and central mass.", values, _common_warnings(["Astrophysics calculators are simplified educational models unless paired with full data and methods."]), graphs, ["Applied Kepler's third law in AU, solar masses, and years."], "python/numpy/matplotlib")


def calc_astrophysics_luminosity_flux(inputs: dict[str, Any]) -> dict[str, Any]:
    L_solar = _positive(inputs.get("luminosity_solar"), 1.0)
    d_pc = _positive(inputs.get("distance_parsec"), 10.0)
    Lsun = 3.828e26
    pc = 3.085677581e16
    flux = L_solar * Lsun / (4 * math.pi * (d_pc * pc) ** 2)
    distances = np.linspace(max(0.1, d_pc*0.2), max(d_pc*3, 30.0), 160)
    fluxes = L_solar * Lsun / (4 * math.pi * (distances * pc) ** 2)
    graphs = [_line(distances, fluxes, "Inverse-square flux vs distance", "Distance (pc)", "Flux (W/m²)")]
    values = {"calculator_id": "astrophysics-luminosity-flux", "formula": "F = L/(4πd²)", "inputs": {"luminosity_solar": L_solar, "distance_parsec": d_pc}, "results": {"flux_W_m2": flux}, "engineering_note": _note("Luminosity-to-flux inverse-square relation", "F = L/(4πd²)", {"L": _fmt(L_solar, "L☉"), "d": _fmt(d_pc, "pc")}, {"F": _fmt(flux, "W/m²")}, ["Isotropic emission and no extinction/absorption are assumed."], ["For observational astronomy, account for bandpass, extinction, redshift, calibration, and source model."])}
    return result("Astrophysics: Luminosity and Flux", "Computed received flux from luminosity and distance using the inverse-square law.", values, _common_warnings(["Astronomical interpretation requires observational context and data calibration."]), graphs, ["Converted solar luminosity and parsecs to SI units.", "Applied inverse-square law."], "python/numpy/matplotlib")


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

    {
        "id": "econometrics-simple-ols", "title": "Econometrics: Simple OLS", "domain": "Econometrics", "family": "Regression", "description": "Estimate a simple ordinary least squares line from paired x and y observations.",
        "inputs": [
            {"name": "x_values", "label": "x values", "type": "text", "default": "1,2,3,4,5,6,7,8", "unit": "series", "help": "Comma-separated predictor values."},
            {"name": "y_values", "label": "y values", "type": "text", "default": "2.1,2.9,3.7,4.4,5.2,5.8,6.7,7.4", "unit": "series", "help": "Comma-separated outcome values paired with x."},
        ],
    },
    {
        "id": "econometrics-difference-in-differences", "title": "Econometrics: Difference-in-Differences", "domain": "Econometrics", "family": "Causal inference screening", "description": "Compute a two-period/two-group difference-in-differences contrast.",
        "inputs": [
            {"name": "treated_pre", "label": "Treated pre", "type": "number", "default": "100", "unit": "outcome", "help": "Average treated-group outcome before intervention."},
            {"name": "treated_post", "label": "Treated post", "type": "number", "default": "122", "unit": "outcome", "help": "Average treated-group outcome after intervention."},
            {"name": "control_pre", "label": "Control pre", "type": "number", "default": "98", "unit": "outcome", "help": "Average control-group outcome before intervention."},
            {"name": "control_post", "label": "Control post", "type": "number", "default": "107", "unit": "outcome", "help": "Average control-group outcome after intervention."},
        ],
    },
    {
        "id": "psychometrics-cronbach-alpha", "title": "Psychometrics: Cronbach's Alpha", "domain": "Psychometrics", "family": "Scale reliability", "description": "Estimate internal consistency from item score rows.",
        "inputs": [
            {"name": "item_scores", "label": "Item-score rows", "type": "text", "default": "4,5,4,5; 3,4,4,4; 5,5,5,4; 2,3,3,3; 4,4,5,4; 3,4,3,4", "unit": "rows", "help": "Rows are respondents; columns are scale items. Separate rows with semicolons."},
        ],
    },
    {
        "id": "psychometrics-standard-error-measurement", "title": "Psychometrics: Standard Error of Measurement", "domain": "Psychometrics", "family": "Measurement error", "description": "Compute SEM and an approximate measurement interval from observed SD and reliability.",
        "inputs": [
            {"name": "observed_score", "label": "Observed score", "type": "number", "default": "75", "unit": "score", "help": "Observed test or scale score."},
            {"name": "observed_sd", "label": "Observed SD", "type": "number", "default": "10", "unit": "score", "help": "Observed standard deviation for the score scale."},
            {"name": "reliability", "label": "Reliability", "type": "number", "default": "0.85", "unit": "0–1", "help": "Reliability coefficient for the measurement context."},
        ],
    },
    {
        "id": "computational-biology-logistic-growth", "title": "Computational Biology: Logistic Growth", "domain": "Computational biology", "family": "Population dynamics", "description": "Simulate logistic growth with carrying capacity.",
        "inputs": [
            {"name": "initial_population", "label": "Initial population", "type": "number", "default": "10", "unit": "N0", "help": "Starting population or concentration."},
            {"name": "growth_rate", "label": "Growth rate", "type": "number", "default": "0.4", "unit": "1/time", "help": "Intrinsic growth rate."},
            {"name": "carrying_capacity", "label": "Carrying capacity", "type": "number", "default": "1000", "unit": "K", "help": "Upper limiting capacity."},
            {"name": "time", "label": "Time", "type": "number", "default": "10", "unit": "time", "help": "Evaluation time."},
        ],
    },
    {
        "id": "computational-biology-michaelis-menten", "title": "Computational Biology: Michaelis-Menten", "domain": "Computational biology", "family": "Enzyme kinetics", "description": "Compute enzyme reaction rate from Vmax, Km, and substrate concentration.",
        "inputs": [
            {"name": "vmax", "label": "Vmax", "type": "number", "default": "100", "unit": "rate", "help": "Maximum reaction rate."},
            {"name": "km", "label": "Km", "type": "number", "default": "5", "unit": "concentration", "help": "Michaelis constant."},
            {"name": "substrate_concentration", "label": "Substrate concentration", "type": "number", "default": "3", "unit": "concentration", "help": "Substrate concentration [S]."},
        ],
    },
    {
        "id": "computational-chemistry-arrhenius", "title": "Computational Chemistry: Arrhenius Rate", "domain": "Computational chemistry", "family": "Reaction kinetics", "description": "Compute an Arrhenius rate constant and temperature sensitivity.",
        "inputs": [
            {"name": "pre_exponential_factor", "label": "Pre-exponential factor A", "type": "number", "default": "10000000", "unit": "rate units", "help": "Frequency/pre-exponential factor."},
            {"name": "activation_energy_kJ_mol", "label": "Activation energy", "type": "number", "default": "50", "unit": "kJ/mol", "help": "Activation energy."},
            {"name": "temperature_K", "label": "Temperature", "type": "number", "default": "298.15", "unit": "K", "help": "Absolute temperature."},
        ],
    },
    {
        "id": "computational-chemistry-nernst", "title": "Computational Chemistry: Nernst Potential", "domain": "Computational chemistry", "family": "Electrochemistry", "description": "Compute electrochemical cell potential from the Nernst equation.",
        "inputs": [
            {"name": "standard_potential_V", "label": "Standard potential", "type": "number", "default": "1.10", "unit": "V", "help": "Standard cell potential E°."},
            {"name": "electrons", "label": "Electrons transferred", "type": "number", "default": "2", "unit": "n", "help": "Number of electrons transferred."},
            {"name": "temperature_K", "label": "Temperature", "type": "number", "default": "298.15", "unit": "K", "help": "Absolute temperature."},
            {"name": "reaction_quotient", "label": "Reaction quotient Q", "type": "number", "default": "1", "unit": "Q", "help": "Reaction quotient."},
        ],
    },
    {
        "id": "computational-physics-harmonic-oscillator", "title": "Computational Physics: Harmonic Oscillator", "domain": "Computational physics", "family": "Dynamics", "description": "Compute frequency, period, displacement, energy, and trajectory for an ideal spring-mass oscillator.",
        "inputs": [
            {"name": "mass_kg", "label": "Mass", "type": "number", "default": "1", "unit": "kg", "help": "Oscillating mass."},
            {"name": "spring_constant_N_m", "label": "Spring constant", "type": "number", "default": "25", "unit": "N/m", "help": "Linear spring constant."},
            {"name": "amplitude_m", "label": "Amplitude", "type": "number", "default": "0.1", "unit": "m", "help": "Oscillation amplitude."},
            {"name": "time_s", "label": "Time", "type": "number", "default": "1", "unit": "s", "help": "Evaluation time."},
        ],
    },
    {
        "id": "computational-physics-projectile-motion", "title": "Computational Physics: Projectile Motion", "domain": "Computational physics", "family": "Classical mechanics", "description": "Compute ideal projectile range, flight time, peak height, and trajectory.",
        "inputs": [
            {"name": "initial_speed_m_s", "label": "Initial speed", "type": "number", "default": "30", "unit": "m/s", "help": "Initial launch speed."},
            {"name": "angle_deg", "label": "Launch angle", "type": "number", "default": "45", "unit": "deg", "help": "Launch angle above horizontal."},
            {"name": "initial_height_m", "label": "Initial height", "type": "number", "default": "0", "unit": "m", "help": "Initial height above landing plane."},
            {"name": "gravity_m_s2", "label": "Gravity", "type": "number", "default": "9.80665", "unit": "m/s²", "help": "Gravitational acceleration."},
        ],
    },
    {
        "id": "architecture-floor-area-efficiency", "title": "Architecture: Floor-Area Efficiency", "domain": "Architecture", "family": "Space planning", "description": "Compute net-to-gross area efficiency and net area per occupant.",
        "inputs": [
            {"name": "gross_floor_area_m2", "label": "Gross floor area", "type": "number", "default": "1000", "unit": "m²", "help": "Gross floor area."},
            {"name": "net_usable_area_m2", "label": "Net usable area", "type": "number", "default": "720", "unit": "m²", "help": "Net usable area."},
            {"name": "occupants", "label": "Occupants", "type": "number", "default": "80", "unit": "people", "help": "Planned occupancy count."},
        ],
    },
    {
        "id": "architecture-daylight-aperture", "title": "Architecture: Daylight Aperture", "domain": "Architecture", "family": "Environmental design", "description": "Compute glazing-to-floor ratio and effective aperture proxy.",
        "inputs": [
            {"name": "floor_area_m2", "label": "Floor area", "type": "number", "default": "100", "unit": "m²", "help": "Room or zone floor area."},
            {"name": "glazing_area_m2", "label": "Glazing area", "type": "number", "default": "18", "unit": "m²", "help": "Transparent glazing area."},
            {"name": "visible_transmittance", "label": "Visible transmittance", "type": "number", "default": "0.6", "unit": "0–1", "help": "Glazing visible transmittance."},
        ],
    },
    {
        "id": "infrastructure-peak-water-demand", "title": "Infrastructure: Peak Water Demand", "domain": "Infrastructure", "family": "Water systems", "description": "Estimate average and peak water demand for planning.",
        "inputs": [
            {"name": "population", "label": "Population", "type": "number", "default": "10000", "unit": "people", "help": "Served population."},
            {"name": "per_capita_L_day", "label": "Per-capita demand", "type": "number", "default": "180", "unit": "L/person/day", "help": "Average demand per person."},
            {"name": "peak_factor", "label": "Peak factor", "type": "number", "default": "2.5", "unit": "factor", "help": "Peak demand multiplier."},
        ],
    },
    {
        "id": "infrastructure-rational-runoff", "title": "Infrastructure: Rational Runoff", "domain": "Infrastructure", "family": "Stormwater", "description": "Estimate peak stormwater runoff using the rational method.",
        "inputs": [
            {"name": "runoff_coefficient", "label": "Runoff coefficient", "type": "number", "default": "0.6", "unit": "0–1", "help": "Composite runoff coefficient."},
            {"name": "rainfall_intensity_mm_hr", "label": "Rainfall intensity", "type": "number", "default": "50", "unit": "mm/hr", "help": "Design rainfall intensity."},
            {"name": "drainage_area_ha", "label": "Drainage area", "type": "number", "default": "2", "unit": "ha", "help": "Drainage catchment area."},
        ],
    },
    {
        "id": "pattern-recognition-cosine-similarity", "title": "Pattern Recognition: Cosine Similarity", "domain": "Pattern recognition", "family": "Math, art, and music patterns", "description": "Compare two numeric feature vectors using cosine similarity.",
        "inputs": [
            {"name": "pattern_a", "label": "Pattern A", "type": "text", "default": "1,0,1,1,0,1", "unit": "features", "help": "Comma-separated feature vector."},
            {"name": "pattern_b", "label": "Pattern B", "type": "text", "default": "1,1,1,0,0,1", "unit": "features", "help": "Comma-separated feature vector."},
        ],
    },
    {
        "id": "pattern-recognition-harmonic-centroid", "title": "Pattern Recognition: Harmonic Centroid", "domain": "Pattern recognition", "family": "Music/math pattern", "description": "Compute a harmonic centroid from base frequency and harmonic amplitudes.",
        "inputs": [
            {"name": "base_frequency_hz", "label": "Base frequency", "type": "number", "default": "220", "unit": "Hz", "help": "Fundamental frequency."},
            {"name": "harmonic_amplitudes", "label": "Harmonic amplitudes", "type": "text", "default": "1,0.5,0.25,0.125,0.08", "unit": "series", "help": "Comma-separated harmonic amplitudes."},
        ],
    },
    {
        "id": "astrophysics-kepler-orbit", "title": "Astrophysics: Kepler Orbit", "domain": "Astrophysics", "family": "Orbital mechanics", "description": "Compute orbital period from semi-major axis and central mass in solar-system units.",
        "inputs": [
            {"name": "semi_major_axis_AU", "label": "Semi-major axis", "type": "number", "default": "1", "unit": "AU", "help": "Orbital semi-major axis."},
            {"name": "central_mass_solar", "label": "Central mass", "type": "number", "default": "1", "unit": "M☉", "help": "Central mass in solar masses."},
        ],
    },
    {
        "id": "astrophysics-luminosity-flux", "title": "Astrophysics: Luminosity and Flux", "domain": "Astrophysics", "family": "Radiative astronomy", "description": "Compute observed flux from luminosity and distance with the inverse-square law.",
        "inputs": [
            {"name": "luminosity_solar", "label": "Luminosity", "type": "number", "default": "1", "unit": "L☉", "help": "Source luminosity in solar luminosities."},
            {"name": "distance_parsec", "label": "Distance", "type": "number", "default": "10", "unit": "pc", "help": "Distance to source."},
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
    "econometrics-simple-ols": calc_econometrics_ols,
    "econometrics-difference-in-differences": calc_econometrics_difference_in_differences,
    "psychometrics-cronbach-alpha": calc_psychometrics_cronbach_alpha,
    "psychometrics-standard-error-measurement": calc_psychometrics_standard_error_measurement,
    "computational-biology-logistic-growth": calc_biology_logistic_growth,
    "computational-biology-michaelis-menten": calc_biology_michaelis_menten,
    "computational-chemistry-arrhenius": calc_chemistry_arrhenius,
    "computational-chemistry-nernst": calc_chemistry_nernst,
    "computational-physics-harmonic-oscillator": calc_physics_harmonic_oscillator,
    "computational-physics-projectile-motion": calc_physics_projectile_motion,
    "architecture-floor-area-efficiency": calc_architecture_floor_area_efficiency,
    "architecture-daylight-aperture": calc_architecture_daylight_aperture,
    "infrastructure-peak-water-demand": calc_infrastructure_peak_water_demand,
    "infrastructure-rational-runoff": calc_infrastructure_rational_runoff,
    "pattern-recognition-cosine-similarity": calc_pattern_cosine_similarity,
    "pattern-recognition-harmonic-centroid": calc_pattern_harmonic_centroid,
    "astrophysics-kepler-orbit": calc_astrophysics_kepler_orbit,
    "astrophysics-luminosity-flux": calc_astrophysics_luminosity_flux,
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
