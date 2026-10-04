export class StandaloneCalculatorWorkspaceClient {
  constructor(api, sessionClient) {
    this.api = api;
    this.session = sessionClient;
  }

  headers() {
    if (!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization":`Bearer ${this.session.token}`};
  }

  config() {
    return this.api.request("/standalone/v1/calculator/config",{
      headers:this.headers()
    });
  }

  execute(calculationRequest, options={}) {
    return this.api.request("/standalone/v1/calculator/execute",{
      method:"POST",
      headers:this.headers(),
      body:{
        calculationRequest,
        projectId:options.projectId || null,
        saveResult:Boolean(options.saveResult),
        title:options.title || "Calculation",
        tags:options.tags || [],
        metadata:options.metadata || {}
      }
    });
  }

  executeAndSave(calculationRequest, projectId, options={}) {
    if (!projectId) throw new Error("projectId required");
    return this.execute(calculationRequest,{
      ...options,
      projectId,
      saveResult:true
    });
  }
}
