# Workbench v2.1.0 Security and Responsible-Use Boundary

## Local runner boundary

The Go Runner binds only to `127.0.0.1:8787`. Browser access requires a one-time pairing code and an origin-bound token. The runner does not expose an arbitrary shell endpoint.

`GET /devices` reads local interface metadata visible to the current operating-system user. It does not claim that a device is electrically compatible, calibrated, trusted, or safe.

`POST /device-task` accepts only the following named tasks:

- `raspberry-pi-info`
- `serial-list`
- `i2c-list`
- `gpio-list`
- `arduino-board-list`

The first four tasks use bounded file and interface discovery. `arduino-board-list` invokes only `arduino-cli board list --format json` and requires both explicit browser consent and `--enable-native-exec`.

## TinyML boundary

The browser calculations are inspectable baseline models for validating data shape and deployment logic. They do not provide production model selection, hyperparameter optimization, deep-learning training, model signing, adversarial robustness, or regulatory validation.

Before deployment, validate data provenance, leakage, group and temporal splitting, class balance, target distribution, uncertainty, fairness, calibration, drift, privacy, latency, flash, RAM, energy use, quantization effects, and hardware-in-the-loop performance.

## Hardware boundary

Generated Raspberry Pi code and project records are scaffolds. Confirm wiring, voltage, current, grounding, pull-ups, logic levels, protection, pin assignments, device permissions, operating conditions, sensor calibration, enclosures, electromagnetic compatibility, network exposure, and applicable standards.

Do not use generated outputs without qualified review for medical, legal, financial, industrial-control, environmental-assurance, safety-critical, certification, manufacturing, or public-policy decisions.
