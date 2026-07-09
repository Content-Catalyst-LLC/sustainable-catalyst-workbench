# Workbench v1.7.0 — Advanced Domain Calculators

Phase 7 expands the Workbench calculator library beyond the initial engineering set. The same calculator UI now supports advanced deterministic calculators across:

- Econometrics
- Psychometrics
- Computational biology
- Computational chemistry
- Computational physics
- Architecture
- Infrastructure
- Pattern recognition across math, art, and music
- Astrophysics

The implementation intentionally keeps computation deterministic and reviewable. AI may later help explain, route, or compare outputs, but the calculator results are produced by Python/Numpy/Matplotlib-backed functions.

## New calculators

- Econometrics: Simple OLS
- Econometrics: Difference-in-Differences
- Psychometrics: Cronbach's Alpha
- Psychometrics: Standard Error of Measurement
- Computational Biology: Logistic Growth
- Computational Biology: Michaelis-Menten
- Computational Chemistry: Arrhenius Rate
- Computational Chemistry: Nernst Potential
- Computational Physics: Harmonic Oscillator
- Computational Physics: Projectile Motion
- Architecture: Floor-Area Efficiency
- Architecture: Daylight Aperture
- Infrastructure: Peak Water Demand
- Infrastructure: Rational Runoff
- Pattern Recognition: Cosine Similarity
- Pattern Recognition: Harmonic Centroid
- Astrophysics: Kepler Orbit
- Astrophysics: Luminosity and Flux

## Shortcodes

Full Workbench:

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="compact"]
```

Standalone advanced calculator library:

```text
[sc_workbench_advanced_calculators title="Advanced Calculator Library"]
```

Backward-compatible engineering calculator shortcode remains available:

```text
[sc_workbench_engineering_calculators title="Advanced Calculator Library"]
```

## Boundary

The calculators are educational, analytical, and research-support tools. They are not substitutes for licensed engineering, architecture, clinical, legal, financial, laboratory, scientific, safety-critical, or professional judgment.
