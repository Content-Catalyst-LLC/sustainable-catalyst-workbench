# Workbench v1.3.0 — Engineering Mode Output Template

Phase 3 adds an engineering-oriented output layer to the Sustainable Catalyst Workbench.

Engineering Mode does not replace licensed engineering judgment. It turns symbolic formulas, variables, and unit assignments into a reviewable calculation-note structure suitable for educational analysis, early-stage engineering reasoning, and article/tool workflows.

## New user-facing shortcode

```text
[sc_workbench_engineering_mode title="Engineering Mode"]
```

The main Workbench shortcode also includes a new **Engineering Mode** tab:

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="compact"]
```

## New backend endpoint

```http
POST /engineering/analyze
```

Example payload:

```json
{
  "input": "F = m*a\nm = 12 kg\na = 3.5 m/s^2",
  "variable": "",
  "include_solve": false
}
```

## New WordPress REST proxy

```http
POST /wp-json/sc-workbench/v1/engineering
```

## What Engineering Mode returns

Engineering Mode produces:

- keyboard input
- chalkboard preview
- LaTeX
- SymPy expression
- inferred engineering domain
- formula summary
- variables table
- unit-aware computation when possible
- assumptions
- validation checks
- sensitivity template
- professional-review warnings
- export-ready calculation note sections

## Example inputs

```text
F = m*a
m = 12 kg
a = 3.5 m/s^2
```

```text
sigma = F/A
F = 1000 N
A = 0.02 m^2
```

```text
P = V*I
V = 120 V
I = 8 A
```

## Engineering template sections

1. Problem / relationship
2. Inputs and units
3. Formula and symbolic form
4. Computation result
5. Assumptions
6. Validation checks
7. Limitations and next review

## Boundary

Engineering Mode is educational, analytical, and decision-support oriented. It is not a stamped calculation, code-compliant engineering report, safety certification, or substitute for licensed professional review.
