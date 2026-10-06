export class IntentPlanningClient{
  constructor(api){this.api=api;}
  contract(){return this.api.request("/standalone/v1/intent-planning/contract");}
  plan(text){return this.api.request("/standalone/v1/intent-planning/plan",{method:"POST",body:{text,mode:"conservative"}});}
  validate(plan){return this.api.request("/standalone/v1/intent-planning/validate",{method:"POST",body:{plan}});}
  explain(plan,calculationObject){return this.api.request("/standalone/v1/intent-planning/explain",{method:"POST",body:{plan,calculationObject}});}
}
