export class ProductionCertificationClient{
  constructor(api){this.api=api;}
  status(){return this.api.request('/v13120/status',{auth:false});}
  report(){return this.api.request('/standalone/v1/certification/v13/report');}
}
