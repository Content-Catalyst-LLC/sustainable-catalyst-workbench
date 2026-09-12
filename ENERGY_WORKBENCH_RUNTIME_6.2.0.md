# Energy Workbench Runtime 6.2.0

Energy Systems version: 1.3.0

## Execution routes

- `GET /v1/energy-runtime/execution-framework`
- `POST /v1/energy-runtime/plan`
- `POST /v1/energy-runtime/execute`
- `POST /v1/energy-runtime/validate-result`

## Supported calculations

Unit conversion; conversion-chain efficiency; supply-demand balance; capacity-factor generation; energy-cost comparison; simple payback; net present value; cost-benefit; cost-efficiency; simplified levelized energy cost; feedstock energy; anaerobic-digestion energy; biochar-carbon stoichiometry; biomass-to-oil energy.

## Boundary

Inputs must be explicit. Workbench does not supply hidden defaults, market prices, avoided-emissions estimates, lifecycle claims, rankings, recommendations, or persistence. Biochar output is a physical stoichiometric equivalence only and is not carbon-accounting or carbon-credit assurance.
