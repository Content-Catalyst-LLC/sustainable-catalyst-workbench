# Sustainable Catalyst Prototyping Workbench v2.5.0

## Simulation, Digital Twin, and Systems Modeling Studio

Version 2.5.0 adds six connected, browser-local modeling environments and matching FastAPI calculation routes.

### New studios

- Dynamic Simulation Studio for first-order processes, logistic growth, and damped oscillators
- Digital Twin Studio with measured-stream comparison and bounded parameter calibration
- Systems Modeling Studio for coupled linear state-space models
- Scenario Sweep and Sensitivity Studio
- Seeded Monte Carlo and Uncertainty Studio
- Model Validation and Twin Calibration Studio

### Numerical and validation capabilities

- Explicit Euler and fourth-order Runge–Kutta integration
- Numerical-step limits and divergence detection
- Matrix and vector dimension checks
- Gershgorin stability-review bounds for linear systems
- RMSE, MAE, bias, MAPE, R², and residual-trend records
- Parameter sweeps with sensitivity and nonlinearity flags
- Normal, uniform, and triangular uncertainty distributions
- P05, median, P95, threshold-exceedance, and input-sensitivity summaries
- Browser-local JSON exports with versioned schemas and timestamps

### Local runner

The v2.5.0 runner adds paired, loopback-only discovery for Python, Jupyter, IPython, R, Julia, Octave, OpenModelica, and Gnuplot. Native tasks remain allowlisted and require explicit consent. No arbitrary shell route is added.

### Compatibility

All v2.0.0–v2.4.0 shortcodes, browser-storage namespaces, FastAPI routes, runner protections, and saved project records are preserved.
