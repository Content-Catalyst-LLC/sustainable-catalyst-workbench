export class StandaloneProjectStoreClient {
  constructor(api, sessionClient) {
    this.api = api;
    this.session = sessionClient;
  }

  headers() {
    if (!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization":`Bearer ${this.session.token}`};
  }

  storeStatus() {
    return this.api.request("/standalone/v1/store/status",{headers:this.headers()});
  }

  createProject(project) {
    return this.api.request("/standalone/v1/projects",{
      method:"POST",headers:this.headers(),body:project
    });
  }

  listProjects() {
    return this.api.request("/standalone/v1/projects",{headers:this.headers()});
  }

  getProject(projectId) {
    return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}`,{
      headers:this.headers()
    });
  }

  updateProject(projectId, patch) {
    return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}`,{
      method:"PATCH",headers:this.headers(),body:patch
    });
  }

  deleteProject(projectId) {
    return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}`,{
      method:"DELETE",headers:this.headers()
    });
  }

  saveCalculation(payload) {
    return this.api.request("/standalone/v1/calculations",{
      method:"POST",headers:this.headers(),body:payload
    });
  }

  listCalculations(projectId) {
    return this.api.request(
      `/standalone/v1/projects/${encodeURIComponent(projectId)}/calculations`,
      {headers:this.headers()}
    );
  }

  getCalculation(calculationId) {
    return this.api.request(`/standalone/v1/calculations/${encodeURIComponent(calculationId)}`,{
      headers:this.headers()
    });
  }

  deleteCalculation(calculationId) {
    return this.api.request(`/standalone/v1/calculations/${encodeURIComponent(calculationId)}`,{
      method:"DELETE",headers:this.headers()
    });
  }
}
