# Sustainable Catalyst Workbench v3.0.2

Project Migration, Storage, and Recovery for the Unified Prototyping Workbench. v3.0.2 adds a twelfth recovery studio for legacy-project discovery, migration preview, browser-storage health, content-hashed backups, conflict-aware restore, rollback, and guarded cleanup while retaining every v2.x and v3.x studio.

See `V301_RELEASE_NOTES.md`.

# Sustainable Catalyst Prototyping Workbench v2.8.0

## Version 2.0.0 — Go Runner, Research Lab, and Hardware Studio Foundation

Adds an optional loopback-only Go runner, one-time browser pairing, origin-bound tokens, allowlisted native runtime discovery and execution, a Research Lab Canvas, structured Research and Lab Notebook, Technical Documentation Studio, Arduino Studio, conceptual schematic and PCB generators, synchronized BOM workflows, an Assembly Translator foundation, and an FPGA Studio foundation.

Native execution is disabled by default and is not a hostile-code sandbox. It runs only on the local visitor machine when the runner is explicitly started with `--enable-native-exec`. Generated code, electronics, PCB, and FPGA outputs require technical review and validation.

## Version 2.1.0 — Raspberry Pi, TinyML, and Embedded Device Studio

Adds a Raspberry Pi project generator, structured embedded-device discovery through the loopback Go Runner, TinyML dataset validation and browser baselines, INT8 and Float16 deployment previews, sensor calibration with residual and uncertainty records, device observation logs, an expanded embedded board catalog, and project-bundle exports.

The local runner remains loopback-only and origin-paired. It exposes no arbitrary shell endpoint. The new device-task endpoint accepts only named allowlisted tasks; Arduino CLI board discovery additionally requires `--enable-native-exec`. Generated models, code, wiring assumptions, and deployment scaffolds require hardware-in-the-loop validation.

## Version 2.2.0 — FPGA, Electronics Design, and Hardware Validation Studio

Adds FPGA project generation and implementation-report review, HDL and board-constraint records, electronics architecture checks, structured schematic and netlist validation, BOM lifecycle/cost/substitution review, preliminary PCB planning and design-rule checks, hardware test-plan evaluation, validation dossiers, and expanded local hardware-tool discovery.

The local runner remains loopback-only and origin-paired. It exposes no arbitrary shell endpoint. Named hardware-version tasks require explicit consent and `--enable-native-exec`. Generated HDL, constraints, schematics, netlists, BOMs, PCB plans, test records, and validation results require qualified engineering review and hardware-in-the-loop verification.

## Version 2.3.0 — Robotics, Controls, and Mechatronics Studio

Adds differential-drive kinematics, PID baseline simulation, mechatronics architecture review, actuator sizing, robot state-machine validation, hardware-in-the-loop telemetry checks, and paired local robotics-tool discovery.

## Version 2.4.0 — Instrumentation, Data Acquisition, and Signal Analysis Studio

Adds instrumentation range and resolution review, data-acquisition sizing, time-domain statistics, browser-local spectrum analysis, calibration and uncertainty budgets, measurement-campaign validation, and paired local instrumentation-tool discovery.

## Version 2.5.0 — Simulation, Digital Twin, and Systems Modeling Studio

Adds dynamic simulation, bounded digital-twin calibration, coupled systems models, scenario sweeps, seeded Monte Carlo uncertainty, model validation, and paired local simulation-tool discovery.

## Version 2.6.0 — Multi-Language Engineering Runtime Studio

Adds Python, JavaScript, R, SQL, Go, C, C++, Rust, Haskell, and assembly profiles; cross-language calculation equivalence; numerical-stability benchmarks; generated projects and test vectors; reproducibility validation; execution-boundary auditing; and paired local runtime discovery and execution.

## Version 2.7.0 — Scientific Visualization and Engineering Dashboard Studio

Adds browser-local scientific figures, threshold-aware engineering dashboards, interactive parameter charts, validation overlays, system-state views, accessible descriptions, and report-ready visual exports.

## Version 2.8.0 — Experiment Automation and Reproducible Workflow Studio

Adds structured protocols, dependency-aware experiment pipelines, schedule and resource-conflict planning, dataset/configuration manifests, automatic checkpoints, reproducibility comparison, deviation records, and exportable experiment bundles.

## Version 2.9.0 — Technical Documentation and Product Dossier Studio

Adds versioned technical-document generation, product dossiers, requirements-to-test traceability, revision and engineering-change control, verification-evidence registers, manufacturing and release-readiness gates, reproducible documentation snapshots, Markdown/HTML/JSON exports, and paired local documentation-tool discovery.

The documentation layer preserves project sources, revisions, evidence, limitations, risks, review states, and SHA-256 record hashes. Readiness scores and dossier exports are planning aids only; they do not establish certification, regulatory approval, conformity, product safety, manufacturing readiness, or professional sign-off.
