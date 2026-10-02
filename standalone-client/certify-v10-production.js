/**
 * Workbench v10 production certification helper.
 *
 * Talks directly to the canonical FastAPI runtime; WordPress is not required.
 */
export async function certifyWorkbenchV10Production(api) {
  const [status, certification, releases, contracts, probe] = await Promise.all([
    api.request("/v10120/status"),
    api.request("/certification/v10"),
    api.request("/certification/v10/releases"),
    api.request("/certification/v10/contracts"),
    api.request("/certification/v10/probe"),
  ]);

  const ok =
    status.data.ok === true &&
    certification.data.certification === "pass" &&
    releases.data.ok === true &&
    contracts.data.ok === true &&
    probe.data.ok === true;

  return {
    ok,
    version: status.data.version,
    status: status.data,
    certification: certification.data,
    releases: releases.data,
    contracts: contracts.data,
    probe: probe.data,
  };
}
