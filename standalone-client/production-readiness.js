export class StandaloneProductionReadinessClient {
  constructor(api, sessionClient) {
    this.api = api;
    this.session = sessionClient;
  }
  headers() {
    if (!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization": `Bearer ${this.session.token}`};
  }
  status() {
    return this.api.request("/v12100/status");
  }
  deploymentManifest() {
    return this.api.request("/standalone/v1/production/deployment-manifest");
  }
  environment() {
    return this.api.request("/standalone/v1/production/environment");
  }
  certification() {
    return this.api.request("/standalone/v1/production/certification");
  }
  readiness() {
    return this.api.request("/standalone/v1/production/readiness");
  }
  sessionProbe() {
    return this.api.request("/standalone/v1/production/session-probe", {
      headers: this.headers()
    });
  }
}
