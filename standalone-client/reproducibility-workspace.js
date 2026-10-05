export class ReproducibilityWorkspaceClient{
  constructor(api){this.api=api;}
  list(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/reproducibility/workspace`);}
  get(id){return this.api.request(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(id)}`);}
  update(id,body){return this.api.request(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(id)}`,{method:"PATCH",body});}
  verify(id){return this.api.request(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(id)}/verify`,{method:"POST"});}
  replay(id,comparisonMode="strict"){return this.api.request(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(id)}/replay`,{method:"POST",body:{comparisonMode}});}
  exportPath(id){return `/standalone/v1/reproducibility/workspace/${encodeURIComponent(id)}/export`;}
}
