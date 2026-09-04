# Workbench v5.7.0 — Signals, Systems & Control Mathematics

The v5.7.0 studio connects mathematical analysis to signal-processing and control-system workflows without exposing a general-purpose execution surface.

## Signal analysis

The spectrum engine accepts bounded numeric sample arrays, sample rate, detrending choice, and an allowlisted window. It returns a one-sided FFT amplitude spectrum, PSD, phase, dominant peaks, RMS, fundamental estimate, and bounded harmonic/THD estimate.

## Filters

Digital filters are designed through SciPy's bounded Butterworth or Chebyshev-I paths. Users select order, response type, sample rate, cutoff frequencies, and ripple where applicable. The result contains second-order sections, digital poles/zeros, stability, and frequency response.

## Systems

Continuous transfer functions expose poles, zeros, gain, DC gain, Bode response, step response, and optional impulse response. Root-locus analysis samples the unity-feedback closed-loop characteristic polynomial across an explicit bounded gain interval.

## State space

The state-space surface accepts bounded SISO A/B/C/D matrices, reports eigenvalues and continuous-time stability, calculates controllability and observability matrices/ranks, and produces a step response.

## PID

The PID surface forms an ideal continuous controller `C(s) = (Kd s² + Kp s + Ki) / s`, combines it with a numeric plant transfer function under unity feedback, and returns the closed-loop response plus overshoot, rise time, settling time, steady-state error, and integral absolute error.

## Reproducibility

Every backend result carries source parameters, the v5.7.0 schema/version, explicit safety-boundary flags, and a SHA-256 `signalsControlObjectHash`.
