export class GraphStudioClient{
  constructor(api){this.api=api;}
  create(body){return this.api.request("/standalone/v1/graph-studio/graphs",{method:"POST",body});}
  list(projectId){return this.api.request(`/standalone/v1/projects/${encodeURIComponent(projectId)}/graphs`);}
  get(id){return this.api.request(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(id)}`);}
  update(id,body){return this.api.request(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(id)}`,{method:"PATCH",body});}
  remove(id){return this.api.request(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(id)}`,{method:"DELETE"});}
  annotate(id,body){return this.api.request(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(id)}/annotations`,{method:"POST",body});}
  render(id){return this.api.request(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(id)}/render`,{method:"POST"});}
}
