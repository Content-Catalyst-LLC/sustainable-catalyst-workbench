export async function numericalAnalysis(api, request) {
  return api.request("/calculation-engine/v1/numerical-analysis",{method:"POST",body:request});
}
export async function numericalAnalysisCalculationObject(api, calculationObjectRequest, numericalAnalysisRequest) {
  return api.request("/calculation-engine/v1/numerical-analysis/calculation-object",{
    method:"POST",body:{calculationObjectRequest,numericalAnalysis:numericalAnalysisRequest}});
}
