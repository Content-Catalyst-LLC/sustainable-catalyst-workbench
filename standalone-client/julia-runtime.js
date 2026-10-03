export async function juliaRuntime(api) {
  return api.request("/calculation-engine/v1/runtimes/julia");
}
export async function juliaRuntimeContract(api) {
  return api.request("/calculation-engine/v1/runtimes/julia/contract");
}
export async function executeJulia(api, request) {
  return api.request("/calculation-engine/v1/runtimes/julia/execute",{method:"POST",body:request});
}
export async function juliaCalculationObject(api, calculationObjectRequest, juliaRequest) {
  return api.request("/calculation-engine/v1/runtimes/julia/calculation-object",{
    method:"POST",body:{calculationObjectRequest,julia:juliaRequest}});
}
