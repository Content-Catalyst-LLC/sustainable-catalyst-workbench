# Workbench v2.4.0 Security and Safety Boundary

The local Workbench Runner listens only on `127.0.0.1:8787` and requires browser-origin pairing before protected routes are available.

## Enforced boundaries

- Loopback-only listener
- Six-digit pairing code
- Origin-bound bearer tokens
- Explicit consent for each local instrumentation task
- Native tasks disabled unless `--enable-native-exec` is supplied
- Fixed allowlist of tool/version and read-only discovery commands
- No arbitrary shell endpoint
- Request and output size limits
- Command timeouts
- Minimal inherited environment

## Measurement safety

Tool discovery or successful command execution does not establish that an instrument, sensor, probe, ADC, DAQ, SDR, audio interface, serial device, or wiring arrangement is safe or suitable. Users must verify:

- input voltage and current limits
- galvanic isolation and grounding
- differential and common-mode ratings
- probe attenuation and category ratings
- anti-alias filtering and sample-clock accuracy
- calibration state and traceability
- uncertainty contributors and environmental effects
- data integrity, timestamp source, and channel synchronization
- applicable laboratory, electrical, product, and occupational-safety requirements
