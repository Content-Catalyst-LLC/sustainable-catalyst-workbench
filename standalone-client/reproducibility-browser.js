export class StandaloneReproducibilityBrowserClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){if(!this.session?.token) throw new Error("Workbench session required");return {"Authorization":`Bearer ${this.session.token}`};}
  createPackage(payload){return this.api.request("/standalone/v1/reproducibility/packages",{method:"POST",headers:this.headers(),body:payload});}
  listPackages(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/reproducibility/packages`,{headers:this.headers()});}
  getPackage(id){return this.api.request(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}`,{headers:this.headers()});}
  verifyPackage(id){return this.api.request(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}/verify`,{method:"POST",headers:this.headers(),body:{}});}
  replayPackage(id,comparisonMode="strict"){return this.api.request(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}/replay`,{method:"POST",headers:this.headers(),body:{comparisonMode}});}
  deletePackage(id){return this.api.request(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}`,{method:"DELETE",headers:this.headers()});}
}
