/**
 * Sustainable Catalyst Workbench v11.4 linear algebra, matrix & tensor client.
 */
export async function linearAlgebra(api, request) {
  return api.request("/calculation-engine/v1/linear-algebra", {
    method: "POST",
    body: request,
  });
}

export async function linearAlgebraCalculationObject(api, calculationObjectRequest, linearAlgebraRequest) {
  return api.request("/calculation-engine/v1/linear-algebra/calculation-object", {
    method: "POST",
    body: {
      calculationObjectRequest,
      linearAlgebra: linearAlgebraRequest,
    },
  });
}
