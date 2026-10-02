/**
 * Sustainable Catalyst Workbench v11.2 calculus client.
 */
export async function calculus(api, request) {
  return api.request("/calculation-engine/v1/calculus", {
    method: "POST",
    body: request,
  });
}

export async function calculusCalculationObject(api, calculationObjectRequest, calculusRequest) {
  return api.request("/calculation-engine/v1/calculus/calculation-object", {
    method: "POST",
    body: {
      calculationObjectRequest,
      calculus: calculusRequest,
    },
  });
}
