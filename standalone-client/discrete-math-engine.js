export async function discreteMath(api, request) {
  return api.request("/calculation-engine/v1/discrete-math",{method:"POST",body:request});
}
export async function discreteMathCalculationObject(api, calculationObjectRequest, discreteMathRequest) {
  return api.request("/calculation-engine/v1/discrete-math/calculation-object",{
    method:"POST",body:{calculationObjectRequest,discreteMath:discreteMathRequest}});
}
