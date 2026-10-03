export async function probabilityStatistics(api, request) {
  return api.request("/calculation-engine/v1/statistics",{method:"POST",body:request});
}
export async function probabilityStatisticsCalculationObject(api, calculationObjectRequest, statisticsRequest) {
  return api.request("/calculation-engine/v1/statistics/calculation-object",{
    method:"POST",body:{calculationObjectRequest,statistics:statisticsRequest}});
}
