export class ComputationalWorkflowClient{
  constructor(api){this.api=api;}
  contract(){return this.api.request('/standalone/v1/workflows/contract');}
  compose(payload){return this.api.request('/standalone/v1/workflows/compose',{method:'POST',body:payload});}
  validate(workflow){return this.api.request('/standalone/v1/workflows/validate',{method:'POST',body:workflow});}
  execute(workflow){return this.api.request('/standalone/v1/workflows/execute',{method:'POST',body:{workflow}});}
}
