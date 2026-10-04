export class StandaloneNotebookHistoryClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){if(!this.session?.token) throw new Error("Workbench session required");return {"Authorization":`Bearer ${this.session.token}`};}
  createNotebook(payload){return this.api.request("/standalone/v1/notebooks",{method:"POST",headers:this.headers(),body:payload});}
  listNotebooks(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/notebooks`,{headers:this.headers()});}
  updateNotebook(id,patch){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(id)}`,{method:"PATCH",headers:this.headers(),body:patch});}
  deleteNotebook(id){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(id)}`,{method:"DELETE",headers:this.headers()});}
  addEntry(notebookId,payload){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(notebookId)}/entries`,{method:"POST",headers:this.headers(),body:payload});}
  listEntries(notebookId){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(notebookId)}/entries`,{headers:this.headers()});}
  updateEntry(id,patch){return this.api.request(`/standalone/v1/notebook-entries/${encodeURIComponent(id)}`,{method:"PATCH",headers:this.headers(),body:patch});}
  deleteEntry(id){return this.api.request(`/standalone/v1/notebook-entries/${encodeURIComponent(id)}`,{method:"DELETE",headers:this.headers()});}
  projectHistory(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/history`,{headers:this.headers()});}
  projectTimeline(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/timeline`,{headers:this.headers()});}
}
