# Workbench v5.3.0 Security Boundary

v5.3.0 preserves the governed execution model established in v5.1 and v5.2.

- Blackboard expressions use the restricted AST/SymPy parser.
- No Python `eval` or `exec` is used for user mathematics.
- Music and creative-form calculations are bounded mathematical transforms.
- Prototype targets are an allowlisted enum.
- Prototype code is generated from fixed templates and returned as text.
- No generated code is automatically executed.
- No Arduino/ESP32 flashing is authorized.
- No PYNQ bitstream loading is performed by the public Workbench.
- No FPGA synthesis, place-and-route, programming, or device I/O is automatic.
- No remote shell is exposed.
- Human review remains required before physical deployment.
