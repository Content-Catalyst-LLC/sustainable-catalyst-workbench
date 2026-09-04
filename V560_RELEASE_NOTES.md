# Workbench v5.6.0 — Numerical Methods & Scientific Computing

Workbench v5.6.0 extends the mathematics line from symbolic computation, advanced graphing, and dynamic geometry into bounded scientific numerical computation.

## Highlights

- Numerical root finding with Brent, bisection, secant, and Newton methods.
- Adaptive quadrature plus composite Simpson and trapezoid integration.
- First- and second-derivative finite-difference estimates with symbolic cross-check metadata.
- Linear, cubic-spline, and shape-preserving PCHIP interpolation.
- Initial-value ODE solving with RK45, DOP853, Radau, and BDF methods.
- Linear-system solving, eigen analysis, SVD, least squares, and matrix inversion.
- Bounded multivariable optimization with L-BFGS-B.
- Canonical content-hashed numerical objects containing methods, tolerances, diagnostics, and source payloads.
- WordPress studio: `[sc_workbench_numerical_methods]` with aliases `[sc_workbench_scientific_computing]`, `[sc_workbench_numerical_studio]`, and `[sc_workbench_numerical]`.
- Workbench studio router adds a dedicated Numerical Computing entry.
- Workbench Settings now certifies the `/v560/status` capability.
- Public Workbench experience advances visible release identity to v5.6.0 and adds Numerical Computing to the advanced navigator without enlarging the compact homepage instrument.

## Runtime

This is a backend + WordPress release. Deploy the v5.6.0 backend to Contabo after pushing GitHub, then upload the v5.6.0 WordPress plugin.

## Security boundary

User expressions remain inside the restricted v5.1 AST → SymPy parser. Numerical methods accept bounded structured inputs only. Arbitrary Python `eval` / `exec`, uploaded callables, remote shell access, arbitrary commands, automatic device execution, and unattended hardware programming remain unauthorized.
