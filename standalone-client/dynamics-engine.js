export async function dynamics(api, request) {
  return api.request("/calculation-engine/v1/dynamics",{method:"POST",body:request});
}
export async function dynamicsCalculationObject(api, calculationObjectRequest, dynamicsRequest) {
  return api.request("/calculation-engine/v1/dynamics/calculation-object",{
    method:"POST",body:{calculationObjectRequest,dynamics:dynamicsRequest}});
}
