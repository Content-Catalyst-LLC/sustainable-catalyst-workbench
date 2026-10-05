export class MathematicalNotationClient {
  constructor(api,sessionClient){this.api=api;this.session=sessionClient;}
  headers(){
    if(!this.session?.token) throw new Error("Workbench session required");
    return {"Authorization":`Bearer ${this.session.token}`};
  }
  contract(){return this.api.request("/standalone/v1/calculator/input-contract");}
  normalize(expression){
    return this.api.request("/standalone/v1/calculator/normalize",{
      method:"POST",
      headers:this.headers(),
      body:{expression,mode:"conservative"}
    });
  }
}
