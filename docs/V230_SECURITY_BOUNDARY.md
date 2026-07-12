# Workbench v2.3.0 Security Boundary

- Browser calculations and project storage remain local to the browser.
- The Go Runner listens only on 127.0.0.1:8787.
- Pairing tokens are origin-bound.
- Native and robotics diagnostic tasks are disabled unless the runner starts with `--enable-native-exec`.
- The runner exposes no arbitrary shell endpoint.
- Robotics tasks are a fixed allowlist of tool-version diagnostics.
- Device motion, GPIO writes, motor commands, flashing, and autonomous operation are not performed by v2.3.0.
