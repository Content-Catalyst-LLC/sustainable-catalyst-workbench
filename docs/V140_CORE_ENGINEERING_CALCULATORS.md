# Workbench v1.4.0 — Core Engineering Calculators

Phase 4 adds a core engineering calculator library to the Sustainable Catalyst Workbench. It builds on v1.1 Chalkboard Translator, v1.2 Graph Studio, and v1.3 Engineering Mode output templates.

## New backend endpoints

- `GET /engineering/calculators` — list available core engineering calculators.
- `GET /engineering/calculators/{calculator_id}` — inspect one calculator spec.
- `POST /engineering/calculate` — run a selected engineering calculator.

## New WordPress REST routes

- `/wp-json/sc-workbench/v1/engineering-calculators`
- `/wp-json/sc-workbench/v1/engineering-calculate`

## New shortcode

```text
[sc_workbench_engineering_calculators title="Core Engineering Calculators"]
```

The calculators are also available as a tab inside the main `[sc_workbench]` interface.

## Initial calculator library

- Force, Mass, and Acceleration
- Normal Stress
- Axial Strain
- Factor of Safety
- Beam Deflection
- Ohm's Law and Power
- RC Time Constant and Response
- Conduction Heat Transfer
- Pump Power
- Energy Emissions
- FMEA Risk Priority Number

## Output standard

Each calculator returns a reviewable engineering calculation note with:

- formula
- inputs and units
- computed results
- sensitivity graph where useful
- assumptions
- validation checks
- professional-review warnings
- JSON/PDF-ready export support through the Workbench UI

## Boundary

These calculators are educational and engineering-aware. They are not licensed professional engineering judgment, code compliance, assurance, or stamped calculations.
