# Workbench v7.2.0 Runtime Adapter Map

| Adapter | Mode | Categories | Execution |
|---|---|---|---|
| `workbench.symbolic` | in-process | mathematics | bounded local |
| `workbench.numerical` | in-process | numerical-scientific | bounded local |
| `workbench.simulation` | in-process | simulation-systems | bounded local |
| `workbench.controls` | in-process | controls-mechatronics, signals-controls | bounded local |
| `workbench.measurement` | in-process | measurement-instrumentation | bounded local |
| `workbench.electronics` | in-process | electronics-embedded, digital-logic-fpga | bounded local |
| `workbench.uncertainty` | in-process | uncertainty-sensitivity | bounded local |
| `workbench.predictive` | in-process | predictive | bounded local |
| `workbench.forensics` | in-process | forensic-quantitative | bounded local |
| `workbench.energy` | in-process | energy-systems | bounded local |
| `external.r` | handoff-plan | future bounded adapter | **no execution** |
| `external.julia` | handoff-plan | future bounded adapter | **no execution** |
| `external.ml` | handoff-plan | future bounded adapter | **no execution** |

Routing is deterministic by operation category. An explicit preferred runtime must support the operation category. Plan-only adapters never execute code in v7.2.
