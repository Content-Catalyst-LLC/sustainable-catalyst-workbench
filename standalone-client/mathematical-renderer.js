export class StandaloneMathematicalRendererClient {
  constructor(api, sessionClient){ this.api=api; this.session=sessionClient; }
  headers(){
    if(!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization":`Bearer ${this.session.token}`};
  }
  config(){
    return this.api.request("/standalone/v1/renderer/config",{headers:this.headers()});
  }
  viewSpec(graphing){
    return this.api.request("/standalone/v1/renderer/view-spec",{
      method:"POST",headers:this.headers(),body:{graphing}
    });
  }
}
