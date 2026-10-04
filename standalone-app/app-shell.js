import { WORKBENCH_CONFIG } from "./config.js";

const state={
  token:null,session:null,launch:null,
  migrationCertification:null,capabilityMatrix:null,runbook:null,
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

async function resolveLaunch(){
  const token=new URL(location.href).searchParams.get("launch");
  if(!token) return;
  const v=await request("/standalone/v1/launch/validate",{
    method:"POST",auth:false,body:{token}
  });
  state.launch=v.launchDescriptor;
}

async function loadMigrationCertification(){
  const [cert,matrix,runbook,probe]=await Promise.all([
    request("/standalone/v1/migration/certification"),
    request("/standalone/v1/migration/capability-matrix"),
    request("/standalone/v1/migration/runbook"),
    request("/standalone/v1/migration/session-probe"),
  ]);
  state.migrationCertification=cert;
  state.capabilityMatrix=matrix.matrix;
  state.runbook=runbook.runbook;
  if(!probe.ok) throw new Error("Standalone migration session probe failed.");
}

function render(){
  const root=document.getElementById("sc-workbench-app");
  const passed=state.migrationCertification?.certification==="pass";
  const rows=state.capabilityMatrix?.capabilities||[];

  root.innerHTML=`
  <div class="sc-shell">
    <header class="sc-topbar">
      <div class="sc-brand">Sustainable Catalyst / Workbench</div>
      <div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.9.0 · ${passed?"MIGRATION CERTIFIED":"CERTIFICATION PENDING"}</div>
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
          <div class="sc-kicker">Standalone migration certification</div>
          <h1 class="sc-title">${passed?"Migration Certified":"Migration Certification"}</h1>
          <p class="sc-copy">The v12 application path is certified to operate with standalone browser state, FastAPI authority, and persistent SQLite research state while WordPress remains optional.</p>
        </section>
        <section class="sc-panel">
          <h3>Certification</h3>
          <pre>${JSON.stringify({
            certification:state.migrationCertification?.certification||"pending",
            migrationReady:state.migrationCertification?.migrationReady||false,
            wordpressRequired:state.migrationCertification?.wordpressRequired??false,
            canonicalApplication:state.migrationCertification?.canonicalApplication||null,
            canonicalBackend:state.migrationCertification?.canonicalBackend||null,
            canonicalPersistentState:state.migrationCertification?.canonicalPersistentState||null,
          },null,2)}</pre>
        </section>
        <section class="sc-panel">
          <h3>Capability Matrix</h3>
          ${rows.map(r=>`<div class="sc-project-row"><strong>${r.capability}</strong> · ${r.migrationReady?"ready":"not ready"}<br><small>${r.standaloneAuthority} · WordPress required: ${r.wordpressRequired}</small></div>`).join("")||"<p>Loading…</p>"}
        </section>
        ${state.error?`<section class="sc-panel"><p class="sc-error">${state.error}</p></section>`:""}
      </main>
    </div>
    <footer class="sc-footer">v12 migration boundary certified · WordPress optional · v12.10 production consolidation next</footer>
  </div>`;
}

async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await resolveLaunch();
    await bootstrapSession();
    await loadMigrationCertification();
  }catch(e){
    state.error=String(e);
  }
  render();
}
bootstrap();
