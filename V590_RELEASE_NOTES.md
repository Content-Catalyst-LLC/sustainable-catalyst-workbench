# Workbench v5.9.0 — FPGA, PYNQ & Digital Logic Workbench

v5.9.0 adds a governed digital-logic and FPGA planning layer to the Workbench. It provides restricted Boolean-expression parsing, truth tables, Boolean minimization, Karnaugh maps, deterministic finite-state-machine validation, zero-delay digital timing waveforms, pre-synthesis logic-resource estimates, Verilog/VHDL plus testbench scaffolds, and PYNQ overlay planning.

The backend advances to v5.9.0 and must be redeployed.

## New backend routes

- `GET /v590/status`
- `POST /v590/truth-table`
- `POST /v590/minimize`
- `POST /v590/karnaugh`
- `POST /v590/fsm`
- `POST /v590/timing`
- `POST /v590/hdl-scaffold`
- `POST /v590/resource-estimate`
- `POST /v590/pynq-overlay`

## WordPress

Primary studio shortcode: `[sc_workbench_digital_logic]`

Aliases: `[sc_workbench_fpga_pynq]`, `[sc_workbench_digital_logic_studio]`, `[sc_workbench_fpga_workbench]`, `[sc_workbench_pynq_studio]`.

## Boundary

No synthesis execution, placement/routing, automatic physical-pin resolution, bitstream generation, bitstream programming, JTAG access, PYNQ overlay loading, shell execution, Python eval, or arbitrary code execution is authorized.
