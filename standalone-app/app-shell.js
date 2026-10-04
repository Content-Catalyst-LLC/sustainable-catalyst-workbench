import { WORKBENCH_CONFIG } from "./config.js";

const state = {
  manifest:null, routes:null, shell:null, auth:null,
  session:null, token:null, projects:[], calculatorConfig:null,
  calculation:null, calculationError:null, calculationBusy:false,
  online:false, error:null
};

async function request(path, options={}) {
  const headers=Object.assign(
    {"Accept":"application/json","Content-Type":"application/json"},
    options.headers||{}
  );
  if(state.token && options.auth!==false) headers["Authorization"]=`Bearer ${state.token}`;
  const init={method:options.method||"GET",headers};
  if(options.body!==undefined) init.body=JSON.stringify(options.body);
  const response=await fetch(WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"")+path,init);
  const payload=await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(payload.detail||`HTTP ${response.status}`);
  return payload;
}

async function bootstrapSession() {
  state.auth=(await request("/standalone/v1/auth/config",{auth:false})).auth;
  const stored=sessionStorage.getItem("scwb.session.token");
  if(stored) {
    try {
      const verified=await request("/standalone/v1/auth/session/verify",{
        method:"POST",auth:false,body:{token:stored}
      });
      state.token=stored; state.session=verified.session; return;
    } catch(_error) {
      sessionStorage.removeItem("scwb.session.token");
    }
  }
  const created=await request("/standalone/v1/auth/session/anonymous",{
    method:"POST",auth:false,
    body:{ttlSeconds:3600,clientLabel:"standalone-app"}
  });
  state.token=created.token;
  state.session=created.session;
  sessionStorage.setItem("scwb.session.token",created.token);
}

async function loadProjects() {
  if(!state.token) return;
  const result=await request("/standalone/v1/projects");
  state.projects=result.projects||[];
}

async function loadCalculatorConfig() {
  if(!state.token) return;
  const result=await request("/standalone/v1/calculator/config");
  state.calculatorConfig=result.calculator;
  state.projects=result.projects||state.projects;
}

async function createProject(name="Untitled Project") {
  const result=await request("/standalone/v1/projects",{
    method:"POST",body:{name,description:"",metadata:{}}
  });
  state.projects.unshift(result.project);
  render();
  return result.project;
}

function valueOf(obj) {
  const v=obj?.result?.value;
  if(v===null||v===undefined) return "No result";
  if(typeof v==="object") {
    if(v.float!==null && v.float!==undefined) return String(v.float);
    if(v.expression!==undefined) return String(v.expression);
    if(v.exact!==undefined) return String(v.exact);
    if(v.solutions!==undefined) return JSON.stringify(v.solutions);
    if(v.value!==undefined) return String(v.value);
    return JSON.stringify(v,null,2);
  }
  return String(v);
}

function buildCalculationRequest(form) {
  const operation=form.querySelector("#calculator-operation").value;
  const expression=form.querySelector("#calculator-expression").value.trim();
  const variable=form.querySelector("#calculator-variable").value.trim();
  const runtime=form.querySelector("#calculator-runtime").value;
  const requestedResultType=form.querySelector("#calculator-result-type").value;

  const calculation={operation,expression};
  if(variable) calculation.variable=variable;

  return {
    calculation,
    requestedResultType,
    preferredRuntime:runtime,
    requireVerification:true,
    requireProvenance:true,
    metadata:{source:"standalone-calculator-workspace"}
  };
}

async function executeCalculator(saveResult=false) {
  const form=document.querySelector("#calculator-form");
  if(!form) return;
  state.calculationBusy=true;
  state.calculationError=null;
  render();

  try {
    const calculationRequest=buildCalculationRequest(form);
    const projectId=form.querySelector("#calculator-project")?.value||null;
    if(saveResult && !projectId) throw new Error("Select a project before saving.");

    const title=form.querySelector("#calculator-title")?.value.trim() || "Calculation";
    const result=await request("/standalone/v1/calculator/execute",{
      method:"POST",
      body:{calculationRequest,projectId,saveResult,title,tags:[],metadata:{}}
    });
    state.calculation=result;
    if(result.saved) await loadProjects();
  } catch(error) {
    state.calculationError=String(error);
  } finally {
    state.calculationBusy=false;
    render();
  }
}

function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function navigate(path){history.pushState({},"",path);render();}
function sessionLabel(){return state.session?.subject?.type==="anonymous"?"ANONYMOUS SESSION":"NO SESSION";}

