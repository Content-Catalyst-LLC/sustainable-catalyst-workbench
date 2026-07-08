from __future__ import annotations
import math, shutil, subprocess, tempfile, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sympy as sp
from scipy import stats, optimize, integrate

from .utils import parse_number_list, parse_matrix, parse_kv, parse_rows, svg_from_figure, safe_float


def result(title, summary, values=None, warnings=None, graphs=None, method=None, engine="python"):
    return {
        "ok": True,
        "title": title,
        "summary": summary,
        "engine": engine,
        "method": method or [],
        "values": values or {},
        "warnings": warnings or [],
        "graphs": graphs or [],
    }


def linear_system_solver(inputs):
    A = parse_matrix(inputs.get("A", "[[2,1],[1,3]]"))
    b = np.array(parse_number_list(inputs.get("b", "[1,2]")), dtype=float)
    if b.ndim != 1 or A.shape[0] != b.shape[0]:
        raise ValueError("A rows must match vector b length.")
    rank = int(np.linalg.matrix_rank(A))
    cond = float(np.linalg.cond(A)) if A.shape[0] == A.shape[1] else None
    det = float(np.linalg.det(A)) if A.shape[0] == A.shape[1] else None
    warnings = []
    if cond and cond > 1e8:
        warnings.append("The matrix is ill-conditioned; small input changes may cause large solution changes.")
    if A.shape[0] == A.shape[1] and abs(det or 0) < 1e-10:
        warnings.append("The determinant is near zero; the system may be singular or nearly singular.")
    try:
        x = np.linalg.solve(A, b) if A.shape[0] == A.shape[1] and rank == A.shape[1] else np.linalg.lstsq(A, b, rcond=None)[0]
    except np.linalg.LinAlgError:
        x = np.linalg.lstsq(A, b, rcond=None)[0]
    residual = A @ x - b
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(residual)), residual)
    ax.axhline(0, linewidth=1)
    ax.set_title("Residual by equation")
    ax.set_xlabel("Equation index")
    ax.set_ylabel("Ax - b")
    graphs = [{"title": "Residual diagnostics", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result(
        "Linear System Solver",
        "Computed a direct or least-squares solution with rank, conditioning, and residual diagnostics.",
        {"solution": x.tolist(), "rank": rank, "determinant": det, "condition_number": cond, "residual_norm": float(np.linalg.norm(residual))},
        warnings,
        graphs,
        ["Parse A and b", "Estimate rank and conditioning", "Solve directly or by least squares", "Compute residual"],
    )


def calculus_function_analyzer(inputs):
    expr_text = inputs.get("function") or "x**3 - 3*x + 1"
    x = sp.symbols("x")
    expr = sp.sympify(expr_text)
    derivative = sp.diff(expr, x)
    integral = sp.integrate(expr, x)
    x_min = safe_float(inputs.get("x_min"), -5)
    x_max = safe_float(inputs.get("x_max"), 5)
    xs = np.linspace(x_min, x_max, 400)
    f = sp.lambdify(x, expr, "numpy")
    d = sp.lambdify(x, derivative, "numpy")
    ys = np.array(f(xs), dtype=float)
    dys = np.array(d(xs), dtype=float)
    finite = np.isfinite(ys)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(xs[finite], ys[finite], label="f(x)")
    ax.plot(xs[np.isfinite(dys)], dys[np.isfinite(dys)], linestyle="--", label="f'(x)")
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)
    ax.set_title("Function and derivative")
    ax.set_xlabel("x")
    ax.legend()
    graphs = [{"title": "Function behavior", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    critical = []
    try:
        critical = [float(v) for v in sp.nroots(derivative) if abs(float(sp.im(v))) < 1e-8]
    except Exception:
        pass
    return result(
        "Calculus Function Analyzer",
        "Computed symbolic derivative, indefinite integral, approximate critical points, and a behavior graph.",
        {"function": str(expr), "derivative": str(derivative), "indefinite_integral": str(integral), "critical_points_estimate": critical[:10]},
        [], graphs, ["Symbolically parse f(x)", "Differentiate and integrate", "Graph f and f'", "Estimate critical points"],
    )


def statistics_analyzer(inputs):
    data = np.array(parse_number_list(inputs.get("data", "12,15,18,19,21,25,29")), dtype=float)
    if data.size < 2:
        raise ValueError("Enter at least two values.")
    mean = float(np.mean(data)); median = float(np.median(data)); sd = float(np.std(data, ddof=1))
    se = sd / math.sqrt(data.size)
    ci = stats.t.interval(0.95, data.size - 1, loc=mean, scale=se) if data.size > 1 else (mean, mean)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.hist(data, bins="auto", alpha=0.85, edgecolor="black")
    ax.axvline(mean, linewidth=2, label="mean")
    ax.axvline(median, linewidth=2, linestyle="--", label="median")
    ax.set_title("Distribution summary")
    ax.set_xlabel("Value")
    ax.set_ylabel("Frequency")
    ax.legend()
    graphs = [{"title": "Distribution summary", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result("Statistics Analyzer", "Computed descriptive statistics and a 95% confidence interval for the mean.",
        {"n": int(data.size), "mean": mean, "median": median, "standard_deviation": sd, "min": float(np.min(data)), "max": float(np.max(data)), "ci95_mean": [float(ci[0]), float(ci[1])]}, [], graphs,
        ["Parse sample", "Compute descriptive statistics", "Estimate confidence interval", "Draw distribution graph"], engine="python/scipy")


def regression_analyzer(inputs):
    x = np.array(parse_number_list(inputs.get("x", "1,2,3,4,5")), dtype=float)
    y = np.array(parse_number_list(inputs.get("y", "2,4,5,4,6")), dtype=float)
    if x.size != y.size or x.size < 2:
        raise ValueError("X and Y must have the same length with at least two points.")
    slope, intercept, r, p, se = stats.linregress(x, y)
    xs = np.linspace(float(np.min(x)), float(np.max(x)), 200)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.scatter(x, y, label="data")
    ax.plot(xs, intercept + slope * xs, label="fit")
    ax.set_title("Linear regression fit")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    graphs = [{"title": "Regression fit", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result("Regression Analyzer", "Fit a simple linear model and returned slope, intercept, r-squared, p-value, and standard error.",
        {"slope": float(slope), "intercept": float(intercept), "r_squared": float(r*r), "p_value": float(p), "slope_standard_error": float(se)}, [], graphs,
        ["Parse paired values", "Fit ordinary least squares line", "Compute diagnostics", "Graph observed values and fitted line"], engine="python/scipy")


def probability_distribution_calculator(inputs):
    dist = (inputs.get("distribution") or "normal").lower()
    params = parse_kv(inputs.get("params") or "mean=0;sd=1")
    value = safe_float(inputs.get("value"), 1)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    values = {}
    if dist == "binomial":
        n = int(params.get("n", 20)); p = float(params.get("p", 0.4))
        xs = np.arange(0, n+1); pmf = stats.binom.pmf(xs, n, p)
        ax.bar(xs, pmf); values = {"pmf_at_value": float(stats.binom.pmf(int(value), n, p)), "cdf_at_value": float(stats.binom.cdf(int(value), n, p)), "mean": n*p, "variance": n*p*(1-p)}
    elif dist == "poisson":
        lam = float(params.get("lambda", params.get("lam", 3)))
        xs = np.arange(0, max(12, int(lam*4)+1)); pmf = stats.poisson.pmf(xs, lam)
        ax.bar(xs, pmf); values = {"pmf_at_value": float(stats.poisson.pmf(int(value), lam)), "cdf_at_value": float(stats.poisson.cdf(int(value), lam)), "mean": lam, "variance": lam}
    else:
        mean = float(params.get("mean", 0)); sd = float(params.get("sd", 1))
        xs = np.linspace(mean-4*sd, mean+4*sd, 400); pdf = stats.norm.pdf(xs, mean, sd)
        ax.plot(xs, pdf); ax.axvline(value, linestyle="--")
        values = {"pdf_at_value": float(stats.norm.pdf(value, mean, sd)), "cdf_at_value": float(stats.norm.cdf(value, mean, sd)), "upper_tail": float(1-stats.norm.cdf(value, mean, sd)), "mean": mean, "sd": sd}
    ax.set_title(f"{dist.title()} distribution")
    graphs = [{"title": "Probability distribution", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result("Probability Distribution Calculator", "Computed distribution probability values and rendered the distribution shape.", values, [], graphs, engine="python/scipy")


def differential_equation_simulator(inputs):
    model = inputs.get("model") or "logistic"
    initial = safe_float(inputs.get("initial"), 10)
    rate = safe_float(inputs.get("rate"), 0.25)
    K = safe_float(inputs.get("carrying_capacity"), 100)
    t_end = safe_float(inputs.get("t_end"), 30)
    t = np.linspace(0, t_end, 300)
    if model == "exponential_decay":
        y = initial * np.exp(-rate * t)
    else:
        y = K / (1 + ((K - initial) / max(initial, 1e-9)) * np.exp(-rate * t))
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(t, y)
    ax.set_title("System trajectory")
    ax.set_xlabel("time")
    ax.set_ylabel("state")
    graphs = [{"title": "Differential equation trajectory", "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result("Differential Equation Simulator", "Simulated the selected first-order system trajectory. Julia can be used later for larger dynamical systems.",
        {"model": model, "initial": initial, "rate": rate, "carrying_capacity": K, "final_value": float(y[-1])}, [], graphs, engine="python/scipy + optional julia")


def economics_calculator(inputs):
    mode = inputs.get("mode") or "npv"
    kv = parse_kv(inputs.get("inputs") or "rate=0.08; cashflows=-1000,300,400,500")
    values = {}; graphs = []; warnings=[]
    if mode == "elasticity":
        p1,p2,q1,q2 = [float(kv.get(k, 0)) for k in ["p1","p2","q1","q2"]]
        elasticity = ((q2-q1)/((q1+q2)/2)) / ((p2-p1)/((p1+p2)/2))
        values = {"arc_elasticity": float(elasticity), "interpretation": "elastic" if abs(elasticity) > 1 else "inelastic"}
    elif mode == "supply_demand":
        a = float(kv.get("demand_intercept", 100)); b = float(kv.get("demand_slope", 2)); c = float(kv.get("supply_intercept", 20)); d = float(kv.get("supply_slope", 1))
        q_eq = (a-c)/(b+d); p_eq = a-b*q_eq
        q = np.linspace(0, max(q_eq*2, 10), 200)
        fig, ax = plt.subplots(figsize=(7,4.4)); ax.plot(q, a-b*q, label="Demand"); ax.plot(q, c+d*q, label="Supply"); ax.scatter([q_eq],[p_eq]); ax.set_title("Supply and demand equilibrium"); ax.set_xlabel("Quantity"); ax.set_ylabel("Price"); ax.legend(); graphs=[{"title":"Equilibrium graph","svg":svg_from_figure(fig)}]; plt.close(fig)
        values = {"equilibrium_quantity": float(q_eq), "equilibrium_price": float(p_eq)}
    elif mode == "break_even":
        fixed=float(kv.get("fixed_cost", 1000)); price=float(kv.get("price", 25)); variable=float(kv.get("variable_cost", 10))
        units=fixed/(price-variable); values={"break_even_units": float(units), "contribution_margin": float(price-variable)}
    else:
        rate=float(kv.get("rate", 0.08)); cashflows=kv.get("cashflows", [-1000,300,400,500]);
        if not isinstance(cashflows, list): cashflows=[float(cashflows)]
        npv=sum(float(cf)/((1+rate)**i) for i,cf in enumerate(cashflows)); values={"npv": float(npv), "rate": rate, "cashflows": cashflows}
        fig, ax=plt.subplots(figsize=(7,4.4)); ax.bar(range(len(cashflows)), cashflows); ax.axhline(0, linewidth=1); ax.set_title("Cash flows"); ax.set_xlabel("Period"); ax.set_ylabel("Cash flow"); graphs=[{"title":"Cash flow profile","svg":svg_from_figure(fig)}]; plt.close(fig)
    return result("Economics Calculator", f"Ran economics mode: {mode}.", values, warnings, graphs, engine="python/scipy")


def energy_systems_calculator(inputs):
    mode = inputs.get("mode") or "electricity_cost_emissions"
    kv = parse_kv(inputs.get("inputs") or "kwh=500;rate=0.16;kgco2_per_kwh=0.4")
    if mode == "solar_pv":
        kw=float(kv.get("kw",5)); sun=float(kv.get("sun_hours",4.2)); pr=float(kv.get("performance_ratio",0.8)); daily=kw*sun*pr; annual=daily*365
        values={"daily_kwh": daily, "annual_kwh": annual}
        ys=np.array([daily*m for m in [31,28,31,30,31,30,31,31,30,31,30,31]])
        title="Estimated monthly solar generation"
    elif mode == "battery_autonomy":
        battery=float(kv.get("battery_kwh",13.5)); load=float(kv.get("load_kw",1.2)); dod=float(kv.get("depth_of_discharge",0.9)); hours=battery*dod/load
        values={"usable_kwh": battery*dod, "autonomy_hours": hours}; ys=np.array([battery*dod, load, hours]); title="Battery autonomy components"
    else:
        kwh=float(kv.get("kwh",500)); rate=float(kv.get("rate",0.16)); kg=float(kv.get("kgco2_per_kwh",0.4)); values={"cost": kwh*rate, "emissions_kgco2": kwh*kg, "kwh": kwh}; ys=np.array([kwh, kwh*rate, kwh*kg]); title="Energy cost and emissions"
    fig, ax=plt.subplots(figsize=(7,4.4)); ax.bar(range(len(ys)), ys); ax.set_title(title); graphs=[{"title": title, "svg": svg_from_figure(fig)}]; plt.close(fig)
    return result("Energy Systems Calculator", f"Ran energy mode: {mode}.", values, [], graphs, engine="python")


def psychology_scale_analyzer(inputs):
    data = parse_rows(inputs.get("responses", "4,5,4,3\n3,4,4,2\n5,5,4,4"))
    if data.size == 0: raise ValueError("Enter item response rows.")
    item_vars = data.var(axis=0, ddof=1) if data.shape[0] > 1 else np.zeros(data.shape[1])
    total = data.sum(axis=1); total_var = total.var(ddof=1) if data.shape[0] > 1 else 0
    k = data.shape[1]
    alpha = (k/(k-1))*(1 - item_vars.sum()/total_var) if k > 1 and total_var > 0 else None
    fig, ax=plt.subplots(figsize=(7,4.4)); ax.boxplot([data[:,i] for i in range(data.shape[1])]); ax.set_title("Item response distributions"); ax.set_xlabel("Item"); ax.set_ylabel("Score"); graphs=[{"title":"Psychology scale profile","svg":svg_from_figure(fig)}]; plt.close(fig)
    return result("Psychology Scale Analyzer", "Analyzed item-level response data and estimated internal consistency when possible.", {"respondents": int(data.shape[0]), "items": int(data.shape[1]), "mean_total_score": float(total.mean()), "cronbach_alpha": None if alpha is None else float(alpha), "item_means": data.mean(axis=0).tolist()}, [], graphs, engine="python + optional R")


def scientific_calculator(inputs):
    mode=inputs.get("mode") or "ideal_gas"; kv=parse_kv(inputs.get("inputs") or "n=1;R=8.314;T=298;V=0.024")
    if mode == "kinetic_energy":
        m=float(kv.get("mass",1)); v=float(kv.get("velocity",1)); values={"kinetic_energy_joules": 0.5*m*v*v}
    elif mode == "stress_strain":
        F=float(kv.get("force",1000)); A=float(kv.get("area",0.01)); dl=float(kv.get("delta_length",0.002)); L=float(kv.get("length",1)); stress=F/A; strain=dl/L; values={"stress_pa":stress,"strain":strain,"youngs_modulus_estimate_pa":stress/strain if strain else None}
    elif mode == "dilution":
        c1=float(kv.get("c1",1)); v1=float(kv.get("v1",1)); c2=float(kv.get("c2",0.1)); values={"required_final_volume": c1*v1/c2}
    else:
        n=float(kv.get("n",1)); R=float(kv.get("r",kv.get("R",8.314))); T=float(kv.get("t",kv.get("T",298))); V=float(kv.get("v",kv.get("V",0.024))); values={"pressure_pa": n*R*T/V}
    return result("Scientific Calculator", f"Ran scientific mode: {mode}.", values, [], [], engine="python")


def sustainability_resilience_scorecard(inputs):
    kv=parse_kv(inputs.get("scores") or "exposure=4,sensitivity=3,adaptive_capacity=2,governance=3,equity=2,recovery=4")
    if len(kv)==1 and isinstance(next(iter(kv.values())), list):
        vals=next(iter(kv.values()))
    else:
        vals=[float(v) for v in kv.values() if isinstance(v,(float,int))]
    if not vals: vals=[3,3,3,3,3,3]
    score=float(np.mean(vals)); warnings=[]
    if score>=4: warnings.append("High risk or high concern profile; review assumptions and mitigation options.")
    fig, ax=plt.subplots(figsize=(7,4.4)); labels=list(kv.keys()) if len(kv)>1 else [f"factor {i+1}" for i in range(len(vals))]; ax.bar(labels, vals); ax.set_ylim(0,5); ax.set_title("Resilience score profile"); ax.tick_params(axis='x', rotation=30); graphs=[{"title":"Score profile","svg":svg_from_figure(fig)}]; plt.close(fig)
    return result("Sustainability & Resilience Scorecard", "Computed a simple weighted diagnostic profile. Interpret as a structured prompt, not a final assessment.", {"average_score":score,"factors":dict(zip(labels,vals))}, warnings, graphs)


def ai_governance_audit(inputs):
    desc=(inputs.get("system_description") or "").lower(); risks=(inputs.get("risk_factors") or "").lower()
    factors={"high_impact": any(w in desc+risks for w in ["health", "legal", "credit", "employment", "housing", "education"]), "personal_data": "personal" in desc+risks or "sensitive" in desc+risks, "automation": "automatic" in desc+risks or "automated" in desc+risks, "low_transparency": "opaque" in desc+risks or "black box" in desc+risks, "weak_appeal": "appeal" not in desc+risks and "contest" not in desc+risks}
    score=sum(1 for v in factors.values() if v)
    return result("AI Governance Audit", "Produced a preliminary governance risk screen. Use this to identify documentation, oversight, contestability, and data-quality questions.", {"risk_flags": factors, "risk_score_0_to_5": score}, ["Educational screening only; not a legal, compliance, or safety certification."])


def haskell_rule_checker(inputs):
    rules=str(inputs.get("rules") or "").splitlines(); must=[r.split(":",1)[1].strip() for r in rules if r.startswith("must:") and ":" in r]; conflicts=[r.split(":",1)[1].strip() for r in rules if r.startswith("conflict:") and ":" in r]
    violations=[m for m in must if m in conflicts]
    engine="python fallback"
    if shutil.which("runghc"):
        engine="haskell bridge available"
    return result("Haskell Rule Checker", "Checked simple must/conflict rule consistency.", {"must":must,"conflicts":conflicts,"violations":violations,"consistent":not violations}, [], [], engine=engine)


def qualitative_interpretation_matrix(inputs):
    subject=inputs.get("subject") or "subject"; context=inputs.get("context") or ""
    lenses=["structure", "symbol", "institution", "ethics", "system effect", "limits of interpretation"]
    values={l: f"Use the {l} lens to examine {subject}." for l in lenses}
    if context: values["context_note"] = context[:500]
    return result("Qualitative Interpretation Matrix", "Generated a structured interpretive matrix for humanities, meaning, culture, philosophy, religion, narrative, or institutional analysis.", values, ["Interpretive tools support reasoning; they do not produce final or exclusive meanings."])


def _parse_label_list(text: str, fallback_count: int = 0) -> list[str]:
    raw = str(text or "").replace("\n", ",")
    labels = [part.strip() for part in raw.split(",") if part.strip()]
    if not labels and fallback_count:
        labels = [str(i + 1) for i in range(fallback_count)]
    return labels


def _style_visual_axes(ax, title: str = "", x_label: str = "", y_label: str = ""):
    ax.set_title(title or "Visual analytics", fontsize=13, fontweight="bold", pad=12)
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    ax.grid(True, axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def visual_analytics_studio(inputs):
    chart_type = (inputs.get("chart_type") or "line").strip().lower()
    title = inputs.get("title") or "Visual analytics"
    x_label = inputs.get("x_label") or ""
    y_label = inputs.get("y_label") or "Value"
    x_text = inputs.get("x_values") or ""
    y_text = inputs.get("y_values") or ""
    labels_text = inputs.get("labels") or ""
    values_text = inputs.get("values") or ""
    values = parse_number_list(values_text or y_text or "12,18,25,21,30,35")
    y = np.array(parse_number_list(y_text or values_text or "12,18,25,21,30,35"), dtype=float)
    x_numeric = parse_number_list(x_text)
    labels = _parse_label_list(labels_text or x_text, len(y) if y.size else len(values))
    warnings = []
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    if chart_type == "bar":
        vals = np.array(values if values else y, dtype=float)
        if not labels or len(labels) != len(vals):
            labels = [f"Item {i+1}" for i in range(len(vals))]
        ax.bar(labels, vals)
        ax.tick_params(axis="x", rotation=25)
        _style_visual_axes(ax, title, x_label or "Category", y_label)
        values_out = {"chart_type": "bar", "n": int(len(vals)), "min": float(np.min(vals)), "max": float(np.max(vals)), "mean": float(np.mean(vals))}
    elif chart_type == "scatter":
        if not x_numeric:
            x_numeric = list(range(1, len(y) + 1))
        x = np.array(x_numeric, dtype=float)
        if len(x) != len(y):
            raise ValueError("Scatter plots require x_values and y_values with the same length.")
        ax.scatter(x, y)
        if len(x) >= 2:
            slope, intercept, r, p, se = stats.linregress(x, y)
            xs = np.linspace(float(np.min(x)), float(np.max(x)), 200)
            ax.plot(xs, intercept + slope * xs, linestyle="--", linewidth=1.4)
            values_out = {"chart_type": "scatter", "n": int(len(x)), "slope": float(slope), "intercept": float(intercept), "r_squared": float(r*r)}
        else:
            values_out = {"chart_type": "scatter", "n": int(len(x))}
        _style_visual_axes(ax, title, x_label or "X", y_label)
    elif chart_type == "histogram":
        vals = np.array(values if values else y, dtype=float)
        ax.hist(vals, bins="auto", edgecolor="black", alpha=0.86)
        ax.axvline(float(np.mean(vals)), linewidth=1.8, label="mean")
        ax.legend()
        _style_visual_axes(ax, title, x_label or "Value", "Frequency")
        values_out = {"chart_type": "histogram", "n": int(len(vals)), "mean": float(np.mean(vals)), "standard_deviation": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0}
    elif chart_type == "box":
        vals = np.array(values if values else y, dtype=float)
        ax.boxplot(vals, vert=True)
        _style_visual_axes(ax, title, "Distribution", y_label)
        values_out = {"chart_type": "box", "n": int(len(vals)), "median": float(np.median(vals)), "q1": float(np.percentile(vals, 25)), "q3": float(np.percentile(vals, 75))}
    else:
        if y.size == 0:
            y = np.array(values, dtype=float)
        if x_numeric and len(x_numeric) == len(y):
            x = np.array(x_numeric, dtype=float)
            ax.plot(x, y, marker="o")
        else:
            x = np.arange(1, len(y) + 1)
            ax.plot(x, y, marker="o")
            if labels and len(labels) == len(y):
                ax.set_xticks(x)
                ax.set_xticklabels(labels, rotation=25, ha="right")
        _style_visual_axes(ax, title, x_label or "Index", y_label)
        values_out = {"chart_type": "line", "n": int(len(y)), "start": float(y[0]), "end": float(y[-1]), "change": float(y[-1] - y[0])}
    fig.tight_layout()
    graphs = [{"title": title, "svg": svg_from_figure(fig)}]
    plt.close(fig)
    return result("Visual Analytics Studio", "Generated a backend-rendered SVG visualization with summary diagnostics.", values_out, warnings, graphs, ["Parse user data", "Choose chart geometry", "Render SVG with Python/matplotlib", "Return graph and diagnostics"], engine="python/matplotlib")

RUNNERS={
    "linear-system-solver": linear_system_solver,
    "calculus-function-analyzer": calculus_function_analyzer,
    "statistics-analyzer": statistics_analyzer,
    "regression-analyzer": regression_analyzer,
    "probability-distribution-calculator": probability_distribution_calculator,
    "differential-equation-simulator": differential_equation_simulator,
    "economics-calculator": economics_calculator,
    "energy-systems-calculator": energy_systems_calculator,
    "psychology-scale-analyzer": psychology_scale_analyzer,
    "scientific-calculator": scientific_calculator,
    "sustainability-resilience-scorecard": sustainability_resilience_scorecard,
    "ai-governance-audit": ai_governance_audit,
    "haskell-rule-checker": haskell_rule_checker,
    "visual-analytics-studio": visual_analytics_studio,
    "qualitative-interpretation-matrix": qualitative_interpretation_matrix,
}


def run_tool(tool_id: str, inputs: dict):
    if tool_id not in RUNNERS:
        raise ValueError(f"Unknown tool: {tool_id}")
    return RUNNERS[tool_id](inputs or {})
