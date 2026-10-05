export class CalculationPresentationClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){if(!this.session?.token)throw new Error("Workbench session required");return {"Authorization":`Bearer ${this.session.token}`};}
  experienceContract(){return this.api.request("/standalone/v1/calculator/experience-contract");}
  present(calculationObject,options={}){return this.api.request("/standalone/v1/calculator/presentation",{method:"POST",headers:this.headers(),body:{calculationObject,title:options.title||"Calculation",saved:Boolean(options.saved),savedCalculationId:options.savedCalculationId||null}});}
}
