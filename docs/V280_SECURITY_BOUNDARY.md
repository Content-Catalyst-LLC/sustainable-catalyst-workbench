# Workbench v2.8.0 Security and Automation Boundary

- The local runner binds only to `127.0.0.1:8787`.
- Browser access requires a one-time pairing code and origin-bound token.
- Experiment diagnostics are allowlisted version checks only.
- There is no arbitrary shell endpoint.
- Browser schedule plans do not install cron, launchd, systemd timers, or another persistent scheduler.
- Native execution remains disabled unless the user starts the runner with `--enable-native-exec`.
- The Workbench does not bypass hardware interlocks or approve unattended laboratory operation.
- Protocols, checkpoints, datasets, code revisions, instruments, physical conditions, and exports require project-specific review.
