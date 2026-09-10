# Sustainable Catalyst Workbench v5.8.0

## Electronics & Embedded Systems Studio

v5.8.0 adds a bounded electronics and embedded-system layer on top of the v5.7.0 signals/control foundation.

New backend routes:

- `GET /v580/status`
- `POST /v580/resistor-network`
- `POST /v580/rlc`
- `POST /v580/adc-dac`
- `POST /v580/pwm-timer`
- `POST /v580/sampling`
- `POST /v580/bus-plan`
- `POST /v580/sensor-model`
- `POST /v580/gpio-plan`
- `POST /v580/prototype-scaffold`

New WordPress studio: `[sc_workbench_electronics_embedded]`.

The release preserves all earlier v5.x capabilities and keeps hardware interaction export-only: no serial/GPIO/JTAG access and no automatic device programming.

## Certification

- 430 Python tests passed.
- WordPress/PHP runtime and activation audits passed for v5.8.0 through the active v5.x regression line.
- Browser regression gates passed with no `eval`, `new Function`, `scrollIntoView`, or `window.scrollTo` usage in the v5.8.0 runtime.
- FastAPI route smoke tests passed for status, resistor-network, ADC/DAC, PWM/timer, and export-only prototype scaffolding.
