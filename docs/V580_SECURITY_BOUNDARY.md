# Workbench v5.8.0 Security & Physical-Execution Boundary

v5.8.0 performs bounded numerical electronics calculations and produces planning/export artifacts only.

It does **not** authorize or perform:

- arbitrary Python or JavaScript evaluation;
- shell or remote-shell execution;
- serial-port access;
- GPIO access;
- JTAG/programmer access;
- automatic firmware flashing;
- automatic FPGA bitstream programming;
- automatic hardware actuation;
- unattended physical-system control.

Generated Arduino, ESP32, Raspberry Pi, PYNQ, Verilog, and VHDL files are scaffolds only. A human must verify the exact board revision, pinout, voltage/current limits, component ratings, timing, grounding, isolation, and any applicable electrical/safety requirements before using exported material on physical hardware.
