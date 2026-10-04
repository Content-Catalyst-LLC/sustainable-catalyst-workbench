export class StandaloneMigrationCertificationClient {
  constructor(api, sessionClient) {
    this.api = api;
    this.session = sessionClient;
  }
  headers() {
    if (!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization": `Bearer ${this.session.token}`};
  }
  status() {
    return this.api.request("/v1290/status");
  }
  certification() {
    return this.api.request("/standalone/v1/migration/certification");
  }
  capabilityMatrix() {
    return this.api.request("/standalone/v1/migration/capability-matrix");
  }
  runbook() {
    return this.api.request("/standalone/v1/migration/runbook");
  }
  sessionProbe() {
    return this.api.request("/standalone/v1/migration/session-probe", {
      headers: this.headers()
    });
  }
}
