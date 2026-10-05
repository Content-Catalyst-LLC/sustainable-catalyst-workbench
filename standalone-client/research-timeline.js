export class ResearchTimelineClient{
  constructor(api){this.api=api;}
  project(projectId,kinds=""){const q=kinds?`?kinds=${encodeURIComponent(kinds)}`:"";return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/research-timeline${q}`);}
  session(sessionId,kinds=""){const q=kinds?`?kinds=${encodeURIComponent(kinds)}`:"";return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(sessionId)}/timeline${q}`);}
  notebookEntries(notebookId){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(notebookId)}/research-entries`);}
  note(notebookId,body){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(notebookId)}/structured-notes`,{method:"POST",body});}
  attach(notebookId,body){return this.api.request(`/standalone/v1/notebooks/${encodeURIComponent(notebookId)}/attach`,{method:"POST",body});}
}
