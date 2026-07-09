# Sustainable Catalyst Workbench v1.2.0 — Graph Studio with Parameter Sliders

Workbench v1.2.0 adds Phase 2 of the symbolic interface: **Graph Studio**.

Graph Studio builds on v1.1.0 Chalkboard Translator, symbolic math, and unit-aware engineering notes. It allows visitors to enter a symbolic function, detect non-axis symbols as adjustable parameters, generate an exportable graph, and move sliders to regenerate the graph with updated parameter values.

## Shortcodes

Full standalone Graph Studio page/module:

```text
[sc_workbench_graph_studio title="Graph Studio"]
```

Main Workbench interface with Graph Studio tab:

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="compact"]
```

## Backend endpoint

```http
POST /graph/studio
```

Example payload:

```json
{
  "input": "y = a*sin(b*x)",
  "variable": "x",
  "x_min": -10,
  "x_max": 10,
  "points": 700,
  "parameters": {"a": 1, "b": 1},
  "show_derivative": false
}
```

## WordPress REST proxy

```http
POST /wp-json/sc-workbench/v1/graph
```

The WordPress plugin sanitizes the input and forwards it to the FastAPI backend.

## What Graph Studio supports in v1.2.0

- Explicit symbolic functions such as `y = a*sin(b*x)`.
- Function syntax such as `f(x) = A*exp(-k*x)*sin(omega*x)`.
- Axis variable selection, usually `x`.
- Domain controls: `x_min`, `x_max`, and sample count.
- Parameter detection from non-axis symbols.
- Slider controls for parameters.
- Optional derivative overlay.
- Exportable SVG/PNG graph output through the existing Workbench export controls.
- JSON and PDF-ready report output.

## Intended use

Graph Studio is designed for educational, analytical, and engineering-aware exploration. It is not a substitute for licensed engineering, scientific, legal, financial, medical, safety-critical, assurance, or compliance review.

## Good examples

```text
y = a*sin(b*x)
f(x) = A*exp(-k*x)*sin(omega*x)
y = m*x + b
y = K/(1 + a*exp(-r*x))
y = c*x^2 + b*x + a
```

## Phase 3 candidates

- 3D surface plots.
- Parametric curves.
- Polar plots.
- Vector fields.
- Phase portraits.
- Slope fields.
- Saved presets for article embeds.
- Plotly-powered interactive graph mode.
