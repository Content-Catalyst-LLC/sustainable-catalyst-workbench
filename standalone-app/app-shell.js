import { WORKBENCH_CONFIG } from "./config.js";
import { renderMathematicalViews } from "./math-renderer.js";

const state={token:null,session:null,projects:[],result:null,graph:null,error:null,online:false};

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
async function loadProjects(){state.projects=(await request("/standalone/v1/projects")).projects||[];}
function calcRequest(){
  return {
    calculation:{
      operation:document.querySelector("#calculator-operation").value,
      expression:document.querySelector("#calculator-expression").value.trim(),
      variable:document.querySelector("#calculator-variable").value.trim()||undefined
    },
    requestedResultType:"auto",preferredRuntime:"auto",
    requireVerification:true,requireProvenance:true
  };
}
async function executeCalculator(saveResult=false){
  state.error=null;
  try{
    const projectId=document.querySelector("#calculator-project").value||null;
    if(saveResult&&!projectId) throw new Error("Select a project before saving.");
    state.result=await request("/standalone/v1/calculator/execute",{method:"POST",body:{
      calculationRequest:calcRequest(),projectId,saveResult,title:"Calculation",tags:[],metadata:{}
    }});
  }catch(e){state.error=String(e);}
  render();
}
async function requestGraphView(){
  state.error=null;
  try{
    const expression=document.querySelector("#calculator-expression").value.trim();
    const variable=document.querySelector("#calculator-variable").value.trim()||"x";
    state.graph=await request("/standalone/v1/renderer/view-spec",{method:"POST",body:{graphing:{
      operation:"linked-function-study",expression,variable,domain:[-10,10],samples:401,
      includeDerivative:true,includeIntegral:false,includeRoots:true,includeCriticalPoints:true
    }}});
  }catch(e){state.error=String(e);}
  render();
}
function render(){
  const root=document.getElementById("sc-workbench-app");
  root.innerHTML=`
  <div class="sc-shell">
    <header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.4.0</div></header>
    <div class="sc-main">
      <nav class="sc-nav"><a aria-current="page">Calculator</a><a>Workspace</a><a>Graphs</a><a>Settings</a></nav>
      <main class="sc-workspace">
        <section class="sc-hero"><div class="sc-kicker">Standalone mathematical view renderer</div><h1 class="sc-title">Calculator</h1><p class="sc-copy">Compute canonical CalculationObjects, then request renderer-neutral mathematical views from FastAPI and render them directly in the standalone browser application.</p></section>
        <section class="sc-panel">
          <div class="sc-grid">
            <div class="sc-field"><label>Operation</label><select id="calculator-operation" class="sc-select"><option value="evaluate">Evaluate</option><option value="differentiate">Differentiate</option><option value="simplify">Simplify</option></select></div>
            <div class="sc-field"><label>Variable</label><input id="calculator-variable" class="sc-input" value="x"></div>
            <div class="sc-field sc-field-wide"><label>Expression</label><textarea id="calculator-expression" class="sc-textarea">x**2-1</textarea></div>
            <div class="sc-field"><label>Project</label><select id="calculator-project" class="sc-select"><option value="">Not selected</option>${state.projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join("")}</select></div>
          </div>
          <div class="sc-actions">
            <button id="calculator-run" class="sc-button sc-button-primary">Run</button>
            <button id="calculator-save" class="sc-button">Run & Save</button>
            <button id="calculator-graph" class="sc-button">Graph</button>
          </div>
          ${state.error?`<p class="sc-error">${state.error}</p>`:""}
          ${state.result?`<div class="sc-result"><pre>${JSON.stringify(state.result.calculationObject?.result,null,2)}</pre></div>`:""}
          <div id="mathematical-views" class="math-view-grid"></div>
        </section>
      </main>
    </div>
    <footer class="sc-footer">View specs: FastAPI · rendering: standalone browser · WordPress optional</footer>
  </div>`;
  document.querySelector("#calculator-run")?.addEventListener("click",()=>executeCalculator(false));
  document.querySelector("#calculator-save")?.addEventListener("click",()=>executeCalculator(true));
  document.querySelector("#calculator-graph")?.addEventListener("click",requestGraphView);
  if(state.graph) renderMathematicalViews(document.querySelector("#mathematical-views"),state.graph.viewSpec);
}
async function bootstrap(){
  try{
    const h=await request("/standalone/v1/health",{auth:false});state.online=Boolean(h.ok);
    await bootstrapSession();await loadProjects();
  }catch(e){state.error=String(e);}
  render();
}
bootstrap();
