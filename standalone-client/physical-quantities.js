export async function physicalQuantity(api, request) {
  return api.request("/calculation-engine/v1/quantities",{method:"POST",body:request});
}
export async function physicalQuantityCalculationObject(api, calculationObjectRequest, quantityRequest) {
  return api.request("/calculation-engine/v1/quantities/calculation-object",{
    method:"POST",body:{calculationObjectRequest,quantity:quantityRequest}});
}
