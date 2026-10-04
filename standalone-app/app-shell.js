import { WORKBENCH_CONFIG } from "./config.js";

const state={
  token:null,session:null,launch:null,projects:[],
  stateCertification:null,stateAuthority:null,error:null,online:false
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
      const v=await request("/standalone/v1/auth/session/verify",{method:"POST",auth:false,body:{token:stored}});
      state.token=stored;state.session=v.session;return;
    }catch(_e){sessionStorage.removeItem("scwb.session.token");}
  }
  const c=await request("/standalone/v1/auth/session/anonymous",{
    method:"POST",auth:false,body:{ttlSeconds:3600,clientLabel:"standalone-app"}
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

async function loadStateCertification(){
  const [cert,authority,probe]=await Promise.all([
    request("/standalone/v1/state-dependency/certification"),
    request("/standalone/v1/state-authority"),
    request("/standalone/v1/state-dependency/session-probe")
  ]);
  state.stateCertification=cert;
  state.stateAuthority=authority.authority;
  if(!probe.ok) throw new Error("Standalone session authority probe failed.");
}

function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function nav(p){history.pushState({},"",p);render();}

function render(){
  const root=document.getElementById("sc-workbench-app");
  const path=currentPath();
  const passed=state.stateCertification?.certification==="pass";
  root.innerHTML=`
  <div class="sc-shell">
    <header class="sc-topbar">
      <div class="sc-brand">Sustainable Catalyst / Workbench</div>
      <div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.8.0 · ${passed?"WORDPRESS STATE: ELIMINATED":"STATE CHECK PENDING"}</div>
    </header>
    <div class="sc-main">
      <nav class="sc-nav">
        <a data-route="/calculator">Calculator</a>
        <a data-route="/workspace">Workspace</a>
        <a data-route="/graphs">Graphs</a>
        <a data-route="/history">History</a>
        <a data-route="/packages">Packages</a>
        <a data-route="/settings">Settings</a>
      </nav>
      <main class="sc-workspace">
        <section class="sc-hero">
          <div class="sc-kicker">WordPress state dependency elimination</div>
          <h1 class="sc-title">${path.slice(1)||"Calculator"}</h1>
          <p class="sc-copy">The v12 standalone path owns identity, projects, calculations, notebooks, history, reproducibility packages, views, and route state outside WordPress.</p>
        </section>
        <section class="sc-panel">
          <h3>State authority certification</h3>
          <pre>${JSON.stringify({
            certification:state.stateCertification?.certification||"pending",
            wordpressRequired:state.stateCertification?.wordpressRequired??false,
            checks:state.stateCertification?.checks||{},
            authorityHash:state.stateAuthority?.authorityManifestHash||null,
            launchSource:state.launch?.source||null
          },null,2)}</pre>
          ${state.error?`<p class="sc-error">${state.error}</p>`:""}
        </section>
      </main>
    </div>
    <footer class="sc-footer">Canonical state: standalone browser → FastAPI → SQLite · WordPress compatibility only</footer>
  </div>`;
  root.querySelectorAll("[data-route]").forEach(a=>a.addEventListener("click",()=>nav(a.dataset.route)));
}

async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await resolveLaunch();
    await bootstrapSession();
    await loadStateCertification();
  }catch(e){state.error=String(e);}
  render();
}
addEventListener("popstate",render);
bootstrap();
