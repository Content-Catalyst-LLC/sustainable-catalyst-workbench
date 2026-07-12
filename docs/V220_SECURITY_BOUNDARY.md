# Workbench v2.2.0 Security and Engineering Boundary

## Local runner

The Workbench Go Runner listens only on `127.0.0.1:8787`. It requires a one-time six-digit pairing code, binds session tokens to the browser origin, limits JSON request and output sizes, uses execution timeouts, and exposes no general shell endpoint.

`GET /hardware-tools` performs path discovery only. `POST /hardware-task` accepts only named tool-version tasks, requires explicit user consent, and remains disabled unless the runner starts with `--enable-native-exec`.

## Browser data

Workbench v2.2.0 project, schematic, BOM, PCB, and validation records are stored in browser local storage unless the user exports them. Do not enter secrets, private keys, regulated personal data, or confidential design data into a public/shared browser profile.

## Engineering limits

- FPGA timing and resource parsing is best-effort across varied tool formats and must be checked against the original report.
- Constraint generation is a starting record, not a verified board definition.
- Schematic checks operate on structured user-entered data and are not a complete ERC.
- PCB checks are preliminary and do not know real footprint geometry, copper, impedance, creepage, clearance, stackup, or fabricator capabilities.
- BOM values are not live inventory, compliance, authenticity, lifecycle, or pricing data.
- Validation evaluation does not calibrate instruments, authenticate evidence, establish measurement uncertainty, or provide certification.

Qualified engineering review and hardware-in-the-loop verification remain mandatory.
