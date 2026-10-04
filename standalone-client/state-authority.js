export class StandaloneStateAuthorityClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){
    if(!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization":`Bearer ${this.session.token}`};
  }
  authority(){
    return this.api.request("/standalone/v1/state-authority");
  }
  certification(){
    return this.api.request("/standalone/v1/state-dependency/certification");
  }
  wordpressPolicy(){
    return this.api.request("/standalone/v1/state-dependency/wordpress-policy");
  }
  sessionProbe(){
    return this.api.request("/standalone/v1/state-dependency/session-probe",{headers:this.headers()});
  }
}
