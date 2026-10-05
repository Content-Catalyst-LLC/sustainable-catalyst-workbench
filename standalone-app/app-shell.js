import { WORKBENCH_CONFIG } from "./config.js";
import { renderViewSpec } from "./math-renderer.js";

const API=WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"");
const state={
  token:null,session:null,online:false,route:"calculator",
  projects:[],projectId:null,calculations:[],notebooks:[],notebookId:null,
  history:[],timeline:[],packages:[],lastCalculation:null,lastRequest:null,lastViewSpec:null,
  message:null,error:null,capabilities:null
};

function pathRoute(){
  const p=location.pathname.replace(/^\/+/,"").split("/")[0]||"calculator";
  return ["calculator","workspace","graphs","history","packages","settings"].includes(p)?p:"calculator";
}
state.route=pathRoute();

async function api(path,options={}){
  const headers={"Accept":"application/json","Content-Type":"application/json",...(options.headers||{})};
  if(state.token&&options.auth!==false) headers.Authorization=`Bearer ${state.token}`;
  const init={method:options.method||"GET",headers};
  if(options.body!==undefined) init.body=JSON.stringify(options.body);
  const r=await fetch(API+path,init);
  const d=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(typeof d.detail==="string"?d.detail:JSON.stringify(d.detail||d||{status:r.status}));
  return d;
}

async function bootstrapSession(){
  const stored=sessionStorage.getItem("scwb.session.token");
  if(stored){
    try{
      const v=await api("/standalone/v1/auth/session/verify",{method:"POST",auth:false,body:{token:stored}});
      state.token=stored; state.session=v.session||v.data?.session||v; return;
    }catch(_e){ sessionStorage.removeItem("scwb.session.token"); }
  }
  const d=await api("/standalone/v1/auth/session/anonymous",{method:"POST",auth:false,body:{ttlSeconds:3600,clientLabel:"v13-functional-standalone"}});
  state.token=d.token||d.data?.token;
  state.session=d.session||d.data?.session||d;
  sessionStorage.setItem("scwb.session.token",state.token);
}

async function loadProjects(){
  const d=await api("/standalone/v1/projects");
  state.projects=d.projects||[];
  if(!state.projectId&&state.projects.length) state.projectId=state.projects[0].id;
  if(state.projectId&&!state.projects.some(x=>x.id===state.projectId)) state.projectId=state.projects[0]?.id||null;
}

async function loadProjectData(){
  if(!state.projectId){state.calculations=[];state.notebooks=[];state.history=[];state.timeline=[];state.packages=[];return;}
  const id=encodeURIComponent(state.projectId);
  const [c,n,h,t,p]=await Promise.all([
    api(`/standalone/v1/projects/${id}/calculations`),
    api(`/standalone/v1/projects/${id}/notebooks`),
    api(`/standalone/v1/projects/${id}/history`),
    api(`/standalone/v1/projects/${id}/timeline`),
    api(`/standalone/v1/projects/${id}/reproducibility/packages`)
  ]);
  state.calculations=c.calculations||[];
  state.notebooks=n.notebooks||[];
  state.history=h.history||[];
  state.timeline=t.timeline||[];
  state.packages=p.packages||[];
  if(!state.notebookId&&state.notebooks.length) state.notebookId=state.notebooks[0].id;
}

function nav(route){
  state.route=route;
  history.pushState({}, "", route==="calculator"?"/calculator":`/${route}`);
  render();
}
window.addEventListener("popstate",()=>{state.route=pathRoute();render();});