function calculatorPanel() {
  const ops=state.calculatorConfig?.operations||[
    {id:"evaluate",label:"Evaluate"},
    {id:"exact",label:"Exact"},
    {id:"simplify",label:"Simplify"},
    {id:"differentiate",label:"Differentiate"},
    {id:"integrate-symbolic",label:"Integrate"},
    {id:"solve",label:"Solve"}
  ];
  const result=state.calculation?.calculationObject;
  const saved=state.calculation?.savedCalculation;

  return `
    <section class="sc-panel">
      <form id="calculator-form">
        <div class="sc-grid">
          <div class="sc-field">
            <label for="calculator-operation">Operation</label>
            <select id="calculator-operation" class="sc-select">
              ${ops.map(op=>`<option value="${op.id}">${op.label}</option>`).join("")}
            </select>
          </div>
          <div class="sc-field">
            <label for="calculator-variable">Variable</label>
            <input id="calculator-variable" class="sc-input" value="x" placeholder="x">
          </div>
          <div class="sc-field sc-field-wide">
            <label for="calculator-expression">Expression</label>
            <textarea id="calculator-expression" class="sc-textarea" placeholder="Example: sin(x)^2 + cos(x)^2">2+3*4</textarea>
          </div>
          <div class="sc-field">
            <label for="calculator-runtime">Preferred runtime</label>
            <select id="calculator-runtime" class="sc-select">
              <option value="auto">Auto</option>
              <option value="python">Python</option>
              <option value="julia">Julia</option>
            </select>
          </div>
          <div class="sc-field">
            <label for="calculator-result-type">Result type</label>
            <select id="calculator-result-type" class="sc-select">
              <option value="auto">Auto</option>
              <option value="numeric">Numeric</option>
              <option value="exact">Exact</option>
              <option value="symbolic">Symbolic</option>
            </select>
          </div>
          <div class="sc-field">
            <label for="calculator-project">Save to project</label>
            <select id="calculator-project" class="sc-select">
              <option value="">Not selected</option>
              ${state.projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join("")}
            </select>
          </div>
          <div class="sc-field">
            <label for="calculator-title">Calculation title</label>
            <input id="calculator-title" class="sc-input" value="Calculation">
          </div>
        </div>
        <div class="sc-actions">
          <button type="button" id="calculator-run" class="sc-button sc-button-primary" ${state.calculationBusy?"disabled":""}>${state.calculationBusy?"Running…":"Run"}</button>
          <button type="button" id="calculator-save" class="sc-button" ${state.calculationBusy?"disabled":""}>Run & Save</button>
        </div>
      </form>
      ${state.calculationError?`<p class="sc-error">${state.calculationError}</p>`:""}
      ${result?`
        <div class="sc-result">
          <div class="sc-result-value">${valueOf(result)}</div>
          <div class="sc-meta">
            <div><strong>Engine</strong><br>${result.result?.engine||"—"}</div>
            <div><strong>Runtime</strong><br>${result.executionPlan?.selectedRuntime||"—"}</div>
            <div><strong>Verification</strong><br>${result.verification?.status||"—"}</div>
          </div>
          <pre>${JSON.stringify({
            result:result.result,
            provenance:result.provenance,
            calculationObjectHash:result.calculationObjectHash,
            savedCalculationId:saved?.id||null
          },null,2)}</pre>
        </div>`:""}
    </section>`;
}

function workspacePanel(selected) {
  if(selected?.path!=="/workspace") return "";
  return `
    <section class="sc-panel" id="workspace-projects">
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
        <strong>Projects</strong>
        <button id="create-project" class="sc-button">New Project</button>
      </div>
      <div>
        ${state.projects.length
          ? state.projects.map(p=>`<div class="sc-project-row"><strong>${p.name}</strong><br><small>${p.id}</small></div>`).join("")
          : "<p>No projects yet.</p>"}
      </div>
    </section>`;
}

function render() {
  const root=document.getElementById("sc-workbench-app");
  const fallback=[
    {path:"/calculator",label:"Calculator",available:true},
    {path:"/workspace",label:"Workspace",available:true},
    {path:"/graphs",label:"Graphs",available:true},
    {path:"/settings",label:"Settings",available:true}
  ];
  let routes=state.routes?.routes||fallback;
  routes=routes.map(r=>r.path==="/workspace"?Object.assign({},r,{available:true}):r);
  const path=currentPath();
  const selected=routes.find(r=>r.path===path&&r.available)||routes.find(r=>r.path==="/calculator")||routes[0];

  root.innerHTML=`
    <div class="sc-shell">
      <header class="sc-topbar">
        <div class="sc-brand">Sustainable Catalyst / Workbench</div>
        <div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · ${sessionLabel()} · ${WORKBENCH_CONFIG.version}</div>
      </header>
      <div class="sc-main">
        <nav class="sc-nav" aria-label="Workbench">
          ${routes.map(r=>`<a href="${r.path}" data-route="${r.path}" data-disabled="${!r.available}" ${selected?.path===r.path?'aria-current="page"':''}>${r.label}</a>`).join("")}
        </nav>
        <main class="sc-workspace">
          <section class="sc-hero">
            <div class="sc-kicker">Standalone calculator workspace</div>
            <h1 class="sc-title">${selected?.label||"Workbench"}</h1>
            <p class="sc-copy">Execute canonical CalculationObjects directly against FastAPI, inspect result/runtime/provenance, and save the exact CalculationObject into a persistent standalone project.</p>
          </section>
          ${selected?.path==="/calculator"?calculatorPanel():workspacePanel(selected)}
        </main>
      </div>
      <footer class="sc-footer">Canonical math: v11 engine · persistence: v12.2 store · WordPress optional</footer>
    </div>`;

  root.querySelectorAll("a[data-route]").forEach(a=>{
    if(a.dataset.disabled==="true") return;
    a.addEventListener("click",e=>{e.preventDefault();navigate(a.dataset.route);});
  });
  root.querySelector("#calculator-run")?.addEventListener("click",()=>executeCalculator(false));
  root.querySelector("#calculator-save")?.addEventListener("click",()=>executeCalculator(true));
  root.querySelector("#create-project")?.addEventListener("click",async()=>{
    const name=prompt("Project name","Untitled Project");
    if(name) await createProject(name);
  });
}

async function bootstrap() {
  try {
    const [health,manifest,routes,shell]=await Promise.all([
      request("/standalone/v1/health",{auth:false}),
      request("/standalone/v1/app-manifest",{auth:false}),
      request("/standalone/v1/app-routes",{auth:false}),
      request("/standalone/v1/app-shell",{auth:false})
    ]);
    state.online=Boolean(health.ok);
    state.manifest=manifest.manifest;
    state.routes=routes.routeRegistry;
    state.shell=shell.shell;
    await bootstrapSession();
    await loadProjects();
    await loadCalculatorConfig();
  } catch(error) {
    state.online=false; state.error=String(error);
  }
  render();
}

addEventListener("popstate",render);
bootstrap();
