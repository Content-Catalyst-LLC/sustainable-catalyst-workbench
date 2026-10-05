export class StandaloneDeploymentHealthClient {
  constructor(api){this.api=api;}
  deploymentContract(){return this.api.request("/standalone/v1/interface/deployment-contract");}
  hardeningReadiness(){return this.api.request("/standalone/v1/interface/hardening-readiness");}
  async frontendVersion(url="/version.json"){
    const r=await fetch(url,{cache:"no-store"});
    if(!r.ok) throw new Error(`Frontend version probe failed: HTTP ${r.status}`);
    return r.json();
  }
  async compareVersions(url="/version.json"){
    const [front,back]=await Promise.all([this.frontendVersion(url),this.hardeningReadiness()]);
    return {ok:front.version===back.version,frontendVersion:front.version,backendVersion:back.version,hardeningReady:Boolean(back.hardeningReady)};
  }
}
