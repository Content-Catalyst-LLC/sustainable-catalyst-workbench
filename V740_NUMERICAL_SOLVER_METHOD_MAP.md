# Workbench v7.4.0 Numerical Solver Method Map

| Problem family | Solver keys | Underlying bounded engine |
|---|---|---|
| Root finding | `root.brentq`, `root.bisection`, `root.secant`, `root.newton` | SciPy scalar root methods + restricted SymPy expression parser |
| Quadrature | `integration.adaptive`, `integration.simpson`, `integration.trapezoid` | SciPy adaptive quadrature / composite rules |
| Differentiation | `differentiation.five-point` | Five-point centered finite differences with symbolic comparison when available |
| Interpolation | `interpolation.linear`, `interpolation.cubic-spline`, `interpolation.pchip` | SciPy interpolation objects |
| ODE / IVP | `ode.rk45`, `ode.dop853`, `ode.radau`, `ode.bdf` | `solve_ivp` bounded initial-value solvers |
| Linear algebra | `linear.solve`, `linear.eigen`, `linear.svd`, `linear.least-squares`, `linear.inverse` | NumPy linear algebra |
| Optimization | `optimization.lbfgsb` | bounded SciPy L-BFGS-B |

All methods execute through the v7.0 unified runtime and v7.2 `workbench.numerical` adapter. v7.4 adds canonical diagnostics and provenance around the underlying method result rather than replacing the specialist engine.
