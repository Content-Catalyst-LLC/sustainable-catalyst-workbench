# Workbench v5.8.0 — Electronics & Embedded Systems Studio

v5.8.0 extends the Workbench computational line from signal/control mathematics into bounded electronics and embedded-system planning.

## Capabilities

- series and parallel resistor-network analysis with current, voltage, and power breakdowns;
- series/parallel RLC impedance, phase, resonant-frequency, and approximate Q analysis;
- ADC/DAC quantization, code/voltage conversion, clipping, LSB, and quantization-error analysis;
- PWM/timer configuration search across bounded prescaler choices, counter width, frequency error, duty-cycle count, and effective resolution;
- Nyquist/oversampling analysis, sample-count planning, sample interval, ideal ADC SNR, and anti-alias-filter review flags;
- bounded I2C, SPI, and UART transfer-time/throughput planning;
- linear, voltage-divider, and NTC beta sensor transfer models;
- GPIO allocation plans with duplicate-pin prevention and voltage-domain review warnings;
- export-only scaffolds for Arduino, ESP32, Raspberry Pi, PYNQ, Verilog, and VHDL.

## Computational object chain

`circuit/signal requirement → electrical model → timing/interface plan → diagnostics → human review → export-only prototype object`

Every v5.8.0 result is a canonical `sc-workbench-electronics-embedded-object/1.0` record with a SHA-256 content hash and explicit execution-boundary fields.

## WordPress surface

Primary studio shortcode:

`[sc_workbench_electronics_embedded]`

Aliases:

`[sc_workbench_electronics_studio]`
`[sc_workbench_embedded_systems]`
`[sc_workbench_embedded_studio]`
`[sc_workbench_electronics]`

The unified Workbench catalog adds an **Electronics & Embedded Systems** studio. The compact homepage instrument remains compact and inherits the v5.8.0 release identity without adding another tall homepage module.
