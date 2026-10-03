export async function optimization(api, request) {
  return api.request("/calculation-engine/v1/optimization",{method:"POST",body:request});
}
export async function optimizationCalculationObject(api, calculationObjectRequest, optimizationRequest) {
  return api.request("/calculation-engine/v1/optimization/calculation-object",{
    method:"POST",body:{calculationObjectRequest,optimization:optimizationRequest}});
}
