export class FunctionalStandaloneInterfaceClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){if(!this.session?.token)throw new Error("Workbench session required");return {"Authorization":`Bearer ${this.session.token}`};}
  status(){return this.api.request("/v1300/status");}
  capabilities(){return this.api.request("/standalone/v1/interface/capabilities");}
  readiness(){return this.api.request("/standalone/v1/interface/readiness");}
  sessionProbe(){return this.api.request("/standalone/v1/interface/session-probe",{headers:this.headers()});}
}
