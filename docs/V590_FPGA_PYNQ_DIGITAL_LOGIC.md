# v5.9.0 FPGA, PYNQ & Digital Logic Workbench

The v5.9 layer connects Boolean mathematics to digital hardware artifacts without turning the public Workbench into a remote hardware-programming surface.

## Capability chain

`BOOLEAN EXPRESSION → TRUTH TABLE → MINIMIZATION / K-MAP → FSM / TIMING → RESOURCE ESTIMATE → HDL / TESTBENCH → PYNQ PLAN`

The Boolean parser accepts variables, constants 0/1, NOT (`!` or `~`), AND (`&`), OR (`|`), XOR (`^`) and parentheses. The words `NOT`, `AND`, `OR`, and `XOR` are accepted as operator aliases. The parser is deterministic and does not use Python `eval` or dynamic code generation.

Truth-table generation is bounded to ten variables. Karnaugh maps are bounded to two through four variables. FSM validation rejects duplicate state/input transitions and reports reachability, incomplete input coverage, and selected binary, Gray, or one-hot encodings. Timing analysis evaluates discrete logic samples and explicitly does not claim propagation-delay, metastability, or timing-closure analysis.

HDL output is an export scaffold. Constraint files deliberately contain placeholders rather than guessed board pin assignments. PYNQ scaffolds reference externally built `.bit` and `.hwh` artifacts but do not run Vivado or load an overlay.
