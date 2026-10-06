export class NaturalLanguageComputationClient{
  constructor(api){this.api=api;}
  contract(){return this.api.request("/standalone/v1/natural-language/contract");}
  interpret(text){return this.api.request("/standalone/v1/natural-language/interpret",{method:"POST",body:{text,mode:"conservative"}});}
}
