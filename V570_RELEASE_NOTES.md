# Sustainable Catalyst Workbench v5.7.0

## Signals, Systems & Control Mathematics

Workbench v5.7.0 extends the post-v5.6 scientific-computing line into bounded signal processing and control-system mathematics.

### Added

- FFT spectrum analysis with Hann, Hamming, Blackman, and rectangular windows.
- One-sided amplitude and power-spectral-density output.
- Dominant-frequency and bounded harmonic/THD inspection.
- Discrete convolution with optional kernel normalization.
- Butterworth and Chebyshev-I digital filter design.
- Low-pass, high-pass, band-pass, and band-stop frequency-response analysis.
- Continuous-time transfer-function analysis with poles, zeros, DC gain, Bode response, and step/optional impulse response.
- Root-locus sampling over a bounded gain interval.
- SISO continuous state-space analysis with controllability and observability ranks and step response.
- PID closed-loop simulation with stability, overshoot, rise time, settling time, steady-state error, and integral absolute error.
- Canonical content-hashed signal/control result objects.
- A dedicated WordPress Signals, Systems & Control Mathematics studio.
- Workbench Settings capability check for the v5.7 backend.

### Public shortcodes

- `[sc_workbench_signals_systems_controls]`
- `[sc_workbench_control_mathematics]`
- `[sc_workbench_signals_studio]`
- `[sc_workbench_signals]`
- `[sc_workbench_systems_control]`

### Backend routes

- `GET /v570/status`
- `POST /v570/spectrum`
- `POST /v570/convolve`
- `POST /v570/filter-design`
- `POST /v570/transfer-function`
- `POST /v570/state-space`
- `POST /v570/pid`
- `POST /v570/root-locus`

### Deployment

The backend runtime advances to v5.7.0. Deploy the Contabo Workbench service before installing the WordPress interface.

### Boundary

The release performs analysis and simulation only. It does not authorize arbitrary Python execution, shell access, controller deployment, unattended device programming, or physical-system actuation.
