/**
 * Sustainable Catalyst Workbench v11.3 equation & solver client.
 */
export async function solverLaboratory(api, request) {
  return api.request("/calculation-engine/v1/solver", {
    method: "POST",
    body: request,
  });
}

export async function solverCalculationObject(api, calculationObjectRequest, solverRequest) {
  return api.request("/calculation-engine/v1/solver/calculation-object", {
    method: "POST",
    body: {
      calculationObjectRequest,
      solver: solverRequest,
    },
  });
}
