import { WORKBENCH_CONFIG } from "./config.js";
import { renderMathematicalViews } from "./math-renderer.js";

const state={token:null,session:null,launch:null,projects:[],selectedProject:null,error:null,online:false};

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
async function resolveLaunch(){
  const token=new URL(location.href).searchParams.get("launch");
  if(!token) return null;
  const v=await request("/standalone/v1/launch/validate",{method:"POST",auth:false,body:{token}});
  state.launch=v.launchDescriptor;
  const route=state.launch.route||"/calculator";
  if(location.pathname!==route) history.replaceState({},"",`${route}?launch=${encodeURIComponent(token)}`);
  return state.launch;
}
async function loadProjects(){state.projects=(await request("/standalone/v1/projects")).projects||[];}
async function resolveProtectedTarget(){
  if(!state.launch||state.launch.targetType==="none"||!state.launch.targetId) return;
  // Launch tokens never bypass ownership. Protected target lookups use the standalone session.
  if(state.launch.targetType==="project"){
    const p=await request(`/standalone/v1/projects/${encodeURIComponent(state.launch.targetId)}`);
    state.selectedProject=p.project.id;
  } else if(state.launch.targetType==="calculation"){
    await request(`/standalone/v1/calculations/${encodeURIComponent(state.launch.targetId)}`);
  } else if(state.launch.targetType==="package"){
    await request(`/standalone/v1/reproducibility/packages/${encodeURIComponent(state.launch.targetId)}`);
  }
}
function currentPath(){return location.pathname==="/" ? "/calculator" : location.pathname;}
function nav(p){history.pushState({},"",p);render();}
function render(){
  const root=document.getElementById("sc-workbench-app"),path=currentPath();
  const embed=Boolean(state.launch?.embed);
  root.innerHTML=`<div class="sc-shell ${embed?"sc-embedded":""}"><header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · 12.7.0${embed?" · EMBED":""}</div></header><div class="sc-main"><nav class="sc-nav"><a data-route="/calculator">Calculator</a><a data-route="/workspace">Workspace</a><a data-route="/graphs">Graphs</a><a data-route="/history">History</a><a data-route="/packages">Packages</a><a data-route="/settings">Settings</a></nav><main class="sc-workspace"><section class="sc-hero"><div class="sc-kicker">Embed & deep-link compatibility</div><h1 class="sc-title">${path.slice(1)||"Calculator"}</h1><p class="sc-copy">This standalone route may have been launched from WordPress, but authentication and ownership remain standalone.</p></section><section class="sc-panel"><pre>${JSON.stringify({launch:state.launch,selectedProject:state.selectedProject,sessionSubject:state.session?.subject?.type||null},null,2)}</pre>${state.error?`<p class="sc-error">${state.error}</p>`:""}</section></main></div><footer class="sc-footer">WordPress launch compatibility · standalone state authority preserved</footer></div>`;
  root.querySelectorAll("[data-route]").forEach(a=>a.addEventListener("click",()=>nav(a.dataset.route)));
}
async function bootstrap(){
  try{
    state.online=Boolean((await request("/standalone/v1/health",{auth:false})).ok);
    await resolveLaunch();
    await bootstrapSession();
    await loadProjects();
    await resolveProtectedTarget();
  }catch(e){state.error=String(e);}
  render();
}
addEventListener("popstate",render);
bootstrap();
