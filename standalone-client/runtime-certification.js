export async function certifyRuntimeCalculation(api, request) {
  return api.request("/calculation-engine/v1/runtime-certification",{
    method:"POST",body:request
  });
}

export async function certifyRuntimeCalculationObject(api, calculationObjectRequest, certification) {
  return api.request("/calculation-engine/v1/runtime-certification/calculation-object",{
    method:"POST",body:{calculationObjectRequest,certification}
  });
}
