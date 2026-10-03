export async function mathematicalViews(api, request) {
  return api.request("/calculation-engine/v1/graphing",{method:"POST",body:request});
}

export async function mathematicalViewsCalculationObject(api, calculationObjectRequest, graphing) {
  return api.request("/calculation-engine/v1/graphing/calculation-object",{
    method:"POST",body:{calculationObjectRequest,graphing}});
}

export function createLinkedViewState(viewSpec) {
  return {
    linkGroup: viewSpec.linkGroup,
    crosshair: null,
    selectedDatum: null,
    domain: null
  };
}

export function linkedViewEvent(linkGroup, type, payload) {
  return {linkGroup,type,payload};
}
