# Workbench v2.5.0 Security and Responsible-Use Boundary

- Browser calculations remain local unless the user deliberately calls a configured backend.
- Local runner traffic is restricted to `127.0.0.1:8787`.
- Protected runner routes require browser pairing and an origin-bound token.
- Native diagnostic tasks are disabled by default and require `--enable-native-exec` plus explicit consent.
- The runner exposes no arbitrary shell endpoint.
- Simulation and twin outputs are approximations, not certified engineering, safety, medical, financial, environmental, or policy conclusions.
- Users must verify equations, units, numerical stability, time steps, parameter ranges, distributions, calibration data, uncertainty assumptions, and boundary conditions.
- Digital-twin calibration is deliberately bounded and transparent; it is not automated control authorization.
