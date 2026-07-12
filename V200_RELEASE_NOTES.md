# Sustainable Catalyst Prototyping Workbench v2.0.0

## Go Runner, Research Lab, and Hardware Studio Foundation

Version 2.0.0 extends the editor-first v1.9.1 Browser Code Lab without replacing its calculator registry, symbolic tools, browser runtimes, saved projects, or existing shortcodes.

## Added

- Optional Go Runner for Apple Silicon, Intel macOS, Linux x86-64, Linux ARM64, and Linux ARMv7
- Loopback-only service on `127.0.0.1:8787`
- One-time six-digit browser pairing and origin-bound session tokens
- Runtime and toolchain discovery for Python, JavaScript, Go, C, C++, Rust, Arduino CLI, Yosys, nextpnr, and Haskell
- Explicit opt-in structured native execution for allowlisted languages
- Research Lab Canvas with pointer/stylus support, undo, browser-local persistence, and PNG export
- Structured Research and Lab Notebook with JSON export
- Technical Documentation Studio with Markdown generation
- Arduino sketch scaffolding
- Conceptual schematic generation and SVG export
- Editable synchronized bill of materials with CSV export
- Conceptual PCB placement generation and SVG export
- Educational Assembly Translator foundation
- FPGA Verilog project scaffold
- Standalone shortcodes for every new panel
- FastAPI v2 foundation, hardware-manifest, and documentation contracts

## Preserved

- Existing `[sc_workbench]` behavior
- Browser Code Studio and terminal shortcodes
- JavaScript, Python/Pyodide, R/webR, and SQL/DuckDB-Wasm browser execution
- Existing calculator, graph, equation, report, placement, and validation interfaces
- Existing WordPress REST namespace
- Existing browser-local projects and storage records
- Existing FastAPI analytical and AI backend

## Security boundary

The local runner is disabled for execution by default. It binds only to loopback, requires a one-time pairing code, binds tokens to the requesting browser origin, caps request/output sizes and execution time, accepts only fixed language adapters, and has no general shell endpoint.

The runner is not a hostile-code sandbox. When native execution is enabled, code runs with the permissions of the local user. Run only trusted code. Generated schematics, PCB concepts, hardware recommendations, assembly scaffolds, FPGA code, and technical documents require validation against actual components, toolchains, standards, operating conditions, and field evidence.

## New shortcodes

```text
[sc_workbench_lab_canvas project="default"]
[sc_workbench_notebook project="default"]
[sc_workbench_documentation_studio project="default"]
[sc_workbench_hardware_studio project="default"]
[sc_workbench_arduino project="default"]
[sc_workbench_schematic project="default"]
[sc_workbench_bom project="default"]
[sc_workbench_pcb project="default"]
[sc_workbench_assembly project="default"]
[sc_workbench_fpga project="default"]
[sc_workbench_local_runner project="default"]
```
