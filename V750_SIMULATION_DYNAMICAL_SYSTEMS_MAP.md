# v7.5.0 Simulation & Dynamical Systems Map

| Simulation kind | Underlying bounded engine | Primary diagnostics |
|---|---|---|
| scalar-dynamic | v2.5 dynamic simulation via v7.2 | trajectory, extrema, threshold events, first-order/logistic stability metadata |
| linear-state-space | v2.5 state-space simulation via v7.2 | trajectories, eigenvalues, max real eigenvalue, stability class |
| ode-ivp | v7.4 numerical ODE solver | normalized multi-state trajectory, solver diagnostics, events |
| digital-twin | v2.5 bounded digital-twin calibration | predicted/observed trajectory, RMSE, R² |

Parameter sweeps remain explicit and bounded. Platform Core receives lineage plans only.
