/**
 * Standalone dual-mode certification helper.
 *
 * This helper talks directly to FastAPI. It never requires WordPress.
 */
export async function certifyWorkbenchDualMode(api) {
  const [status, certification, routes, probe, config] = await Promise.all([
    api.request("/v10104/status"),
    api.request("/certification/dual-mode"),
    api.request("/certification/dual-mode/routes"),
    api.request("/certification/dual-mode/probe"),
    api.request("/standalone/v1/client/config"),
  ]);

  const passed =
    status.data.ok === true &&
    certification.data.certification === "pass" &&
    routes.data.ok === true &&
    probe.data.ok === true &&
    config.data.wordpressRequired === false;

  return {
    ok: passed,
    version: status.data.version,
    certification: certification.data,
    routes: routes.data,
    probe: probe.data,
    config: config.data,
  };
}
