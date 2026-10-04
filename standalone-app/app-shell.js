import { WORKBENCH_CONFIG } from "./config.js";

const state = {
  manifest:null, routes:null, shell:null, auth:null,
  session:null, token:null, projects:[], online:false, error:null
};

async function request(path, options={}) {
  const headers=Object.assign(
    {"Accept":"application/json","Content-Type":"application/json"},
    options.headers||{}
  );
  if (state.token && options.auth !== false) {
    headers["Authorization"]=`Bearer ${state.token}`;
  }
  const init={method:options.method||"GET",headers};
  if (options.body!==undefined) init.body=JSON.stringify(options.body);
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
      state.token=stored;
      state.session=verified.session;
      return;
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

async function createProject(name="Untitled Project") {
  const result=await request("/standalone/v1/projects",{
    method:"POST",body:{name,description:"",metadata:{}}
  });
  state.projects.unshift(result.project);
  render();
  return result.project;
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
  } catch(error) {
    state.online=false; state.error=String(error);
  }
  render();
}

function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function navigate(path){history.pushState({},"",path);render();}
function sessionLabel(){return state.session?.subject?.type==="anonymous"?"ANONYMOUS SESSION":"NO SESSION";}

function workspacePanel(selected) {
  if(selected?.path!=="/workspace") return `
    <section class="sc-panel">
      <strong>Persistent Store</strong>
      <pre>${state.projects.length} project(s) available in this session-owned workspace.</pre>
    </section>`;
  return `
    <section class="sc-panel" id="workspace-projects">
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
        <strong>Projects</strong>
        <button id="create-project">New Project</button>
      </div>
      <div>
        ${state.projects.length
          ? state.projects.map(p=>`<div style="padding:10px 0;border-bottom:1px solid #242424"><strong>${p.name}</strong><br><small>${p.id}</small></div>`).join("")
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
            <div class="sc-kicker">Persistent calculation & project store</div>
            <h1 class="sc-title">${selected?.label||"Workbench"}</h1>
            <p class="sc-copy">Projects and saved CalculationObjects now persist in the FastAPI application store and are owned by the standalone session subject. WordPress is not the persistence authority.</p>
          </section>
          ${workspacePanel(selected)}
        </main>
      </div>
      <footer class="sc-footer">SQLite persistence · session-subject ownership · WordPress optional</footer>
    </div>`;

  root.querySelectorAll("a[data-route]").forEach(a=>{
    if(a.dataset.disabled==="true") return;
    a.addEventListener("click",e=>{e.preventDefault();navigate(a.dataset.route);});
  });
  const create=root.querySelector("#create-project");
  if(create) create.addEventListener("click",async()=>{
    const name=prompt("Project name","Untitled Project");
    if(name) await createProject(name);
  });
}

addEventListener("popstate",render);
bootstrap();
