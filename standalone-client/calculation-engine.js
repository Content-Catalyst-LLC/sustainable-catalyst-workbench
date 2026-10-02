/**
 * Sustainable Catalyst Workbench v11 unified calculation engine client.
 *
 * Framework-neutral. Calls FastAPI directly; WordPress is optional.
 */
export async function calculationObjectSchema(api) {
  return api.request("/calculation-engine/v1/schema");
}

export async function normalizeCalculation(api, request) {
  return api.request("/calculation-engine/v1/normalize", {
    method: "POST",
    body: request,
  });
}

export async function planCalculation(api, request) {
  return api.request("/calculation-engine/v1/plan", {
    method: "POST",
    body: request,
  });
}

export async function computeCalculationObject(api, request) {
  return api.request("/calculation-engine/v1/compute", {
    method: "POST",
    body: request,
  });
}
