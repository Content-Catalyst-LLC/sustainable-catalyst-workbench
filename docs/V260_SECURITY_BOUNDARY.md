# Workbench v2.6.0 Security and Responsible-Use Boundary

- Browser calculations and project generation remain local unless a user deliberately calls a configured backend.
- The optional Go Runner binds only to `127.0.0.1:8787`.
- Protected runner routes require one-time browser pairing and an origin-bound bearer token.
- Native execution is disabled unless the runner is explicitly started with `--enable-native-exec`.
- Every execution request requires explicit consent and an allowlisted language.
- Source files run in temporary working directories and are removed after execution.
- Source requests are limited to 200 KiB and output is limited to 256 KiB.
- Runtime execution is time-limited and inherits only a minimal environment.
- The runner does not provide a general command or arbitrary shell endpoint.
- This is not a hostile-code sandbox. Execute only code you understand and trust on your own machine.
- Cross-language agreement does not prove model validity, correct units, stable numerics, safe engineering design, or standards compliance.
- Users must review dependencies, licenses, compiler flags, runtime versions, ABI assumptions, data types, overflow, precision, tolerances, units, platform behavior, and test coverage.
