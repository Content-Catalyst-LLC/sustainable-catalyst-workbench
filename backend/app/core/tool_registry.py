from __future__ import annotations

TOOLS = [
    {
        "id": "ask-workbench",
        "title": "Ask the Workbench",
        "domain": "Research Library",
        "type": "assistant",
        "description": "A compact site-scoped assistant that routes questions to calculators, analytics, research pathways, or interpretive frameworks.",
        "featured": True,
        "schema": {"fields": [{"name": "question", "label": "Question", "type": "textarea", "placeholder": "Ask anything connected to Sustainable Catalyst."}]},
    },
    {
        "id": "linear-system-solver",
        "title": "Linear System Solver",
        "domain": "Mathematical Modeling",
        "type": "calculator",
        "description": "Solve Ax=b, estimate rank, determinant, condition number, residual, and stability warnings.",
        "featured": True,
        "schema": {"fields": [
            {"name": "A", "label": "Matrix A", "type": "textarea", "placeholder": "[[2,1],[1,3]]"},
            {"name": "b", "label": "Vector b", "type": "text", "placeholder": "[1,2]"}
        ]},
    },
    {
        "id": "calculus-function-analyzer",
        "title": "Calculus Function Analyzer",
        "domain": "Mathematical Modeling",
        "type": "calculator",
        "description": "Differentiate, integrate, locate critical points, and graph a symbolic function.",
        "featured": True,
        "schema": {"fields": [
            {"name": "function", "label": "Function f(x)", "type": "text", "placeholder": "x**3 - 3*x + 1"},
            {"name": "x_min", "label": "Graph x-min", "type": "number", "placeholder": "-5"},
            {"name": "x_max", "label": "Graph x-max", "type": "number", "placeholder": "5"}
        ]},
    },
    {
        "id": "statistics-analyzer",
        "title": "Statistics Analyzer",
        "domain": "Statistics for Systems Modeling",
        "type": "analytics",
        "description": "Summarize data, compute distribution diagnostics, confidence intervals, and detailed SVG graphs.",
        "featured": True,
        "schema": {"fields": [
            {"name": "data", "label": "Data values", "type": "textarea", "placeholder": "12, 15, 18, 19, 21, 25, 29"}
        ]},
    },
    {
        "id": "regression-analyzer",
        "title": "Regression Analyzer",
        "domain": "Statistics and Economics",
        "type": "analytics",
        "description": "Fit a simple linear model with diagnostics and a fitted-line graph.",
        "featured": True,
        "schema": {"fields": [
            {"name": "x", "label": "X values", "type": "textarea", "placeholder": "1,2,3,4,5"},
            {"name": "y", "label": "Y values", "type": "textarea", "placeholder": "2,4,5,4,6"}
        ]},
    },
    {
        "id": "probability-distribution-calculator",
        "title": "Probability Distribution Calculator",
        "domain": "Probability for Systems Modeling",
        "type": "calculator",
        "description": "Analyze normal, binomial, and Poisson probabilities with distribution graphs.",
        "featured": True,
        "schema": {"fields": [
            {"name": "distribution", "label": "Distribution", "type": "select", "options": ["normal", "binomial", "poisson"]},
            {"name": "params", "label": "Parameters", "type": "text", "placeholder": "normal: mean=0,sd=1 | binomial: n=20,p=0.4 | poisson: lambda=3"},
            {"name": "value", "label": "Value / threshold", "type": "number", "placeholder": "1"}
        ]},
    },
    {
        "id": "differential-equation-simulator",
        "title": "Differential Equation Simulator",
        "domain": "Differential Equations for Systems Modeling",
        "type": "simulation",
        "description": "Simulate logistic growth and first-order system dynamics with plotted trajectories. Julia bridge available when installed.",
        "featured": True,
        "schema": {"fields": [
            {"name": "model", "label": "Model", "type": "select", "options": ["logistic", "exponential_decay"]},
            {"name": "initial", "label": "Initial value", "type": "number", "placeholder": "10"},
            {"name": "rate", "label": "Rate", "type": "number", "placeholder": "0.25"},
            {"name": "carrying_capacity", "label": "Carrying capacity", "type": "number", "placeholder": "100"},
            {"name": "t_end", "label": "Time horizon", "type": "number", "placeholder": "30"}
        ]},
    },
    {
        "id": "economics-calculator",
        "title": "Economics Calculator",
        "domain": "Economic Systems",
        "type": "calculator",
        "description": "Calculate NPV, elasticity, break-even, and supply-demand equilibrium with graphs where relevant.",
        "featured": True,
        "schema": {"fields": [
            {"name": "mode", "label": "Mode", "type": "select", "options": ["npv", "elasticity", "supply_demand", "break_even"]},
            {"name": "inputs", "label": "Inputs", "type": "textarea", "placeholder": "npv: rate=0.08; cashflows=-1000,300,400,500\nelasticity: p1=10,p2=12,q1=100,q2=85\nsupply_demand: demand_intercept=100,demand_slope=2,supply_intercept=20,supply_slope=1"}
        ]},
    },
    {
        "id": "energy-systems-calculator",
        "title": "Energy Systems Calculator",
        "domain": "Energy Systems",
        "type": "calculator",
        "description": "Estimate electricity cost, emissions, solar PV generation, and battery autonomy.",
        "featured": True,
        "schema": {"fields": [
            {"name": "mode", "label": "Mode", "type": "select", "options": ["electricity_cost_emissions", "solar_pv", "battery_autonomy"]},
            {"name": "inputs", "label": "Inputs", "type": "textarea", "placeholder": "electricity_cost_emissions: kwh=500,rate=0.16,kgco2_per_kwh=0.4\nsolar_pv: kw=5,sun_hours=4.2,performance_ratio=0.8\nbattery_autonomy: battery_kwh=13.5,load_kw=1.2,depth_of_discharge=0.9"}
        ]},
    },
    {
        "id": "psychology-scale-analyzer",
        "title": "Psychology Scale Analyzer",
        "domain": "Psychology",
        "type": "analytics",
        "description": "Analyze Likert-style responses, subscales, summary scores, and Cronbach alpha when item-level data are provided. R bridge available when installed.",
        "featured": True,
        "schema": {"fields": [
            {"name": "responses", "label": "Responses", "type": "textarea", "placeholder": "Rows of comma-separated item scores, e.g.\n4,5,4,3\n3,4,4,2\n5,5,4,4"},
            {"name": "scale_min", "label": "Scale minimum", "type": "number", "placeholder": "1"},
            {"name": "scale_max", "label": "Scale maximum", "type": "number", "placeholder": "5"}
        ]},
    },
    {
        "id": "scientific-calculator",
        "title": "Scientific Calculator",
        "domain": "Natural Science",
        "type": "calculator",
        "description": "Open science calculator for physics, chemistry, materials, and environmental science examples.",
        "featured": True,
        "schema": {"fields": [
            {"name": "mode", "label": "Mode", "type": "select", "options": ["ideal_gas", "kinetic_energy", "stress_strain", "dilution"]},
            {"name": "inputs", "label": "Inputs", "type": "textarea", "placeholder": "ideal_gas: n=1,R=8.314,T=298,V=0.024\nkinetic_energy: mass=2,velocity=10\nstress_strain: force=1000,area=0.01,delta_length=0.002,length=1"}
        ]},
    },
    {
        "id": "sustainability-resilience-scorecard",
        "title": "Sustainability & Resilience Scorecard",
        "domain": "Sustainable Systems",
        "type": "diagnostic",
        "description": "Weighted diagnostic for exposure, sensitivity, adaptive capacity, governance, equity, and recovery capacity.",
        "featured": True,
        "schema": {"fields": [
            {"name": "scores", "label": "Scores", "type": "textarea", "placeholder": "exposure=4,sensitivity=3,adaptive_capacity=2,governance=3,equity=2,recovery=4"}
        ]},
    },
    {
        "id": "ai-governance-audit",
        "title": "AI Governance Audit",
        "domain": "Technology & Systems Intelligence",
        "type": "audit",
        "description": "Structured audit for model purpose, data quality, proxy variables, human oversight, contestability, and documentation.",
        "featured": True,
        "schema": {"fields": [
            {"name": "system_description", "label": "AI system description", "type": "textarea", "placeholder": "Describe the AI system, use case, data, decision impact, and oversight model."},
            {"name": "risk_factors", "label": "Risk factors", "type": "textarea", "placeholder": "high impact, personal data, automation, vulnerable users, opaque model..."}
        ]},
    },
    {
        "id": "haskell-rule-checker",
        "title": "Haskell Rule Checker",
        "domain": "Algorithms & Computational Reasoning",
        "type": "formal-logic",
        "description": "Validate simple rule consistency using a Haskell bridge when available, with a Python fallback.",
        "featured": False,
        "schema": {"fields": [{"name": "rules", "label": "Rules", "type": "textarea", "placeholder": "must:scope_gate\nmust:not_general_chat\nconflict:allow_all_topics"}]},
    },

    {
        "id": "visual-analytics-studio",
        "title": "Visual Analytics Studio",
        "domain": "Data Systems & Analytics",
        "type": "visualization",
        "description": "Create publication-ready SVG bar, line, scatter, histogram, and box-plot visualizations from data using the Python analytics backend.",
        "featured": True,
        "schema": {"fields": [
            {"name": "chart_type", "label": "Chart type", "type": "select", "options": ["bar", "line", "scatter", "histogram", "box"]},
            {"name": "title", "label": "Chart title", "type": "text", "placeholder": "Energy demand scenario"},
            {"name": "x_values", "label": "X values", "type": "textarea", "placeholder": "1,2,3,4,5 or Jan,Feb,Mar,Apr"},
            {"name": "y_values", "label": "Y values", "type": "textarea", "placeholder": "10,14,19,25,31"},
            {"name": "labels", "label": "Category labels", "type": "textarea", "placeholder": "Energy, Economics, Psychology, Governance"},
            {"name": "values", "label": "Values", "type": "textarea", "placeholder": "42, 38, 35, 31"},
            {"name": "x_label", "label": "X-axis label", "type": "text", "placeholder": "Scenario or time"},
            {"name": "y_label", "label": "Y-axis label", "type": "text", "placeholder": "Value"}
        ]},
    },
    {
        "id": "qualitative-interpretation-matrix",
        "title": "Qualitative Interpretation Matrix",
        "domain": "Meaning and Humanities",
        "type": "interpretive-framework",
        "description": "Structured qualitative analysis for narrative, symbolism, philosophy, religion, culture, and meaning.",
        "featured": True,
        "schema": {"fields": [
            {"name": "subject", "label": "Subject", "type": "text", "placeholder": "ritual, myth, institution, symbol, text, policy, design"},
            {"name": "context", "label": "Context", "type": "textarea", "placeholder": "Describe the material to interpret."}
        ]},
    },
]


def list_tools(topic: str = "", domain: str = "", limit: int = 36):
    t = (topic or "").replace("-", " ").lower()
    d = (domain or "").lower()
    rows = TOOLS
    if d:
        rows = [x for x in rows if d in x["domain"].lower()]
    if t:
        rows = [x for x in rows if t in (x["id"] + " " + x["title"] + " " + x["domain"] + " " + x["description"]).lower()]
    if not rows:
        rows = [x for x in TOOLS if x.get("featured")]
    return rows[: max(1, min(int(limit or 36), 100))]


def get_tool(tool_id: str):
    for t in TOOLS:
        if t["id"] == tool_id:
            return t
    return None
