export class DomainCalculatorClient{
  constructor(api){this.api=api;} contract(){return this.api.request("/standalone/v1/domain-calculators/contract");} domains(){return this.api.request("/standalone/v1/domain-calculators/domains");}
  registry(domain=null,q=null){const p=new URLSearchParams();if(domain)p.set("domain",domain);if(q)p.set("q",q);const s=p.toString()?`?${p}`:"";return this.api.request(`/standalone/v1/domain-calculators/registry${s}`);}
  template(id){return this.api.request(`/standalone/v1/domain-calculators/templates/${encodeURIComponent(id)}`);} instantiate(id,values,metadata={}){return this.api.request(`/standalone/v1/domain-calculators/templates/${encodeURIComponent(id)}/instantiate`,{method:"POST",body:{values,metadata}});}
}
