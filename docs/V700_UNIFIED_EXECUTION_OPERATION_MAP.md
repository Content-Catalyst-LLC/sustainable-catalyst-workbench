# Workbench v7.0.0 Unified Execution Operation Map

The v7.0 runtime wraps existing bounded specialist engines. It does not replace or bypass them.

| Category | Representative operations | Source layer | Core execution type |
|---|---|---|---|
| Mathematics | `math.compute`, `math.calculus`, `math.solve`, `math.substitute` | v5.1 | `engineering_calculation` |
| Numerical scientific | root, integration, differentiation, interpolation, ODE, linear algebra, optimization | v5.6 | engineering / simulation / optimization |
| Simulation & systems | dynamic simulation, digital twin, state-space system, parameter sweep, Monte Carlo, model validation | v2.5 | simulation / statistical analysis |
| Controls & mechatronics | robot kinematics, PID baseline, actuator sizing, HIL, state-machine validation | v2.3 | engineering / simulation |
| Measurement | instrumentation, acquisition, signal/frequency analysis, calibration, measurement validation | v2.4 | engineering / statistical analysis |
| Signals & controls | spectrum, convolution, filter design, transfer function, state-space, PID, root locus | v5.7 | engineering / simulation |
| Electronics & embedded | resistor/RLC, ADC/DAC, PWM, sampling, bus, sensors, GPIO, prototype scaffold | v5.8 | engineering calculation |
| Digital logic / FPGA | truth table, minimization, Karnaugh, FSM, timing, HDL scaffold, resource estimate, PYNQ overlay | v5.9 | engineering calculation |
| Uncertainty & sensitivity | sampling design, Sobol, Morris, ensemble statistics, exceedance | v6.8 | statistical analysis |
| Predictive | forecast, backtest, calibration | v6.10 | forecasting / statistical analysis |
| Forensic quantitative | trajectory, temporal comparison, uncertainty, hypothesis metrics | v6.11 | forensic reconstruction |
| Energy systems | explicit handoff execution | v6.3 | engineering calculation |

All operations are allow-listed. The operation catalog is available from `GET /execution/runtime/catalog` and includes source release, execution type, output type, input model, and deterministic-execution declaration.

## Platform Core lineage

`POST /integration/core/unified-execution/lineage/plan` is explicitly two-phase:

1. Workbench prepares a Core computation-lineage execution registration request.
2. Platform Core persists it and returns the authoritative Core execution ID.
3. Workbench can then prepare ordered input/parameter/environment/step/output records and an optional unified-session binding using that Core-issued ID.

No endpoint performs automatic Core HTTP dispatch or persistence.
