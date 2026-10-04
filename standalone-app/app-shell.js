import { WORKBENCH_CONFIG } from "./config.js";
import { renderMathematicalViews } from "./math-renderer.js";

const state={token:null,session:null,projects:[],selectedProject:null,packages:[],selectedPackage:null,error:null,online:false};

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
    try{const v=await request("/standalone/v1/auth/session/verify",{method:"POST",auth:false,body:{token:stored}});state.token=stored;state.session=v.session;return;}catch(_e){sessionStorage.removeItem("scwb.session.token");}
  }
  const c=await request("/standalone/v1/auth/session/anonymous",{method:"POST",auth:false,body:{ttlSeconds:3600,clientLabel:"standalone-app"}});
  state.token=c.token;state.session=c.session;sessionStorage.setItem("scwb.session.token",c.token);
}
async function loadProjects(){
  state.projects=(await request("/standalone/v1/projects")).projects||[];
  if(!state.selectedProject&&state.projects.length) state.selectedProject=state.projects[0].id;
}
async function loadPackages(projectId=state.selectedProject){
  if(!projectId){state.packages=[];return;}
  state.packages=(await request(`/standalone/v1/projects/${projectId}/reproducibility/packages`)).packages||[];
  state.selectedPackage=state.packages[0]||null;
}
async function createPackage(){
  if(!state.selectedProject) throw new Error("Select a project first.");
  const expression=prompt("Expression for reproducibility package","2+3*4");
  if(!expression) return;
  await request("/standalone/v1/reproducibility/packages",{method:"POST",body:{
    projectId:state.selectedProject,
    title:`Package: ${expression}`,
    notes:"Created from standalone reproducibility browser",
    calculationRequest:{
      calculation:{operation:"evaluate",expression},
      requestedResultType:"numeric",
      requireVerification:true,
      requireProvenance:true
    }
  }});
  await loadPackages();render();
}
async function verifyPackage(id){
  const v=await request(`/standalone/v1/reproducibility/packages/${id}/verify`,{method:"POST",body:{}});
  alert(v.verified?"Package integrity verified.":"Package verification failed.");
  await loadPackages();render();
}
async function replayPackage(id){
  const r=await request(`/standalone/v1/reproducibility/packages/${id}/replay`,{method:"POST",body:{comparisonMode:"strict"}});
  alert(r.certificate?.reproducible?"Replay reproducible.":"Replay divergence detected.");
  await loadPackages();render();
}
function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function nav(p){history.pushState({},"",p);render();}
function packageView(){
  const p=state.selectedPackage;
  return `<section class="sc-panel" id="reproducibility-packages">
    <div class="sc-actions">
      <select id="package-project" class="sc-select">${state.projects.map(x=>`<option value="${x.id}" ${x.id===state.selectedProject?"selected":""}>${x.name}</option>`).join("")}</select>
      <button id="new-package" class="sc-button">New Package</button>
    </div>
    <div class="sc-grid" style="margin-top:16px">
      <div>
        <h3>Packages</h3>
        ${state.packages.length?state.packages.map(x=>`<button class="sc-button package-item" data-package="${x.id}" style="display:block;width:100%;margin-bottom:8px;text-align:left">${x.title}<br><small>${x.lastReplayStatus||"never replayed"}</small></button>`).join(""):"<p>No packages yet.</p>"}
      </div>
      <div>
        <h3>Inspector</h3>
        ${p?`<div class="sc-result"><strong>${p.title}</strong><pre>${JSON.stringify({
          envelopeHash:p.envelopeHash,
          requestHash:p.requestHash,
          runtimeManifestHash:p.runtimeManifestHash,
          sourceCalculationObjectHash:p.sourceCalculationObjectHash,
          lastReplayStatus:p.lastReplayStatus,
          envelope:p.envelope
        },null,2)}</pre><div class="sc-actions"><button class="sc-button" id="verify-package">Verify</button><button class="sc-button sc-button-primary" id="replay-package">Replay</button></div></div>`:"<p>Select a package.</p>"}
      </div>
    </div>
  </section>`;
}
function render(){
  const root=document.getElementById("sc-workbench-app"),path=currentPath();
  root.innerHTML=`<div class="sc-shell"><header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.6.0</div></header><div class="sc-main"><nav class="sc-nav"><a data-route="/calculator">Calculator</a><a data-route="/workspace">Workspace</a><a data-route="/graphs">Graphs</a><a data-route="/history">History</a><a data-route="/packages" ${path==="/packages"?'aria-current="page"':""}>Packages</a><a data-route="/settings">Settings</a></nav><main class="sc-workspace"><section class="sc-hero"><div class="sc-kicker">Reproducibility package browser</div><h1 class="sc-title">${path==="/packages"?"Packages":"Workbench"}</h1><p class="sc-copy">Inspect replay envelopes, runtime manifests, provenance hashes, integrity checks, and deterministic replay certificates directly in the standalone Workbench.</p></section>${path==="/packages"?packageView():"<section class='sc-panel'><p>Use Packages to inspect reproducible calculations.</p></section>"}</main></div><footer class="sc-footer">Replay authority: v11.17 · package index: v12 SQLite · WordPress optional</footer></div>`;
  root.querySelectorAll("[data-route]").forEach(a=>a.addEventListener("click",()=>nav(a.dataset.route)));
  root.querySelector("#package-project")?.addEventListener("change",async e=>{state.selectedProject=e.target.value;await loadPackages();render();});
  root.querySelector("#new-package")?.addEventListener("click",async()=>{try{await createPackage();}catch(e){state.error=String(e);}});
  root.querySelectorAll(".package-item").forEach(b=>b.addEventListener("click",()=>{state.selectedPackage=state.packages.find(x=>x.id===b.dataset.package);render();}));
  root.querySelector("#verify-package")?.addEventListener("click",()=>verifyPackage(state.selectedPackage.id));
  root.querySelector("#replay-package")?.addEventListener("click",()=>replayPackage(state.selectedPackage.id));
}
async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await bootstrapSession();await loadProjects();await loadPackages();
  }catch(e){state.error=String(e);}
  render();
}
addEventListener("popstate",render);
bootstrap();
