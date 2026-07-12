# Sustainable Catalyst Prototyping Workbench v2.2.0

## FPGA, Electronics Design, and Hardware Validation Studio

Workbench v2.2.0 converts the hardware foundations introduced in v2.0.0 and expanded in v2.1.0 into a connected electronics-engineering and verification workflow.

## New WordPress modules

- `[sc_workbench_fpga_studio project="default"]`
- `[sc_workbench_electronics_design project="default"]`
- `[sc_workbench_schematic_editor project="default"]`
- `[sc_workbench_bom_validation project="default"]`
- `[sc_workbench_pcb_studio project="default"]`
- `[sc_workbench_hardware_validation project="default"]`

## FPGA Studio

- Verilog, SystemVerilog, and VHDL project records
- iCEBreaker/iCE40, ULX3S/ECP5, Arty A7, and generic board profiles
- Pin, I/O-standard, clock, and timing-constraint records
- Constraint collision and clock-identification checks
- Implementation-report parsing for errors, warnings, resource estimates, slack, and maximum frequency
- Project-bundle export with HDL, constraints, manifest, and implementation-review template
- Paired local discovery for Yosys, nextpnr, Icarus Verilog, Verilator, GHDL, openFPGALoader, OpenOCD, KiCad CLI, and related tools

## Electronics Design Studio

- Supply, logic-rail, load, and power-budget records
- Structured functional-block architecture
- Regulator/converter, protection, decoupling, test-access, and thermal-review findings
- Exportable architecture records and review gates

## Schematic and Netlist Studio

- Structured component, footprint, pin, net, and endpoint records
- Duplicate reference and net-name detection
- Unknown endpoint and cross-net endpoint detection
- Unconnected-pin review
- Portable JSON netlist and schematic-review exports

## BOM Validation Studio

- Quantity, unit-cost, extended-cost, lifecycle, and substitute fields
- Budget-ceiling checks
- Strict, review, and prototype lifecycle policies
- Validated CSV export and sourcing record
- Clear limits: costs and availability are user-entered, not live supplier data

## PCB Planning and Design-Rule Studio

- Board outline, copper-layer, track/space, via, edge-clearance, and environment records
- Placement coordinates, side, rotation, and component-class records
- Outline, collision, duplicate-reference, and conservative environment-threshold checks
- Exportable preliminary PCB plan

## Hardware Validation Studio

- Bring-up, verification, environmental, and production-test stages
- Test definitions with limits, units, and methods
- Measured results, notes, and evidence references
- PASS/FAIL/NOT RUN evaluation
- Validation dossier and CSV exports
- Signoff placeholders and explicit evidence/authentication limits

## Backend and local runner

- FastAPI v2.2.0 routes for FPGA projects, electronics review, schematic validation, BOM validation, PCB review, and test-plan evaluation
- Go Runner v2.2.0 hardware-tool discovery
- Named allowlisted hardware-version tasks
- Loopback-only service, browser-origin pairing, explicit consent, bounded request/output sizes, and no arbitrary shell endpoint

## Compatibility

The release preserves the v1.x calculator and browser-runtime stack, v2.0.0 Research Lab and Hardware Studio foundation, and v2.1.0 Raspberry Pi, TinyML, calibration, embedded board, and device-log modules.

## Engineering boundary

Generated HDL, constraints, schematics, netlists, BOMs, PCB plans, calculations, report interpretations, and validation records are research and early-stage engineering artifacts. They do not replace electrical-rule checking, timing analysis, simulation, fabrication review, standards review, calibrated instrumentation, safety engineering, certification, or qualified professional signoff.
