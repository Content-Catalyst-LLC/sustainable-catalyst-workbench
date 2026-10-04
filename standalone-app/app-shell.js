import { WORKBENCH_CONFIG } from "./config.js";

const state={
  token:null,session:null,
  productionReadiness:null,
  productionCertification:null,
  deploymentManifest:null,
  error:null,online:false
};

async function request(path,options={}){
  const headers={"Accept":"application/json","Content-Type":"application/json",...(options.headers||{})};
  if(state.token&&options.auth!==false) headers.Authorization=`Bearer ${state.token}`;
  const init={method:options.method||"GET",headers};
  if(options.body!==undefined) init.body=JSON.stringify(options.body);
  const r=await fetch(WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"")+path,init);
  const d=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(d.detail||`HTTP ${r.status}`);
  return d;
}

async function bootstrapSession(){
  const stored=sessionStorage.getItem("scwb.session.token");
  if(stored){
    try{
      const v=await request("/standalone/v1/auth/session/verify",{
        method:"POST",auth:false,body:{token:stored}
      });
      state.token=stored;state.session=v.session;return;
    }catch(_e){
      sessionStorage.removeItem("scwb.session.token");
    }
  }
  const c=await request("/standalone/v1/auth/session/anonymous",{
    method:"POST",auth:false,
    body:{ttlSeconds:3600,clientLabel:"standalone-app"}
  });
  state.token=c.token;state.session=c.session;
  sessionStorage.setItem("scwb.session.token",c.token);
}

async function loadProductionReadiness(){
  const [readiness,certification,deployment,probe]=await Promise.all([
    request("/standalone/v1/production/readiness"),
    request("/standalone/v1/production/certification"),
    request("/standalone/v1/production/deployment-manifest"),
    request("/standalone/v1/production/session-probe"),
  ]);
  state.productionReadiness=readiness;
  state.productionCertification=certification;
  state.deploymentManifest=deployment.deployment;
  if(!probe.ok) throw new Error("Production standalone session probe failed.");
}

function render(){
  const root=document.getElementById("sc-workbench-app");
  const ready=state.productionReadiness?.productionReady===true;
  const remaining=state.productionReadiness?.remainingProductionActions||[];

  root.innerHTML=`
  <div class="sc-shell">
    <header class="sc-topbar">
      <div class="sc-brand">Sustainable Catalyst / Workbench</div>
      <div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.10.0 · ${ready?"PRODUCTION READY":"PRODUCTION CONFIG PENDING"}</div>
    </header>
    <div class="sc-main">
      <nav class="sc-nav">
        <a href="/calculator">Calculator</a>
        <a href="/workspace">Workspace</a>
        <a href="/graphs">Graphs</a>
        <a href="/history">History</a>
        <a href="/packages">Packages</a>
        <a href="/settings">Settings</a>
      </nav>
      <main class="sc-workspace">
        <section class="sc-hero">
          <div class="sc-kicker">WordPress-optional production Workbench</div>
          <h1 class="sc-title">${ready?"Production Ready":"Production Readiness"}</h1>
          <p class="sc-copy">Workbench v12 is consolidated as a standalone application with FastAPI authority and persistent v12 research state. WordPress remains optional.</p>
        </section>

        <section class="sc-panel">
          <h3>Production Certification</h3>
          <pre>${JSON.stringify({
            architectureCertification:state.productionCertification?.architectureCertification||"pending",
            productionEnvironmentCertification:state.productionCertification?.productionEnvironmentCertification||"pending",
            productionReady:state.productionCertification?.productionReady||false,
            wordpressRequired:state.productionCertification?.wordpressRequired??false,
            remainingProductionActions:remaining
          },null,2)}</pre>
        </section>

        <section class="sc-panel">
          <h3>Deployment</h3>
          <pre>${JSON.stringify({
            frontend:state.deploymentManifest?.frontend?.url||null,
            backend:state.deploymentManifest?.backend?.url||null,
            persistentState:state.deploymentManifest?.state?.path||null,
            wordpressRole:state.deploymentManifest?.wordpressRole||null
          },null,2)}</pre>
        </section>

        ${state.error?`<section class="sc-panel"><p class="sc-error">${state.error}</p></section>`:""}
      </main>
    </div>
    <footer class="sc-footer">v12 production consolidation · standalone canonical · WordPress optional</footer>
  </div>`;
}

async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await bootstrapSession();
    await loadProductionReadiness();
  }catch(e){
    state.error=String(e);
  }
  render();
}
bootstrap();
