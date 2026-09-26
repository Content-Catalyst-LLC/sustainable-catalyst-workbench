# Workbench v9.5.0 — Model Calibration & Parameter Estimation

Adds explicit, provenance-preserving calibration problems over completed computational campaigns. Researchers specify target observations, calibration parameters and bounds, estimator, loss function, confidence level, assumptions, and interpretation.

Capabilities include campaign candidate objective scoring, bounded linear-response-surface parameter estimation, weighted least squares, robust Huber loss, residual diagnostics, identifiability/conditioning diagnostics, approximate parameter intervals when supported by the calibration Jacobian, immutable calibration records, downstream analysis planning, and Platform Core binding plans.

Scientific boundaries remain explicit: Workbench does not infer model validity, scientific acceptance, causality, preferred model status, priors, or convergence truth; it does not execute new jobs or automatically dispatch to Platform Core.
