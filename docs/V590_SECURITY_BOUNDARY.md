# v5.9.0 Security & Execution Boundary

v5.9.0 authorizes deterministic logic analysis, zero-delay logic waveform simulation, and text artifact export only.

The release explicitly keeps the following disabled:

- arbitrary code execution
- Python eval/exec
- remote shell access
- subprocess-based synthesis
- Vivado/Quartus invocation
- placement and routing execution
- automatic board pin assignment
- bitstream generation
- bitstream programming
- JTAG access
- physical device execution
- PYNQ overlay loading

Generated HDL, testbenches, constraints, and PYNQ files require human review in an approved external toolchain.
