# v5.6.0 Numerical Methods & Scientific Computing

v5.6.0 adds a governed numerical layer above the existing restricted mathematics parser.

## Numerical object chain

`expression / matrix / dataset → method → tolerance / bounds → computation → diagnostics → canonical numerical object`

## Routes

- `GET /v560/status`
- `POST /v560/root`
- `POST /v560/integrate`
- `POST /v560/differentiate`
- `POST /v560/interpolate`
- `POST /v560/ode`
- `POST /v560/linear-algebra`
- `POST /v560/optimize`

## Supported families

### Root finding
Brent, bisection, secant, and Newton methods with convergence, iteration, function-call, and residual reporting.

### Numerical calculus
Adaptive quadrature, composite Simpson/trapezoid integration, and high-order central finite-difference derivatives.

### Interpolation
Linear, cubic spline, and PCHIP interpolation with canonical source points and sampled output curves.

### ODEs
Initial-value systems up to eight states using RK45, DOP853, Radau, or BDF with explicit tolerances and function-evaluation diagnostics.

### Linear algebra
Solve, eigen analysis, SVD, least squares, and inverse operations on bounded matrices up to 16 × 16.

### Optimization
Bounded multivariable minimization/maximization for up to six variables using L-BFGS-B.

## Reproducibility

Every result carries the source payload, method, runtime version, diagnostics, restrictions, and a SHA-256 content hash. Numerical results are not silently presented as exact symbolic identities.
