# Workbench v10.4.0 — Hyperparameter Optimization & Search Engine Map

```text
v10.0 AI experiment
      ↓
v10.1 immutable model/dataset binding
      ↓
v10.2 training-run template ──────────┐
                                     ├→ v10.4 search study
v10.3 benchmark + metric objective ──┘        ↓
                                      typed search space
                                             ↓
                         grid / random / Latin-hypercube
                         or external Bayesian/custom contract
                                             ↓
                                  deterministic trial manifest
                                             ↓
                               explicit execution plan only
                                             ↓
                                  immutable trial results
                                             ↓
                                  objective diagnostics
                                             ↓
                             Platform Core plan-only handoff
```

Objective ordering is a researcher-defined metric diagnostic. It is not automatic model preference, production approval, or scientific-validity certification.
