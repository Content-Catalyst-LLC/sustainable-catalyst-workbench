export class StandaloneDeepLinkClient {
  constructor(api){this.api=api;}
  config(){return this.api.request("/standalone/v1/launch/config");}
  createLaunch(payload){return this.api.request("/standalone/v1/launch",{method:"POST",body:payload});}
  validateLaunch(token){return this.api.request("/standalone/v1/launch/validate",{method:"POST",body:{token}});}
  parseLaunchToken(url=globalThis.location?.href||""){
    try{return new URL(url).searchParams.get("launch");}catch(_e){return null;}
  }
}
