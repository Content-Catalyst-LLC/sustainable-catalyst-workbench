import { WORKBENCH_CONFIG } from "./config.js";
import { renderMathematicalViews } from "./math-renderer.js";

const state={token:null,session:null,projects:[],selectedProject:null,notebooks:[],history:null,timeline:null,result:null,graph:null,error:null,online:false};

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
async function loadHistory(projectId=state.selectedProject){
  if(!projectId){state.history=null;state.timeline=null;state.notebooks=[];return;}
  const [h,t,n]=await Promise.all([
    request(`/standalone/v1/projects/${projectId}/history`),
    request(`/standalone/v1/projects/${projectId}/timeline`),
    request(`/standalone/v1/projects/${projectId}/notebooks`)
  ]);
  state.history=h.history;state.timeline=t.timeline;state.notebooks=n.notebooks||[];
}
async function createNotebook(){
  if(!state.selectedProject) throw new Error("Select a project first.");
  const title=prompt("Notebook title","Research Notebook");
  if(!title) return;
  await request("/standalone/v1/notebooks",{method:"POST",body:{projectId:state.selectedProject,title}});
  await loadHistory();render();
}
function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function nav(path){history.pushState({},"",path);render();}
function calculatorView(){return `<section class="sc-panel"><div class="sc-grid"><div class="sc-field"><label>Expression</label><textarea id="calculator-expression" class="sc-textarea">x**2-1</textarea></div><div class="sc-field"><label>Project</label><select id="calculator-project" class="sc-select"><option value="">Not selected</option>${state.projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join("")}</select></div></div><div class="sc-actions"><button id="calculator-run" class="sc-button sc-button-primary">Run</button><button id="calculator-graph" class="sc-button">Graph</button></div><div id="mathematical-views" class="math-view-grid"></div></section>`;}
async function runCalc(){
  try{
    const expression=document.querySelector("#calculator-expression").value.trim();
    const projectId=document.querySelector("#calculator-project").value||null;
    state.result=await request("/standalone/v1/calculator/execute",{method:"POST",body:{
      calculationRequest:{calculation:{operation:"evaluate",expression},requestedResultType:"numeric",preferredRuntime:"auto",requireVerification:true,requireProvenance:true},
      projectId,saveResult:Boolean(projectId),title:"Calculation",tags:[],metadata:{}
    }});
    if(projectId){state.selectedProject=projectId;await loadHistory(projectId);}
  }catch(e){state.error=String(e);}
  render();
}
async function graphCalc(){
  try{
    const expression=document.querySelector("#calculator-expression").value.trim();
    state.graph=await request("/standalone/v1/renderer/view-spec",{method:"POST",body:{graphing:{operation:"linked-function-study",expression,variable:"x",domain:[-10,10],samples:401,includeDerivative:true,includeRoots:true,includeCriticalPoints:true}}});
  }catch(e){state.error=String(e);}
  render();
}
function historyView(){
  return `<section class="sc-panel" id="notebook-history">
    <div class="sc-actions">
      <select id="history-project" class="sc-select">${state.projects.map(p=>`<option value="${p.id}" ${p.id===state.selectedProject?"selected":""}>${p.name}</option>`).join("")}</select>
      <button id="new-notebook" class="sc-button">New Notebook</button>
    </div>
    <h3>Notebooks</h3>
    ${state.notebooks.length?state.notebooks.map(n=>`<div class="sc-project-row"><strong>${n.title}</strong><br><small>${n.id}</small></div>`).join(""):"<p>No notebooks yet.</p>"}
    <h3>Calculation History</h3>
    ${state.history?.items?.length?state.history.items.map(i=>`<div class="sc-project-row"><strong>${i.title}</strong><br><small>${i.calculationObjectHash}</small></div>`).join(""):"<p>No saved calculations yet.</p>"}
    <h3>Project Timeline</h3>
    ${state.timeline?.items?.length?state.timeline.items.map(i=>`<div class="sc-project-row"><strong>${i.kind}</strong> · ${i.title||i.notebookTitle||""}<br><small>${i.createdAt||""}</small></div>`).join(""):"<p>No timeline entries yet.</p>"}
  </section>`;
}
function render(){
  const root=document.getElementById("sc-workbench-app"),path=currentPath();
  root.innerHTML=`<div class="sc-shell"><header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.5.0</div></header><div class="sc-main"><nav class="sc-nav"><a data-route="/calculator" ${path==="/calculator"?'aria-current="page"':""}>Calculator</a><a data-route="/workspace">Workspace</a><a data-route="/graphs">Graphs</a><a data-route="/history" ${path==="/history"?'aria-current="page"':""}>History</a><a data-route="/settings">Settings</a></nav><main class="sc-workspace"><section class="sc-hero"><div class="sc-kicker">Notebook & calculation history</div><h1 class="sc-title">${path==="/history"?"History":"Calculator"}</h1><p class="sc-copy">Persistent project notebooks, calculation history, and project timelines now live in the standalone Workbench store.</p></section>${path==="/history"?historyView():calculatorView()}</main></div><footer class="sc-footer">Notebooks + history: FastAPI/SQLite · WordPress optional</footer></div>`;
  root.querySelectorAll("[data-route]").forEach(a=>a.addEventListener("click",()=>nav(a.dataset.route)));
  root.querySelector("#calculator-run")?.addEventListener("click",runCalc);
  root.querySelector("#calculator-graph")?.addEventListener("click",graphCalc);
  root.querySelector("#new-notebook")?.addEventListener("click",async()=>{try{await createNotebook();}catch(e){state.error=String(e);render();}});
  root.querySelector("#history-project")?.addEventListener("change",async e=>{state.selectedProject=e.target.value;await loadHistory();render();});
  if(state.graph&&document.querySelector("#mathematical-views")) renderMathematicalViews(document.querySelector("#mathematical-views"),state.graph.viewSpec);
}
async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await bootstrapSession();await loadProjects();await loadHistory();
  }catch(e){state.error=String(e);}
  render();
}
addEventListener("popstate",render);
bootstrap();
