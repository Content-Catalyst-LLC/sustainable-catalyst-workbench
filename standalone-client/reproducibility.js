export async function captureReplayEnvelope(api, calculationRequest, calculationObject=null, label="", notes="") {
  return api.request("/calculation-engine/v1/reproducibility/capture",{
    method:"POST",
    body:{calculationRequest,calculationObject,label,notes}
  });
}

export async function replayCalculation(api, envelope, comparisonMode="strict") {
  return api.request("/calculation-engine/v1/reproducibility/replay",{
    method:"POST",body:{envelope,comparisonMode}
  });
}

export async function compareCalculationObjects(api, expected, observed, comparisonMode="strict") {
  return api.request("/calculation-engine/v1/reproducibility/compare",{
    method:"POST",body:{expected,observed,comparisonMode}
  });
}

export async function attachReproducibility(api, calculationRequest, calculationObject=null) {
  return api.request("/calculation-engine/v1/reproducibility/calculation-object",{
    method:"POST",body:{calculationRequest,calculationObject}
  });
}
