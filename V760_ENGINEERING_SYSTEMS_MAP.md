# v7.6.0 Engineering Systems Map

| Analysis key | Domain | Bounded method |
|---|---|---|
| `mechanical.axial-member` | Mechanical | Linear axial stress/strain |
| `mechanical.simply-supported-beam` | Mechanical | Euler–Bernoulli small-deflection beam |
| `thermal.conduction` | Thermal | Steady 1D Fourier conduction |
| `thermal.convection` | Thermal | Newton cooling/convection |
| `fluids.pipe-flow` | Fluids | Darcy–Weisbach with laminar/Haaland friction |
| `civil.axial-capacity` | Civil / infrastructure | Declared allowable axial capacity/utilization |
| `electrical.dc-circuit` | Electrical | Ohm-law/DC power balance |
| `controls.actuator-sizing` | Controls / mechatronics | Existing bounded v2.3 actuator sizing |
| `energy.explicit-handoff` | Energy systems | Existing explicit-input Energy Systems handoff |

The runtime emits canonical engineering result objects, v7.1 execution objects, workspace binding plans, bounded system bundles, and two-phase Platform Core lineage plans. It does not certify code compliance, physical safety, or professional-engineering approval.
