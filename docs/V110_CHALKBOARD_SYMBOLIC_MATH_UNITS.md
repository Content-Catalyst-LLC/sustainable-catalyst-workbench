# Workbench v1.1.0 — Chalkboard Translator, Symbolic Math, and Units

Phase 1 adds an engineer-aware symbolic math layer to Sustainable Catalyst Workbench.

## What it adds

- A **Chalkboard** tab inside the main `[sc_workbench]` interface.
- A standalone shortcode:

```text
[sc_workbench_chalkboard title="Chalkboard Translator"]
```

- A FastAPI endpoint:

```text
POST /symbolic/analyze
```

- A WordPress REST proxy:

```text
POST /wp-json/sc-workbench/v1/symbolic
```

## Supported Phase 1 actions

- Translate keyboard math to chalkboard-style notation.
- Return LaTeX.
- Return SymPy code.
- Simplify, factor, expand.
- Solve equations for a selected variable.
- Differentiate and integrate single-variable expressions.
- Generate SVG function graphs.
- Parse engineering-style unit assignments when Pint is installed.

## Example inputs

```text
x^2 + 3x - 4
```

```text
y = sin(x) + 0.3sin(3x)
```

```text
F = m*a
m = 12 kg
a = 3.5 m/s^2
```

## Backend dependencies

The backend now includes:

```text
sympy>=1.12,<2
pint>=0.23,<1
```

The existing matplotlib SVG graph export layer is reused for Phase 1 graph output.

## Engineering boundary

This feature is intended for education, symbolic exploration, unit-aware checking, graphing, and reviewable calculation notes. It is not a substitute for licensed engineering, architecture, safety-critical, legal, medical, financial, or compliance review.
