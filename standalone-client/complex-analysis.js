export async function complexAnalysis(api, request) {
  return api.request("/calculation-engine/v1/complex-analysis",{method:"POST",body:request});
}
export async function complexAnalysisCalculationObject(api, calculationObjectRequest, complexAnalysisRequest) {
  return api.request("/calculation-engine/v1/complex-analysis/calculation-object",{
    method:"POST",body:{calculationObjectRequest,complexAnalysis:complexAnalysisRequest}});
}
