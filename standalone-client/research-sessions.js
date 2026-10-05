export class ResearchSessionsClient{
  constructor(api){this.api=api;}
  create(body){return this.api.request("/standalone/v1/research-sessions",{method:"POST",body});}
  list(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/research-sessions`);}
  get(id){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}`);}
  update(id,body){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}`,{method:"PATCH",body});}
  activate(id){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}/activate`,{method:"POST"});}
  summary(id){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}/summary`);}
  activity(id,limit=100){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}/activity?limit=${limit}`);}
  appendActivity(id,body){return this.api.request(`/standalone/v1/research-sessions/${encodeURIComponent(id)}/activity`,{method:"POST",body});}
}
