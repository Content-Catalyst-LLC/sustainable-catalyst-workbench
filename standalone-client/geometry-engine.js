export async function geometry(api, request) {
  return api.request("/calculation-engine/v1/geometry",{method:"POST",body:request});
}
export async function geometryCalculationObject(api, calculationObjectRequest, geometryRequest) {
  return api.request("/calculation-engine/v1/geometry/calculation-object",{
    method:"POST",body:{calculationObjectRequest,geometry:geometryRequest}});
}
