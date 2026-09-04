# Workbench v5.6.0 Security Boundary

- Mathematical expressions are parsed through `RestrictedSympyParser`.
- No Python `eval()` or `exec()` is used by the v5.6 numerical API.
- No uploaded Python functions or arbitrary callables are accepted.
- Numerical loops, samples, states, matrix dimensions, variables, iterations, and parameter counts are bounded.
- ODE methods are limited to an approved SciPy method allow-list.
- Optimization is bound-constrained and limited to an approved solver path.
- Remote shell access and arbitrary command execution are not exposed.
- Device programming and physical execution remain outside this numerical layer.