function projectOptions(){
  return state.projects.map(p=>`<option value="${esc(p.id)}" ${p.id===state.projectId?"selected":""}>${esc(p.name)}</option>`).join("");
}
function esc(x){return String(x??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function fmt(x){return JSON.stringify(x,null,2);}
function toast(msg,error=false){state.message=error?null:msg;state.error=error?msg:null;render();setTimeout(()=>{state.message=null;state.error=null;render();},3500);}

function shell(content){
  const tabs=[["calculator","Calculator"],["workspace","Workspace"],["graphs","Graphs"],["history","History"],["packages","Packages"],["settings","Settings"]];
  return `<div class="sc-shell">
<header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · ${WORKBENCH_CONFIG.version} · STANDALONE</div></header>
<div class="sc-main">
<nav class="sc-nav">${tabs.map(([r,l])=>`<button data-nav="${r}" class="${state.route===r?"active":""}">${l}</button>`).join("")}</nav>
<main class="sc-workspace">${content}</main>
</div>
<footer class="sc-footer">Functional standalone Workbench · FastAPI authority · WordPress optional</footer>
${state.message?`<div class="sc-toast sc-success">${esc(state.message)}</div>`:""}
${state.error?`<div class="sc-toast sc-error">${esc(state.error)}</div>`:""}
</div>`;
}

function commonProjectBar(){
  return `<section class="sc-panel"><div class="sc-inline">
  <label>Project</label>
  <select id="project-select" class="sc-select" style="max-width:420px">${state.projects.length?projectOptions():'<option value="">No projects yet</option>'}</select>
  <button id="new-project" class="sc-button">New Project</button>
  <span class="sc-badge">${state.calculations.length} calculations</span>
  <span class="sc-badge">${state.notebooks.length} notebooks</span>
  <span class="sc-badge">${state.packages.length} packages</span>
  </div></section>`;
}

function calculatorView(){
  return `<div class="sc-kicker">Functional standalone interface</div><h1 class="sc-title">Calculator</h1>
  <p class="sc-copy">Execute canonical Workbench calculations directly against FastAPI. Save results into the selected project and reuse them across notebooks, history, graphs, and reproducibility packages.</p>
  ${commonProjectBar()}
  <section class="sc-panel"><div class="sc-grid">
    <label class="sc-field sc-field-wide">Expression<textarea id="calc-expression" class="sc-textarea" placeholder="e.g. sin(x)^2 + cos(x)^2">2+3*4</textarea></label>
    <label class="sc-field">Operation<select id="calc-operation" class="sc-select"><option value="evaluate">Evaluate</option><option value="exact">Exact</option><option value="simplify">Simplify</option><option value="solve">Solve</option><option value="differentiate">Differentiate</option><option value="integrate-symbolic">Integrate</option><option value="root">Find Root</option></select></label>
    <label class="sc-field">Variable<input id="calc-variable" class="sc-input" value="x"></label>
    <label class="sc-field">Title<input id="calc-title" class="sc-input" value="Calculation"></label>
    <label class="sc-field"><span>Save result</span><select id="calc-save" class="sc-select"><option value="true">Yes</option><option value="false">No</option></select></label>
  </div>
  <div class="sc-actions"><button id="execute-calc" class="sc-button sc-button-primary">Execute</button><button id="graph-last" class="sc-button" ${state.lastCalculation?"":"disabled"}>Graph last expression</button></div>
  ${state.lastCalculation?`<div class="sc-result"><pre>${esc(fmt(state.lastCalculation))}</pre></div>`:""}</section>`;
}

function workspaceView(){
  return `<div class="sc-kicker">Persistent research state</div><h1 class="sc-title">Workspace</h1><p class="sc-copy">Manage projects, notebooks, saved calculations, and notebook entries.</p>
  ${commonProjectBar()}
  <section class="sc-panel"><h2>Notebooks</h2><div class="sc-actions"><button id="new-notebook" class="sc-button sc-button-primary" ${state.projectId?"":"disabled"}>Create Notebook</button></div>
  <div class="sc-list">${state.notebooks.map(n=>`<div class="sc-item"><strong>${esc(n.title)}</strong><span class="sc-muted">${esc(n.description||"")}</span><div class="sc-actions"><button class="sc-button open-notebook" data-id="${esc(n.id)}">Open</button></div></div>`).join("")||'<p class="sc-muted">No notebooks in this project.</p>'}</div></section>
  ${state.notebookId?`<section class="sc-panel"><h3>Notebook entries</h3><label class="sc-field"><span>Note</span><textarea id="notebook-note" class="sc-textarea" placeholder="Research note"></textarea></label><div class="sc-actions"><button id="add-note" class="sc-button">Add note</button>${state.calculations.length?`<button id="attach-calc" class="sc-button">Attach latest calculation</button>`:""}</div><div id="entries" class="sc-list"></div></section>`:""}
  <section class="sc-panel"><h2>Saved calculations</h2><div class="sc-list">${state.calculations.map(c=>`<div class="sc-item"><strong>${esc(c.title)}</strong><span class="sc-badge">${esc(c.id)}</span></div>`).join("")||'<p class="sc-muted">No saved calculations.</p>'}</div></section>`;
}

function graphsView(){
  return `<div class="sc-kicker">Renderer-neutral mathematical views</div><h1 class="sc-title">Graphs</h1><p class="sc-copy">Generate a backend-authoritative view specification and render it in the browser.</p>
  <section class="sc-panel"><div class="sc-grid">
  <label class="sc-field">Expression<input id="graph-expression" class="sc-input" value="sin(x)"></label>
  <label class="sc-field">Variable<input id="graph-variable" class="sc-input" value="x"></label>
  <label class="sc-field">Domain start<input id="graph-start" class="sc-input" type="number" value="-6.28" step="0.01"></label>
  <label class="sc-field">Domain end<input id="graph-end" class="sc-input" type="number" value="6.28" step="0.01"></label>
  </div><div class="sc-actions"><button id="render-graph" class="sc-button sc-button-primary">Render graph</button></div>
  <div id="graph-output" class="math-view-grid"></div>
  ${state.lastViewSpec?`<details class="sc-result"><summary>View specification</summary><pre>${esc(fmt(state.lastViewSpec))}</pre></details>`:""}</section>`;
}

function historyView(){
  return `<div class="sc-kicker">Project chronology</div><h1 class="sc-title">History</h1>${commonProjectBar()}
  <section class="sc-panel"><h2>Calculation history</h2><div class="sc-list">${state.history.map(x=>`<div class="sc-item"><strong>${esc(x.title||x.kind||"Calculation")}</strong><pre>${esc(fmt(x))}</pre></div>`).join("")||'<p class="sc-muted">No calculation history.</p>'}</div></section>
  <section class="sc-panel"><h2>Project timeline</h2><div class="sc-list">${state.timeline.map(x=>`<div class="sc-item"><pre>${esc(fmt(x))}</pre></div>`).join("")||'<p class="sc-muted">No timeline entries.</p>'}</div></section>`;
}

function packagesView(){
  return `<div class="sc-kicker">Reproducible computation</div><h1 class="sc-title">Packages</h1>${commonProjectBar()}
  <section class="sc-panel"><div class="sc-actions"><button id="create-package" class="sc-button sc-button-primary" ${state.projectId&&state.lastRequest?"":"disabled"}>Capture last calculation</button></div>
  <div class="sc-list">${state.packages.map(p=>`<div class="sc-item"><strong>${esc(p.title)}</strong><span class="sc-badge">${esc(p.id)}</span><div class="sc-actions"><button class="sc-button verify-package" data-id="${esc(p.id)}">Verify</button><button class="sc-button replay-package" data-id="${esc(p.id)}">Replay</button></div></div>`).join("")||'<p class="sc-muted">No reproducibility packages in this project.</p>'}</div></section>`;
}

function settingsView(){
  return `<div class="sc-kicker">Runtime</div><h1 class="sc-title">Settings</h1><section class="sc-panel"><pre>${esc(fmt({
    version:WORKBENCH_CONFIG.version,apiBaseUrl:WORKBENCH_CONFIG.apiBaseUrl,
    session:state.session,capabilities:state.capabilities,projectId:state.projectId
  }))}</pre></section>`;
}

function render(){
  const root=document.getElementById("sc-workbench-app");
  const views={calculator:calculatorView,workspace:workspaceView,graphs:graphsView,history:historyView,packages:packagesView,settings:settingsView};
  root.innerHTML=shell((views[state.route]||calculatorView)());
  bind();
  if(state.route==="workspace"&&state.notebookId) loadEntries();
  if(state.route==="graphs"&&state.lastViewSpec) drawGraph();
}

function bind(){
  document.querySelectorAll("[data-nav]").forEach(b=>b.onclick=()=>nav(b.dataset.nav));
  const sel=document.getElementById("project-select");
  if(sel) sel.onchange=async()=>{state.projectId=sel.value||null;state.notebookId=null;await loadProjectData();render();};
  const np=document.getElementById("new-project"); if(np) np.onclick=createProject;
  const ex=document.getElementById("execute-calc"); if(ex) ex.onclick=executeCalculation;
  const gl=document.getElementById("graph-last"); if(gl) gl.onclick=()=>{nav("graphs");setTimeout(()=>{const x=document.getElementById("graph-expression");if(x&&state.lastRequest)x.value=state.lastRequest.calculation.expression||"";},0);};
  const ng=document.getElementById("render-graph"); if(ng) ng.onclick=renderGraph;
  const nn=document.getElementById("new-notebook"); if(nn) nn.onclick=createNotebook;
  document.querySelectorAll(".open-notebook").forEach(b=>b.onclick=async()=>{state.notebookId=b.dataset.id;render();});
  const an=document.getElementById("add-note"); if(an) an.onclick=addNote;
  const ac=document.getElementById("attach-calc"); if(ac) ac.onclick=attachCalculation;
  const cp=document.getElementById("create-package"); if(cp) cp.onclick=createPackage;
  document.querySelectorAll(".verify-package").forEach(b=>b.onclick=()=>verifyPackage(b.dataset.id));
  document.querySelectorAll(".replay-package").forEach(b=>b.onclick=()=>replayPackage(b.dataset.id));
}

async function createProject(){
  const name=prompt("Project name","Workbench Project"); if(!name)return;
  try{const d=await api("/standalone/v1/projects",{method:"POST",body:{name,description:"Created from Workbench v13.0 standalone interface",metadata:{interfaceVersion:"13.0.0"}}});state.projectId=d.project.id;await loadProjects();await loadProjectData();toast("Project created.");}catch(e){toast(String(e),true);}
}

async function executeCalculation(){
  try{
    const expression=document.getElementById("calc-expression").value.trim();
    const operation=document.getElementById("calc-operation").value;
    const variable=document.getElementById("calc-variable").value.trim()||"x";
    const title=document.getElementById("calc-title").value.trim()||"Calculation";
    const saveResult=document.getElementById("calc-save").value==="true";
    if(saveResult&&!state.projectId) throw new Error("Create or select a project before saving.");
    const calculation={operation,expression};
    if(["solve","differentiate","integrate-symbolic","root"].includes(operation)) calculation.variable=variable;
    const resultType=["evaluate","root"].includes(operation)?"numeric":operation==="exact"?"exact":"symbolic";
    const calculationRequest={calculation,requestedResultType:resultType,requireVerification:true,requireProvenance:true};
    state.lastRequest=calculationRequest;
    const d=await api("/standalone/v1/calculator/execute",{method:"POST",body:{calculationRequest,projectId:state.projectId,saveResult,title,tags:["standalone-v13"],metadata:{interfaceVersion:"13.0.0"}}});
    state.lastCalculation=d.calculationObject;
    await loadProjectData();
    toast(saveResult?"Calculation executed and saved.":"Calculation executed.");
  }catch(e){toast(String(e),true);}
}

async function renderGraph(){
  try{
    const expression=document.getElementById("graph-expression").value.trim();
    const variable=document.getElementById("graph-variable").value.trim()||"x";
    const a=Number(document.getElementById("graph-start").value),b=Number(document.getElementById("graph-end").value);
    const graphing={operation:"function-plot",expression,variable,domain:[a,b],samples:401,includeRoots:true,includeCriticalPoints:true,includeDerivative:false,includeIntegral:false};
    const d=await api("/standalone/v1/renderer/view-spec",{method:"POST",body:{graphing}});
    state.lastViewSpec=d.viewSpec||d.views||d;
    render(); drawGraph();
  }catch(e){toast(String(e),true);}
}
function drawGraph(){
  const target=document.getElementById("graph-output"); if(!target||!state.lastViewSpec)return;
  try{renderViewSpec(target,state.lastViewSpec);}catch(e){target.innerHTML=`<div class="sc-error">${esc(e)}</div>`;}
}

async function createNotebook(){
  const title=prompt("Notebook title","Research Notebook"); if(!title||!state.projectId)return;
  try{const d=await api("/standalone/v1/notebooks",{method:"POST",body:{projectId:state.projectId,title,description:"",metadata:{interfaceVersion:"13.0.0"}}});state.notebookId=d.notebook.id;await loadProjectData();toast("Notebook created.");}catch(e){toast(String(e),true);}
}
async function loadEntries(){
  const target=document.getElementById("entries"); if(!target||!state.notebookId)return;
  try{const d=await api(`/standalone/v1/notebooks/${encodeURIComponent(state.notebookId)}/entries`);target.innerHTML=(d.entries||[]).map(e=>`<div class="sc-item"><span class="sc-badge">${esc(e.kind)}</span><pre>${esc(e.markdown||"")}</pre></div>`).join("")||'<p class="sc-muted">No entries.</p>';}catch(e){target.innerHTML=`<p class="sc-error">${esc(e)}</p>`;}
}
async function addNote(){
  const markdown=document.getElementById("notebook-note").value;
  if(!markdown.trim())return;
  try{await api(`/standalone/v1/notebooks/${encodeURIComponent(state.notebookId)}/entries`,{method:"POST",body:{kind:"note",markdown,pinned:false,metadata:{interfaceVersion:"13.0.0"}}});document.getElementById("notebook-note").value="";await loadEntries();toast("Note added.");}catch(e){toast(String(e),true);}
}
async function attachCalculation(){
  const c=state.calculations[0]; if(!c)return;
  try{await api(`/standalone/v1/notebooks/${encodeURIComponent(state.notebookId)}/entries`,{method:"POST",body:{kind:"calculation-reference",markdown:`Calculation: ${c.title}`,savedCalculationId:c.id,pinned:false,metadata:{interfaceVersion:"13.0.0"}}});await loadEntries();toast("Calculation attached.");}catch(e){toast(String(e),true);}
}
async function createPackage(){
  if(!state.projectId||!state.lastRequest)return;
  try{
    await api("/standalone/v1/reproducibility/packages",{method:"POST",body:{projectId:state.projectId,calculationRequest:state.lastRequest,calculationObject:state.lastCalculation,title:"Workbench v13 Reproducibility Package",notes:"Captured from functional standalone interface",metadata:{interfaceVersion:"13.0.0"}}});
    await loadProjectData();toast("Reproducibility package created.");
  }catch(e){toast(String(e),true);}
}
async function verifyPackage(id){try{const d=await api(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}/verify`,{method:"POST",body:{}});toast(`Verification: ${d.verification?.valid??d.ok}`);}catch(e){toast(String(e),true);}}
async function replayPackage(id){try{const d=await api(`/standalone/v1/reproducibility/packages/${encodeURIComponent(id)}/replay`,{method:"POST",body:{comparisonMode:"strict"}});toast(`Replay: ${d.replay?.reproducible??d.ok}`);}catch(e){toast(String(e),true);}}

async function resolveLaunch(){
  try{
    const token=new URL(location.href).searchParams.get("launch"); if(!token)return;
    const d=await api("/standalone/v1/launch/validate",{method:"POST",auth:false,body:{token}});
    const launch=d.launch||d.descriptor||d;
    if(launch.targetType==="project"&&launch.targetId) state.projectId=launch.targetId;
    if(launch.route) state.route=launch.route.replace(/^\//,"")||"calculator";
  }catch(e){state.error=`Launch token: ${e}`;}
}

async function bootstrap(){
  try{
    state.online=Boolean((await api("/health",{auth:false})).ok);
    await bootstrapSession();
    await resolveLaunch();
    const c=await api("/standalone/v1/interface/capabilities");
    state.capabilities=c.capabilities;
    await loadProjects();
    await loadProjectData();
  }catch(e){state.error=String(e);}
  render();
}
bootstrap();
