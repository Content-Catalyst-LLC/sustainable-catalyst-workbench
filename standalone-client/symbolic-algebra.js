/**
 * Sustainable Catalyst Workbench v11.1 symbolic algebra client.
 */
export async function symbolicAlgebra(api, request) {
  return api.request("/calculation-engine/v1/symbolic/algebra", {
    method: "POST",
    body: request,
  });
}

export async function symbolicCalculationObject(api, calculationObjectRequest, symbolicAlgebraRequest) {
  return api.request("/calculation-engine/v1/symbolic/calculation-object", {
    method: "POST",
    body: {
      calculationObjectRequest,
      symbolicAlgebra: symbolicAlgebraRequest,
    },
  });
}
