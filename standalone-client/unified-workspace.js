export class UnifiedWorkspaceClient{
  constructor(api){this.api=api;}
  project(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/unified-workspace`);}
  session(sessionId){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(sessionId)}/unified-workspace`);}
  handoff(projectId,body){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/unified-workspace/handoff`,{method:"POST",body});}
  contract(){return this.api.request("/standalone/v1/unified-workspace/contract");}
}
