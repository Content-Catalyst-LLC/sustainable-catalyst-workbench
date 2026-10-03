export async function uncertaintyAnalysis(api, request) {
  return api.request("/calculation-engine/v1/uncertainty",{method:"POST",body:request});
}
export async function uncertaintyCalculationObject(api, calculationObjectRequest, uncertaintyAnalysis) {
  return api.request("/calculation-engine/v1/uncertainty/calculation-object",{
    method:"POST",body:{calculationObjectRequest,uncertaintyAnalysis}});
}
