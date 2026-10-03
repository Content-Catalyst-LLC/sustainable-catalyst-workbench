export async function loadStandaloneAppShell(api) {
  const [manifest, routes, shell] = await Promise.all([
    api.request("/standalone/v1/app-manifest"),
    api.request("/standalone/v1/app-routes"),
    api.request("/standalone/v1/app-shell")
  ]);
  return {
    manifest: manifest.data.manifest,
    routeRegistry: routes.data.routeRegistry,
    shell: shell.data.shell
  };
}

export function resolveStandaloneRoute(routeRegistry, pathname) {
  const exact = routeRegistry.routes.find(r => r.path === pathname && r.available);
  if (exact) return exact;
  return routeRegistry.routes.find(r => r.path === routeRegistry.unknownRouteFallback)
    || routeRegistry.routes.find(r => r.available)
    || null;
}
