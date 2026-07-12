# Workbench v2.0.0 Local Runner Security Boundary

The Go Runner is a local development bridge, not a remote compute service and not a hostile-code sandbox.

## Controls

- Listens only on `127.0.0.1:8787`
- Does not bind to LAN or public interfaces
- Prints a one-time six-digit pairing code in the local terminal
- Requires the browser request origin to match the paired origin
- Issues random origin-bound bearer tokens held in browser session storage
- Native execution is off unless the user starts with `--enable-native-exec`
- Requires an explicit consent value on each execution request
- Accepts only allowlisted language identifiers
- Invokes fixed runtime/compile commands directly without a shell
- Creates an isolated temporary working directory per run
- Removes temporary files after execution
- Applies request, source, output, and timeout limits
- Exposes no arbitrary command, path, package-installation, or shell endpoint

## What these controls do not provide

- Operating-system sandboxing
- Container isolation
- Protection from malicious source code run by the local user
- Package or dependency isolation
- Guaranteed prevention of file, network, process, or resource access by executed programs
- Engineering, manufacturing, electrical, FPGA, or compliance validation

Use discovery-only mode for routine public demonstrations. Enable native execution only on a trusted computer and only for code you have reviewed.
