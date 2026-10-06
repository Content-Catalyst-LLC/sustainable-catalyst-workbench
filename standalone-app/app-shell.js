import { WORKBENCH_CONFIG } from "./config.js";
import { renderViewSpec } from "./math-renderer.js";
import { paletteHtml, insertAtCursor } from "./math-input.js";
const API=WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"");
const state={token:null,session:null,online:false,route:"calculator",projects:[],projectId:sessionStorage.getItem("scwb.project.id")||null,calculations:[],notebooks:[],history:[],packages:[],researchSessions:[],researchSessionId:sessionStorage.getItem("scwb.research.session.id")||null,researchSessionSummary:null,researchSessionActivity:[],savedGraphs:[],activeGraphId:sessionStorage.getItem("scwb.graph.id")||null,activeGraph:null,researchTimeline:[],timelineScope:"session",timelineFilter:"all",activeNotebookId:sessionStorage.getItem("scwb.notebook.id")||null,notebookEntries:[],activePackageId:sessionStorage.getItem("scwb.package.id")||null,activePackage:null,packageComparison:null,unifiedWorkspace:null,naturalLanguageText:"",naturalLanguagePlan:null,intentPlan:null,intentPlanApplied:false,executionExplanation:null,lastCalculation:null,lastPresentation:null,lastRequest:null,lastViewSpec:null,lastNormalization:null,message:null,error:null,frontendVersion:null,backendVersion:null,versionAligned:false,recent:JSON.parse(localStorage.getItem("scwb.recent.expressions")||"[]")};
function pathRoute(){const p=location.pathname.replace(/^\/+/,"").split("/")[0]||"calculator";return ["calculator","workspace","graphs","history","packages","settings"].includes(p)?p:"calculator";}state.route=pathRoute();
async function rawRequest(path,options={}){const headers={Accept:"application/json","Content-Type":"application/json",...(options.headers||{})};if(state.token&&options.auth!==false)headers.Authorization=`Bearer ${state.token}`;const init={method:options.method||"GET",headers};if(options.body!==undefined)init.body=JSON.stringify(options.body);const r=await fetch(API+path,init);const d=await r.json().catch(()=>({}));if(!r.ok){const e=new Error(typeof d.detail==="string"?d.detail:JSON.stringify(d.detail||d||{status:r.status}));e.status=r.status;throw e;}return d;}
async function api(path,options={}){try{return await rawRequest(path,options);}catch(e){if((e.status===401||e.status===403)&&options.auth!==false&&path.indexOf("/auth/session/")===-1){sessionStorage.removeItem("scwb.session.token");state.token=null;await bootstrapSession();return rawRequest(path,options);}throw e;}}
async function bootstrapSession(){const stored=sessionStorage.getItem("scwb.session.token");if(stored){try{const v=await rawRequest("/standalone/v1/auth/session/verify",{method:"POST",auth:false,body:{token:stored}});state.token=stored;state.session=v.session||v.data?.session||v;return;}catch(_){sessionStorage.removeItem("scwb.session.token");}}const d=await rawRequest("/standalone/v1/auth/session/anonymous",{method:"POST",auth:false,body:{ttlSeconds:3600,clientLabel:"v13.10-intent-planning"}});state.token=d.token||d.data?.token;state.session=d.session||d.data?.session||d;sessionStorage.setItem("scwb.session.token",state.token);}
async function verifyVersionAlignment(){const [f,b]=await Promise.all([fetch(WORKBENCH_CONFIG.frontendVersionAsset,{cache:"no-store"}).then(r=>r.json()),rawRequest("/v13100/status",{auth:false})]);state.frontendVersion=f.version;state.backendVersion=b.version;state.versionAligned=f.version===b.version&&b.intentPlanningReady===true;if(!state.versionAligned)throw new Error(`Frontend/API version mismatch: ${f.version} vs ${b.version}`);}
async function loadProjects(){const d=await api("/standalone/v1/projects");state.projects=d.projects||[];if(!state.projectId&&state.projects.length)state.projectId=state.projects[0].id;if(state.projectId&&!state.projects.some(x=>x.id===state.projectId))state.projectId=state.projects[0]?.id||null;if(state.projectId)sessionStorage.setItem("scwb.project.id",state.projectId);}
async function loadResearchSessions(){
  if(!state.projectId){state.researchSessions=[];state.researchSessionId=null;state.researchSessionSummary=null;state.researchSessionActivity=[];return;}
  const d=await api(`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/research-sessions`);
  state.researchSessions=d.researchSessions||[];
  if(!state.researchSessionId||!state.researchSessions.some(x=>x.id===state.researchSessionId))state.researchSessionId=state.researchSessions[0]?.id||null;
  if(state.researchSessionId){sessionStorage.setItem("scwb.research.session.id",state.researchSessionId);await loadActiveResearchSession();}
}
async function loadActiveResearchSession(){
  if(!state.researchSessionId){state.researchSessionSummary=null;state.researchSessionActivity=[];return;}
  const id=encodeURIComponent(state.researchSessionId);
  const [summary,activity]=await Promise.all([
    api(`/standalone/v1/research-sessions/${id}/summary`),
    api(`/standalone/v1/research-sessions/${id}/activity?limit=100`)
  ]);
  state.researchSessionSummary=summary.summary||null;
  state.researchSessionActivity=activity.activity||[];
}
async function createResearchSession(){
  if(!state.projectId)throw new Error("Create or select a project first.");
  const title=prompt("Research session title","Research Session"); if(!title)return;
  const purpose=prompt("Purpose (optional)","")||"";
  const d=await api("/standalone/v1/research-sessions",{method:"POST",body:{
    projectId:state.projectId,title,purpose,tags:["workbench-v13.4"],metadata:{interfaceVersion:"13.4.0"}
  }});
  state.researchSessionId=d.researchSession.id;
  sessionStorage.setItem("scwb.research.session.id",state.researchSessionId);
  await loadResearchSessions(); render(); toast("Research session created.");
}
async function activateResearchSession(id){
  state.researchSessionId=id||null;
  if(!state.researchSessionId){sessionStorage.removeItem("scwb.research.session.id");state.researchSessionSummary=null;state.researchSessionActivity=[];render();return;}
  sessionStorage.setItem("scwb.research.session.id",state.researchSessionId);
  const d=await api(`/standalone/v1/research-sessions/${encodeURIComponent(id)}/activate`,{method:"POST"});
  const route=d.researchSession?.lastRoute;
  await loadActiveResearchSession();
  await loadUnifiedWorkspace();
  if(route&&["calculator","workspace","graphs","history","packages","settings"].includes(route))state.route=route;
  render();
}
async function recordSessionActivity(kind,label,objectType=null,objectId=null,route=state.route,metadata={}){
  if(!state.researchSessionId)return;
  try{await api(`/standalone/v1/research-sessions/${encodeURIComponent(state.researchSessionId)}/activity`,{method:"POST",body:{kind,label,objectType,objectId,route,metadata}});}catch(_){}
}
async function loadProjectData(){if(!state.projectId){state.calculations=[];state.notebooks=[];state.history=[];state.packages=[];return;}const id=encodeURIComponent(state.projectId);const [c,n,h,p]=await Promise.all([api(`/standalone/v1/projects/${id}/calculations`),api(`/standalone/v1/projects/${id}/notebooks`),api(`/standalone/v1/projects/${id}/history`),api(`/standalone/v1/projects/${id}/reproducibility/packages`)]);state.calculations=c.calculations||[];state.notebooks=n.notebooks||[];state.history=h.history||[];state.packages=p.packages||[];if(state.activeNotebookId&&!state.notebooks.some(x=>x.id===state.activeNotebookId))state.activeNotebookId=null;if(!state.activeNotebookId&&state.notebooks.length)state.activeNotebookId=state.notebooks[0].id;await loadResearchSessions();await loadSavedGraphs();await loadNotebookEntries();await loadResearchTimeline();await loadPackageWorkspace();await loadUnifiedWorkspace();}
async function loadSavedGraphs(){
  if(!state.projectId){state.savedGraphs=[];state.activeGraphId=null;state.activeGraph=null;return;}
  const d=await api(`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/graphs`);
  state.savedGraphs=d.graphs||[];
  if(state.activeGraphId&&!state.savedGraphs.some(g=>g.id===state.activeGraphId))state.activeGraphId=null;
  if(!state.activeGraphId&&state.savedGraphs.length)state.activeGraphId=state.savedGraphs[0].id;
  if(state.activeGraphId){sessionStorage.setItem("scwb.graph.id",state.activeGraphId);await loadActiveGraph();}
}
async function loadActiveGraph(){
  if(!state.activeGraphId){state.activeGraph=null;return;}
  const d=await api(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(state.activeGraphId)}`);
  state.activeGraph=d.graph||null;
}
function graphSeriesDraft(){
  return Array.from(document.querySelectorAll("[data-graph-series]")).map(row=>({
    expression:row.querySelector("[data-expression]").value.trim(),
    label:row.querySelector("[data-label]").value.trim()||null,
    variable:row.querySelector("[data-variable]").value.trim()||"x",
    visible:row.querySelector("[data-visible]").checked,
    includeRoots:row.querySelector("[data-roots]").checked,
    includeCriticalPoints:row.querySelector("[data-critical]").checked,
    includeDerivative:row.querySelector("[data-derivative]").checked,
    includeIntegral:row.querySelector("[data-integral]").checked
  })).filter(x=>x.expression);
}
function graphSeriesRow(s={},i=0){
  return `<div class="sc-graph-series" data-graph-series>
    <label class="sc-field">Expression<input class="sc-input" data-expression value="${esc(s.expression||"sin(x)")}"></label>
    <div class="sc-grid">
      <label class="sc-field">Label<input class="sc-input" data-label value="${esc(s.label||"")}"></label>
      <label class="sc-field">Variable<input class="sc-input" data-variable value="${esc(s.variable||"x")}"></label>
    </div>
    <div class="sc-inline">
      <label><input type="checkbox" data-visible ${s.visible===false?"":"checked"}> visible</label>
      <label><input type="checkbox" data-roots ${s.includeRoots===false?"":"checked"}> roots</label>
      <label><input type="checkbox" data-critical ${s.includeCriticalPoints===false?"":"checked"}> critical</label>
      <label><input type="checkbox" data-derivative ${s.includeDerivative?"checked":""}> derivative</label>
      <label><input type="checkbox" data-integral ${s.includeIntegral?"checked":""}> integral</label>
      <button type="button" class="sc-button" data-remove-series>Remove</button>
    </div>
  </div>`;
}
function addGraphSeries(expression=""){
  const list=document.getElementById("graph-series-list"); if(!list)return;
  const wrap=document.createElement("div"); wrap.innerHTML=graphSeriesRow({expression:expression||"sin(x)"});
  list.appendChild(wrap.firstElementChild); bindGraphSeriesButtons();
}
function bindGraphSeriesButtons(){
  document.querySelectorAll("[data-remove-series]").forEach(b=>b.onclick=()=>b.closest("[data-graph-series]")?.remove());
}
async function createGraphStudy(){
  if(!state.projectId)throw new Error("Create or select a project first.");
  const series=graphSeriesDraft(); if(!series.length)throw new Error("Add at least one graph expression.");
  const title=document.getElementById("graph-title").value.trim()||"Graph Study";
  const a=Number(document.getElementById("graph-start").value),b=Number(document.getElementById("graph-end").value);
  const ya=Number(document.getElementById("graph-y-start").value),yb=Number(document.getElementById("graph-y-end").value);
  const d=await api("/standalone/v1/graph-studio/graphs",{method:"POST",body:{
    projectId:state.projectId,researchSessionId:state.researchSessionId||null,title,graphType:"cartesian",
    series,domain:[a,b],yDomain:[ya,yb],samples:Number(document.getElementById("graph-samples").value||401),
    metadata:{interfaceVersion:"13.5.0"}
  }});
  state.activeGraphId=d.graph.id;sessionStorage.setItem("scwb.graph.id",state.activeGraphId);
  await recordSessionActivity("graph","Graph study created","graph",state.activeGraphId,"graphs",{title});
  await loadSavedGraphs();await renderSavedGraph();render();toast("Graph study saved.");
}
async function saveActiveGraph(){
  if(!state.activeGraphId)return createGraphStudy();
  const series=graphSeriesDraft(); if(!series.length)throw new Error("Add at least one graph expression.");
  const body={title:document.getElementById("graph-title").value.trim()||"Graph Study",series,
    domain:[Number(document.getElementById("graph-start").value),Number(document.getElementById("graph-end").value)],
    yDomain:[Number(document.getElementById("graph-y-start").value),Number(document.getElementById("graph-y-end").value)],
    samples:Number(document.getElementById("graph-samples").value||401),
    metadata:{interfaceVersion:"13.5.0"}};
  await api(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(state.activeGraphId)}`,{method:"PATCH",body});
  await recordSessionActivity("graph","Graph study updated","graph",state.activeGraphId,"graphs",{title:body.title});
  await loadSavedGraphs();await renderSavedGraph();render();toast("Graph study updated.");
}
async function renderSavedGraph(){
  if(!state.activeGraphId){state.lastViewSpec=null;return;}
  const d=await api(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(state.activeGraphId)}/render`,{method:"POST"});
  state.lastViewSpec=d.render||null;
  state.activeGraph=d.render?.graph||state.activeGraph;
}
async function activateGraphStudy(id){
  state.activeGraphId=id||null;
  if(!id){sessionStorage.removeItem("scwb.graph.id");state.activeGraph=null;state.lastViewSpec=null;render();return;}
  sessionStorage.setItem("scwb.graph.id",id);await loadActiveGraph();await renderSavedGraph();render();drawGraph();
}
async function annotateActiveGraph(){
  if(!state.activeGraphId)throw new Error("Save or select a graph first.");
  const label=prompt("Annotation","Note"); if(!label)return;
  await api(`/standalone/v1/graph-studio/graphs/${encodeURIComponent(state.activeGraphId)}/annotations`,{method:"POST",body:{kind:"note",label,metadata:{interfaceVersion:"13.5.0"}}});
  await recordSessionActivity("graph-annotation","Graph annotation added","graph",state.activeGraphId,"graphs",{label});
  await loadActiveGraph();render();drawGraph();
}
async function loadResearchTimeline(){
  if(!state.projectId){state.researchTimeline=[];return;}
  let path;
  if(state.timelineScope==="session"&&state.researchSessionId)path=`/standalone/v1/research-sessions/${encodeURIComponent(state.researchSessionId)}/timeline`;
  else path=`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/research-timeline`;
  if(state.timelineFilter&&state.timelineFilter!=="all")path+=`?kinds=${encodeURIComponent(state.timelineFilter)}`;
  const d=await api(path);state.researchTimeline=d.timeline?.items||[];
}
async function loadNotebookEntries(){
  if(!state.activeNotebookId){state.notebookEntries=[];return;}
  const d=await api(`/standalone/v1/notebooks/${encodeURIComponent(state.activeNotebookId)}/research-entries`);
  state.notebookEntries=d.entries||[];
}
async function activateNotebook(id){
  state.activeNotebookId=id||null;
  if(state.activeNotebookId)sessionStorage.setItem("scwb.notebook.id",state.activeNotebookId);
  else sessionStorage.removeItem("scwb.notebook.id");
  await loadNotebookEntries();render();
}
async function addNotebookNote(){
  if(!state.activeNotebookId)throw new Error("Select or create a notebook first.");
  const title=prompt("Note title","Research Note");if(!title)return;
  const markdown=prompt("Note text","")||"";
  await api(`/standalone/v1/notebooks/${encodeURIComponent(state.activeNotebookId)}/structured-notes`,{method:"POST",body:{title,markdown,researchSessionId:state.researchSessionId||null,pinned:false,metadata:{interfaceVersion:"13.6.0"}}});
  await recordSessionActivity("notebook-note","Notebook note added","notebook",state.activeNotebookId,"history",{title});
  await loadNotebookEntries();await loadResearchTimeline();render();toast("Notebook note added.");
}
async function attachSelectedObject(type){
  if(!state.activeNotebookId)throw new Error("Select or create a notebook first.");
  let id=null,title=null;
  if(type==="calculation"){const item=state.calculations[0];id=item?.id;title=item?.title;}
  if(type==="graph"){const item=state.savedGraphs[0];id=item?.id;title=item?.title;}
  if(type==="package"){const item=state.packages[0];id=item?.id;title=item?.title;}
  if(!id)throw new Error(`No ${type} object is available to attach.`);
  await api(`/standalone/v1/notebooks/${encodeURIComponent(state.activeNotebookId)}/attach`,{method:"POST",body:{objectType:type,objectId:id,title:title||`${type} reference`,note:"",researchSessionId:state.researchSessionId||null,pinned:false,metadata:{interfaceVersion:"13.6.0"}}});
  await recordSessionActivity("notebook-attachment",`${type} attached to notebook`,"notebook",state.activeNotebookId,"history",{objectType:type,objectId:id});
  await loadNotebookEntries();await loadResearchTimeline();render();toast(`${type} attached.`);
}
function openTimelineItem(item){
  if(!item)return;
  if(item.route==="graphs"&&item.metadata?.graphId){state.activeGraphId=item.metadata.graphId;sessionStorage.setItem("scwb.graph.id",state.activeGraphId);}
  nav(item.route||"history");
}
async function loadPackageWorkspace(){
  if(!state.projectId){state.packages=[];state.activePackageId=null;state.activePackage=null;state.packageComparison=null;return;}
  const d=await api(`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/reproducibility/workspace`);
  state.packages=d.packages||[];
  if(state.activePackageId&&!state.packages.some(x=>x.id===state.activePackageId))state.activePackageId=null;
  if(!state.activePackageId&&state.packages.length)state.activePackageId=state.packages[0].id;
  if(state.activePackageId){sessionStorage.setItem("scwb.package.id",state.activePackageId);await loadActivePackage();}
}
async function loadActivePackage(){
  if(!state.activePackageId){state.activePackage=null;state.packageComparison=null;return;}
  const d=await api(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}`);
  state.activePackage=d.package||null;
}
async function activatePackage(id){
  state.activePackageId=id||null;state.packageComparison=null;
  if(!id){sessionStorage.removeItem("scwb.package.id");state.activePackage=null;render();return;}
  sessionStorage.setItem("scwb.package.id",id);await loadActivePackage();render();
}
async function verifyActivePackage(){
  if(!state.activePackageId)throw new Error("Select a reproducibility package first.");
  await api(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}/verify`,{method:"POST"});
  await recordSessionActivity("package-verification","Reproducibility package verified","package",state.activePackageId,"packages",{});
  await loadPackageWorkspace();render();toast("Package integrity verified.");
}
async function replayActivePackage(){
  if(!state.activePackageId)throw new Error("Select a reproducibility package first.");
  const mode=document.getElementById("package-replay-mode")?.value||"strict";
  const d=await api(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}/replay`,{method:"POST",body:{comparisonMode:mode}});
  state.packageComparison=d.comparison||null;state.activePackage=d.package||state.activePackage;
  await recordSessionActivity("package-replay",`Package replay: ${state.packageComparison?.reproducible?"reproducible":"divergent"}`,"package",state.activePackageId,"packages",{comparisonMode:mode,certificateHash:state.packageComparison?.certificateHash||null});
  await loadResearchTimeline();render();toast(state.packageComparison?.reproducible?"Replay certified reproducible.":"Replay completed with divergences.");
}
async function savePackageMetadata(){
  if(!state.activePackageId)throw new Error("Select a reproducibility package first.");
  const title=document.getElementById("package-title").value.trim()||"Reproducibility Package";
  const notes=document.getElementById("package-notes").value;
  await api(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}`,{method:"PATCH",body:{
    title,notes,researchSessionId:state.researchSessionId||state.activePackage?.researchSessionId||null,
    metadata:{...(state.activePackage?.metadata||{}),interfaceVersion:"13.7.0"}
  }});
  await recordSessionActivity("package-update","Reproducibility package metadata updated","package",state.activePackageId,"packages",{title});
  await loadPackageWorkspace();await loadResearchTimeline();render();toast("Package metadata updated.");
}
function downloadPackageExport(){
  if(!state.activePackageId)return;
  const token=state.token||"";
  fetch(`${WORKBENCH_CONFIG.apiBaseUrl}/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}/export`,{headers:token?{Authorization:`Bearer ${token}`}:{}})
    .then(r=>{if(!r.ok)throw new Error(`Export failed (${r.status})`);return r.blob();})
    .then(blob=>{const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`workbench-reproducibility-${state.activePackageId}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);})
    .catch(e=>toast(String(e),true));
}
function comparisonRows(){
  const rows=state.packageComparison?.matches||[];
  return rows.map(r=>`<tr><td>${esc(r.field)}</td><td>${r.match?"match":"DIFF"}</td><td class="sc-hash">${esc(r.expected||"—")}</td><td class="sc-hash">${esc(r.observed||"—")}</td></tr>`).join("");
}
async function loadUnifiedWorkspace(){
  if(!state.projectId){state.unifiedWorkspace=null;return;}
  let path=`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/unified-workspace`;
  if(state.researchSessionId)path=`/standalone/v1/research-sessions/${encodeURIComponent(state.researchSessionId)}/unified-workspace`;
  const d=await api(path);
  state.unifiedWorkspace=d.workspace||null;
}
async function unifiedHandoff(target,objectType=null,objectId=null){
  if(!state.projectId){nav(target);return;}
  try{
    const d=await api(`/standalone/v1/projects/${encodeURIComponent(state.projectId)}/unified-workspace/handoff`,{
      method:"POST",
      body:{target,objectType,objectId,researchSessionId:state.researchSessionId||null,metadata:{source:"unified-workspace",interfaceVersion:"13.8.0"}}
    });
    const h=d.handoff||{};
    if(target==="graphs"&&objectId){state.activeGraphId=objectId;sessionStorage.setItem("scwb.graph.id",objectId);}
    if(target==="packages"&&objectId){state.activePackageId=objectId;sessionStorage.setItem("scwb.package.id",objectId);}
    if(target==="history"&&objectId){state.activeNotebookId=objectId;sessionStorage.setItem("scwb.notebook.id",objectId);}
    nav((h.route||`/${target}`).replace(/^\//,""));
  }catch(e){toast(String(e),true);}
}
function unifiedContinuation(key,title){
  const item=state.unifiedWorkspace?.continuations?.[key];
  return `<div class="sc-unified-surface"><strong>${esc(title)}</strong>${item?`<span class="sc-muted">${esc(item.title||"Recent work")}</span><button class="sc-button" data-workspace-route="${esc(key)}" data-object-id="${esc(item.id||"")}">Continue</button>`:`<span class="sc-muted">No saved work yet.</span><button class="sc-button" data-workspace-route="${esc(key)}">Open</button>`}</div>`;
}
function unifiedActivity(){
  const items=state.unifiedWorkspace?.recentActivity||[];
  return items.map((a,i)=>`<div class="sc-unified-activity-row"><span class="sc-badge">${esc(a.kind||a.objectType||"activity")}</span><span>${esc(a.title||"Activity")}</span><button class="sc-button" data-workspace-route="${esc(a.route||"workspace")}" data-object-id="${esc(a.metadata?.graphId||a.metadata?.packageId||a.metadata?.notebookId||a.id||"")}">Open</button></div>`).join("")||'<p class="sc-muted">No recent project activity.</p>';
}
async function planNaturalLanguage(){
  const el=document.getElementById("nl-computation");
  const text=(el?.value||"").trim();
  if(!text)throw new Error("Describe the calculation you want Workbench to plan.");
  state.naturalLanguageText=text;
  const d=await api("/standalone/v1/intent-planning/plan",{method:"POST",body:{text,mode:"conservative"}});
  state.intentPlan=d.plan||null;
  state.intentPlanApplied=false;
  state.executionExplanation=null;
  render();
}
function intentPlanHtml(){
  const p=state.intentPlan;
  if(!p)return '<p class="sc-muted">Workbench will build an inspectable plan before anything is handed to the canonical calculation engine.</p>';
  const req=p.selectedCalculationRequest;
  const calc=req?.calculation||{};
  const v=p.validation||{};
  const warnings=[...(v.blockers||[]),...(v.warnings||[])].map(x=>`<div class="sc-nl-warning">${esc(x)}</div>`).join("");
  const steps=(p.steps||[]).map((x,i)=>`<div class="sc-plan-step"><span class="sc-plan-step-index">${i+1}</span><span><strong>${esc(x.label)}</strong><br><span class="sc-muted">${esc(x.authority)}</span></span><span class="sc-badge">${x.executesMathematics?"executes":"planning"}</span></div>`).join("");
  const alternatives=(p.alternatives||[]).map(x=>`<div class="sc-plan-alternative"><strong>${esc(x.label)}</strong><div class="sc-muted">${esc(x.reason)}</div>${x.recommended?'<span class="sc-badge sc-badge-ok">recommended</span>':''}</div>`).join("");
  if(!req)return `<div class="sc-plan"><strong>No executable plan recognized.</strong>${warnings}<details><summary>Planner object</summary><pre>${esc(JSON.stringify(p,null,2))}</pre></details></div>`;
  return `<div class="sc-plan"><div class="sc-nl-plan-grid"><div class="sc-nl-plan-cell"><span class="sc-muted">Intent</span><strong>${esc(p.intent)}</strong></div><div class="sc-nl-plan-cell"><span class="sc-muted">Confidence</span><strong>${esc(Math.round((p.confidence||0)*100))}%</strong></div><div class="sc-nl-plan-cell"><span class="sc-muted">Plan validation</span><strong>${v.valid?"valid":"blocked"}</strong></div><div class="sc-nl-plan-cell"><span class="sc-muted">Execution</span><strong>${state.intentPlanApplied?"applied":"confirmation required"}</strong></div></div><div class="sc-nl-expression">${esc(calc.expression||"")}</div>${warnings}<h4>Intent-to-calculation plan</h4><div class="sc-plan-steps">${steps}</div>${alternatives?`<details><summary>Alternative plans</summary><div class="sc-plan-alternatives">${alternatives}</div></details>`:""}<div class="sc-actions"><button id="plan-apply" class="sc-button sc-button-primary" ${v.valid?"":"disabled"}>Apply approved plan</button><button id="plan-clear" class="sc-button">Clear</button></div><details><summary>Plan provenance</summary><pre>${esc(JSON.stringify({planHash:p.planHash,interpretationHash:p.interpretationHash,validationHash:v.validationHash,assumptions:p.assumptions,selectedCalculationRequest:req},null,2))}</pre></details>${executionExplanationHtml()}</div>`;
}
function executionExplanationHtml(){
  const x=state.executionExplanation;
  if(!x)return "";
  return `<div class="sc-explanation"><h4>Explainable execution</h4><div class="sc-plan-validation"><span class="sc-badge">${esc(x.requestedOperation||"operation")}</span><span class="sc-badge">${esc(x.execution?.runtime||"runtime not reported")}</span><span class="sc-badge">${esc(x.execution?.method||"method not reported")}</span><span class="sc-badge">${x.verification?.passed===true?"verified":x.verification?.reported?"verification reported":"verification not reported"}</span></div><ol class="sc-explanation-list">${(x.narrative||[]).map(n=>`<li>${esc(n)}</li>`).join("")}</ol><details><summary>Explanation provenance</summary><pre>${esc(JSON.stringify({planHash:x.planHash,calculationObjectHash:x.calculationObjectHash,explanationHash:x.explanationHash,policy:x.policy},null,2))}</pre></details></div>`;
}
function applyIntentPlan(){
  const p=state.intentPlan;
  const req=p?.selectedCalculationRequest;
  if(!req)throw new Error("There is no calculation plan to apply.");
  if(!p.validation?.valid)throw new Error("Resolve blocking plan ambiguities before applying.");
  const calc=req.calculation||{};
  const expr=document.getElementById("calc-expression");
  const op=document.getElementById("calc-operation");
  const variable=document.getElementById("calc-variable");
  const guess=document.getElementById("calc-guess");
  if(expr)expr.value=calc.expression||"";
  if(op)op.value=calc.operation||"evaluate";
  if(variable&&calc.variable)variable.value=calc.variable;
  if(guess&&calc.initialGuess!==undefined)guess.value=calc.initialGuess;
  state.lastNormalization=p.normalization||null;
  state.intentPlanApplied=true;
  const preview=document.getElementById("normalization-preview");
  if(preview)preview.innerHTML=normalizationPreview();
  toast("Plan applied. Review the calculator fields, then execute with the canonical engine.");
}
async function explainLastExecution(){
  if(!state.intentPlan||!state.intentPlanApplied||!state.lastCalculation)return;
  const d=await api("/standalone/v1/intent-planning/explain",{method:"POST",body:{plan:state.intentPlan,calculationObject:state.lastCalculation}});
  state.executionExplanation=d.explanation||null;
}
function esc(x){return String(x??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}function fmt(x){return JSON.stringify(x,null,2);}function toast(m,e=false){state.message=e?null:m;state.error=e?m:null;render();setTimeout(()=>{state.message=null;state.error=null;render();},3000);}function nav(r){state.route=r;history.pushState({},"",`/${r}`);if(state.researchSessionId)api(`/standalone/v1/research-sessions/${encodeURIComponent(state.researchSessionId)}`,{method:"PATCH",body:{lastRoute:r}}).catch(()=>{});render();}window.addEventListener("popstate",()=>{state.route=pathRoute();render();});
function projectOptions(){return state.projects.map(p=>`<option value="${esc(p.id)}" ${p.id===state.projectId?"selected":""}>${esc(p.name)}</option>`).join("");}
function researchSessionOptions(){return state.researchSessions.map(x=>`<option value="${esc(x.id)}" ${x.id===state.researchSessionId?"selected":""}>${esc(x.title)}</option>`).join("");}
function researchSessionBar(){return `<section class="sc-panel"><div class="sc-session-bar"><label class="sc-field">Research session<select id="research-session-select" class="sc-select"><option value="">No active session</option>${researchSessionOptions()}</select></label><button id="new-research-session" class="sc-button sc-button-primary" ${state.projectId?"":"disabled"}>New Session</button><span class="sc-badge">${state.researchSessions.length} sessions</span></div></section>`;}
function commonProjectBar(){return `<section class="sc-panel"><div class="sc-inline"><label>Project</label><select id="project-select" class="sc-select" style="max-width:420px">${state.projects.length?projectOptions():'<option value="">No projects yet</option>'}</select><button id="new-project" class="sc-button">New Project</button><span class="sc-badge">${state.calculations.length} calculations</span><span class="sc-badge">${state.notebooks.length} notebooks</span><span class="sc-badge">${state.packages.length} packages</span></div></section>`;}
function answerCard(){const p=state.lastPresentation;if(!p)return "";const ok=p.verification?.passed!==false;return `<section class="sc-answer"><div class="sc-answer-head"><div><div class="sc-answer-label">Result</div><div class="sc-answer-value">${esc(p.primaryResult?.display||"—")}</div></div><span class="sc-badge ${ok?"sc-badge-ok":"sc-badge-warn"}">${esc(p.verification?.status||"not reported")}</span></div><div class="sc-answer-meta"><span class="sc-badge">${esc(p.operation)}</span>${p.saveState?.saved?'<span class="sc-badge sc-badge-ok">saved</span>':''}</div>${(p.warnings||[]).map(w=>`<div class="sc-warning">${esc(w)}</div>`).join("")}<div class="sc-answer-grid"><div class="sc-answer-cell"><span class="sc-answer-label">Runtime</span><strong>${esc(p.execution?.runtime)}</strong></div><div class="sc-answer-cell"><span class="sc-answer-label">Engine / Method</span><strong>${esc(p.execution?.engine)} · ${esc(p.execution?.method)}</strong></div><div class="sc-answer-cell"><span class="sc-answer-label">Provenance</span><strong>${p.provenance?.provenanceHash?"captured":"not reported"}</strong></div></div><div class="sc-actions" style="padding:0 18px 16px"><button id="graph-result" class="sc-button">Graph</button><button id="copy-result" class="sc-button">Copy result</button></div><details class="sc-technical"><summary>Technical calculation object</summary><pre>${esc(fmt(p.technical?.calculationObject||{}))}</pre></details></section>`;}
function normalizationPreview(){
  const n=state.lastNormalization;
  if(!n)return `<div class="sc-normalization"><div class="sc-normalization-row"><span class="sc-muted">Notation preview</span><span class="sc-badge">conservative</span></div><div class="sc-normalization-detail">Type friendly mathematical notation; Workbench will show the normalized expression before execution.</div></div>`;
  const warnings=(n.ambiguities||[]).map(x=>`<div class="sc-normalization-warning">${esc(x)}</div>`).join("");
  return `<div class="sc-normalization ${n.changed?"changed":""}"><div class="sc-normalization-row"><span class="sc-muted">Normalized expression</span><span class="sc-badge">${n.changed?"derived":"unchanged"}</span></div><div class="sc-normalized-expression">${esc(n.normalizedExpression)}</div>${warnings}<details class="sc-normalization-detail"><summary>Transformation lineage</summary><pre>${esc(JSON.stringify(n.transformations||[],null,2))}</pre></details></div>`;
}
async function refreshNormalization(){
  const el=document.getElementById("calc-expression"); if(!el||!el.value.trim())return;
  try{
    const d=await api("/standalone/v1/calculator/normalize",{method:"POST",body:{expression:el.value,mode:"conservative"}});
    state.lastNormalization=d.normalization;
    const target=document.getElementById("normalization-preview"); if(target)target.innerHTML=normalizationPreview();
  }catch(e){ const target=document.getElementById("normalization-preview"); if(target)target.innerHTML=`<div class="sc-normalization-warning">${esc(String(e))}</div>`; }
}
function calculatorView(){const examples=["2+3*4","sin(x)^2 + cos(x)^2","(x+1)^2","exp(-x^2)"];return `<div class="sc-kicker">Calculator experience</div><h1 class="sc-title">Calculator</h1><p class="sc-copy">Enter an expression, choose an operation, and get a readable result backed by the canonical Workbench calculation object, verification, provenance, and reproducibility metadata.</p>${commonProjectBar()}${researchSessionBar()}<section class="sc-nl-panel"><div class="sc-nl-head"><div><strong>Intent-to-calculation planning</strong><div class="sc-muted">Plan first. Workbench exposes stages, assumptions, validation, alternatives, and lineage before canonical execution.</div></div><span class="sc-badge">conservative</span></div><label class="sc-field sc-field-wide">Describe the calculation<textarea id="nl-computation" class="sc-textarea" placeholder="Examples: differentiate x^3 + 2*x with respect to x; solve x + 2 = 5 for x; calculate sin(pi/4)">${esc(state.naturalLanguageText||"")}</textarea></label><div class="sc-actions"><button id="plan-interpret" class="sc-button">Build plan</button></div>${intentPlanHtml()}</section><section class="sc-panel"><div class="sc-math-input-wrap"><label class="sc-field sc-field-wide">Expression<textarea id="calc-expression" class="sc-textarea sc-expression" placeholder="Enter a mathematical expression">${esc(state.lastNormalization?.originalExpression||state.lastRequest?.calculation?.expression||"2+3*4")}</textarea></label><div class="sc-palette">${paletteHtml()}</div><div id="normalization-preview">${normalizationPreview()}</div></div><div class="sc-examples">${examples.map(x=>`<button class="sc-example" data-example="${esc(x)}">${esc(x)}</button>`).join("")}</div>${state.recent.length?`<div class="sc-recent"><span class="sc-muted">Recent:</span>${state.recent.map(x=>`<button class="sc-example" data-example="${esc(x)}">${esc(x)}</button>`).join("")}</div>`:""}<div class="sc-grid" style="margin-top:14px"><label class="sc-field">Operation<select id="calc-operation" class="sc-select"><option value="evaluate">Evaluate</option><option value="exact">Exact</option><option value="simplify">Simplify</option><option value="solve">Solve</option><option value="differentiate">Differentiate</option><option value="integrate-symbolic">Integrate</option><option value="root">Find Root</option></select></label><label id="variable-field" class="sc-field">Variable<input id="calc-variable" class="sc-input" value="x"></label><label id="guess-field" class="sc-field" style="display:none">Initial guess<input id="calc-guess" class="sc-input" type="number" value="1"></label><label class="sc-field">Title<input id="calc-title" class="sc-input" value="Calculation"></label><label class="sc-field"><span>Save result</span><select id="calc-save" class="sc-select"><option value="true">Yes</option><option value="false">No</option></select></label></div><div class="sc-actions"><button id="execute-calc" class="sc-button sc-button-primary">Execute</button><span class="sc-muted">⌘/Ctrl + Enter</span></div>${answerCard()}</section>`;}
function simpleView(title,body){return `<div class="sc-kicker">Standalone Workbench</div><h1 class="sc-title">${title}</h1>${body}`;}
function workspaceView(){const u=state.unifiedWorkspace||{};const c=u.counts||{};const session=u.researchSession||u.activeResearchSession||state.researchSessionSummary?.session||null;return simpleView("Unified Workbench Workspace",`${commonProjectBar()}${researchSessionBar()}<div class="sc-unified-hero"><section class="sc-panel"><div class="sc-kicker">One project · one research context</div><h2>${esc(session?.title||"Unified research workspace")}</h2><p class="sc-copy">${esc(session?.purpose||"Move between calculation, visualization, notebook history, and reproducibility without losing project or research-session context.")}</p><div class="sc-actions"><button class="sc-button sc-button-primary" data-workspace-route="${esc(session?.lastRoute||"calculator")}">Resume work</button><button class="sc-button" data-workspace-route="calculator">New calculation</button></div></section><section class="sc-panel"><h2>Research state</h2><div class="sc-unified-counts"><div class="sc-unified-count"><div class="sc-unified-count-value">${c.calculations||0}</div><span class="sc-muted">Calculations</span></div><div class="sc-unified-count"><div class="sc-unified-count-value">${c.graphs||0}</div><span class="sc-muted">Graphs</span></div><div class="sc-unified-count"><div class="sc-unified-count-value">${c.notebooks||0}</div><span class="sc-muted">Notebooks</span></div><div class="sc-unified-count"><div class="sc-unified-count-value">${c.notebookEntries||0}</div><span class="sc-muted">Entries</span></div><div class="sc-unified-count"><div class="sc-unified-count-value">${c.packages||0}</div><span class="sc-muted">Packages</span></div><div class="sc-unified-count"><div class="sc-unified-count-value">${c.researchSessions||0}</div><span class="sc-muted">Sessions</span></div></div></section></div><section class="sc-panel"><h2>Continue across Workbench</h2><div class="sc-unified-surface-grid">${unifiedContinuation("calculator","Calculator")}${unifiedContinuation("graphs","Graph Studio")}${unifiedContinuation("history","Notebook & Timeline")}${unifiedContinuation("packages","Reproducibility")}</div></section><section class="sc-panel"><h2>Recent research activity</h2><div class="sc-unified-activity">${unifiedActivity()}</div></section>`);}function graphsView(){const g=state.activeGraph||{};const series=g.series?.length?g.series:[{expression:state.lastRequest?.calculation?.expression||"sin(x)",label:"",variable:"x",visible:true,includeRoots:true,includeCriticalPoints:true,includeDerivative:false,includeIntegral:false}];return simpleView("Interactive Graph Studio",`${commonProjectBar()}${researchSessionBar()}<section class="sc-panel"><div class="sc-graph-toolbar"><label class="sc-field" style="min-width:280px">Saved graph<select id="graph-study-select" class="sc-select"><option value="">New graph</option>${state.savedGraphs.map(x=>`<option value="${esc(x.id)}" ${x.id===state.activeGraphId?"selected":""}>${esc(x.title)}</option>`).join("")}</select></label><button id="new-graph-study" class="sc-button">New</button><button id="save-graph-study" class="sc-button sc-button-primary">${state.activeGraphId?"Update":"Save"} Graph</button><button id="annotate-graph" class="sc-button" ${state.activeGraphId?"":"disabled"}>Annotate</button></div></section><div class="sc-graph-layout"><section class="sc-panel sc-graph-sidebar"><label class="sc-field">Title<input id="graph-title" class="sc-input" value="${esc(g.title||"Graph Study")}"></label><div class="sc-grid"><label class="sc-field">X start<input id="graph-start" class="sc-input" value="${esc(g.domain?.[0]??-6.28)}"></label><label class="sc-field">X end<input id="graph-end" class="sc-input" value="${esc(g.domain?.[1]??6.28)}"></label><label class="sc-field">Y start<input id="graph-y-start" class="sc-input" value="${esc(g.yDomain?.[0]??-5)}"></label><label class="sc-field">Y end<input id="graph-y-end" class="sc-input" value="${esc(g.yDomain?.[1]??5)}"></label><label class="sc-field">Samples<input id="graph-samples" class="sc-input" type="number" min="25" max="5000" value="${esc(g.samples||401)}"></label></div><div class="sc-graph-toolbar"><strong>Series</strong><button id="add-graph-series" class="sc-button">Add function</button></div><div id="graph-series-list" class="sc-graph-series-list">${series.map((x,i)=>graphSeriesRow(x,i)).join("")}</div><div class="sc-graph-annotation-list">${(g.annotations||[]).map(a=>`<div class="sc-graph-annotation">${esc(a.label)}</div>`).join("")}</div></section><section class="sc-panel sc-graph-canvas"><div class="sc-graph-toolbar"><button id="render-graph" class="sc-button sc-button-primary">${state.activeGraphId?"Render Saved Graph":"Preview"}</button><span class="sc-muted">Backend sampled | SVG rendered | session linked</span></div><div id="graph-output" class="math-view-grid"></div></section></div>`);}
function historyView(){const notebooks=state.notebooks.map(n=>`<option value="${esc(n.id)}" ${n.id===state.activeNotebookId?"selected":""}>${esc(n.title)}</option>`).join("");return simpleView("Notebook & Research Timeline",`${commonProjectBar()}${researchSessionBar()}<section class="sc-panel"><div class="sc-timeline-toolbar"><label class="sc-field">Timeline scope<select id="timeline-scope" class="sc-select"><option value="session" ${state.timelineScope==="session"?"selected":""}>Research session</option><option value="project" ${state.timelineScope==="project"?"selected":""}>Project</option></select></label><label class="sc-field sc-history-filter">Filter<select id="timeline-filter" class="sc-select"><option value="all">All objects</option><option value="calculation">Calculations</option><option value="graph">Graphs</option><option value="notebook-entry">Notebook entries</option><option value="package">Packages</option><option value="session-activity">Session activity</option></select></label><button id="refresh-timeline" class="sc-button">Refresh</button></div></section><div class="sc-notebook-workspace"><section class="sc-panel"><h2>Notebook</h2><label class="sc-field">Active notebook<select id="notebook-select" class="sc-select"><option value="">No notebook</option>${notebooks}</select></label><div class="sc-actions"><button id="new-notebook-history" class="sc-button">New Notebook</button><button id="add-notebook-note" class="sc-button sc-button-primary" ${state.activeNotebookId?"":"disabled"}>Add Note</button></div><div class="sc-actions"><button data-attach-type="calculation" class="sc-button" ${state.activeNotebookId&&state.calculations.length?"":"disabled"}>Attach calculation</button><button data-attach-type="graph" class="sc-button" ${state.activeNotebookId&&state.savedGraphs.length?"":"disabled"}>Attach graph</button><button data-attach-type="package" class="sc-button" ${state.activeNotebookId&&state.packages.length?"":"disabled"}>Attach package</button></div><div class="sc-notebook-list">${state.notebookEntries.map(e=>`<div class="sc-notebook-entry"><div class="sc-notebook-entry-head"><strong>${esc(e.title||e.kind)}</strong><span class="sc-badge">${esc(e.kind)}</span></div><div class="sc-notebook-entry-body">${esc(e.markdown||"")}</div></div>`).join("")||'<p class="sc-muted">No notebook entries.</p>'}</div></section><section class="sc-panel"><h2>Research timeline</h2><div class="sc-timeline">${state.researchTimeline.map((e,i)=>`<div class="sc-timeline-item"><span class="sc-timeline-time">${esc(new Date((e.createdAt||0)*1000).toLocaleString())}</span><span class="sc-badge">${esc(e.kind)}</span><div><div class="sc-timeline-title">${esc(e.title)}</div><div class="sc-muted">${esc(e.objectType||"")}</div></div><button class="sc-button" data-timeline-index="${i}">Open</button></div>`).join("")||'<p class="sc-muted">No timeline events.</p>'}</div></section></div>`);}
function packagesView(){const p=state.activePackage||{};const rs=p.replaySummary||{};return simpleView("Reproducibility Package Workspace",`${commonProjectBar()}${researchSessionBar()}<div class="sc-package-layout"><section class="sc-panel"><div class="sc-actions"><button id="create-package" class="sc-button sc-button-primary" ${state.projectId&&state.lastRequest?"":"disabled"}>Capture last calculation</button></div><div class="sc-package-list">${state.packages.map(x=>`<div class="sc-package-row ${x.id===state.activePackageId?"active":""}" data-package-id="${esc(x.id)}"><strong>${esc(x.title)}</strong><div class="sc-package-status"><span class="sc-badge">${esc(x.integrityStatus||"unchecked")}</span><span class="sc-badge">${esc(x.lastReplayStatus||"not-replayed")}</span></div></div>`).join("")||'<p class="sc-muted">No reproducibility packages.</p>'}</div></section><section class="sc-panel">${state.activePackageId?`<label class="sc-field">Title<input id="package-title" class="sc-input" value="${esc(p.title||"")}"></label><label class="sc-field">Notes<textarea id="package-notes" class="sc-textarea">${esc(p.notes||"")}</textarea></label><div class="sc-actions"><button id="save-package-meta" class="sc-button">Save metadata</button><button id="verify-package" class="sc-button">Verify integrity</button><label class="sc-field">Replay mode<select id="package-replay-mode" class="sc-select"><option value="strict">Strict</option><option value="input-plan-result">Input / plan / result</option><option value="result-only">Result only</option></select></label><button id="replay-package" class="sc-button sc-button-primary">Replay</button><button id="export-package" class="sc-button">Export JSON</button></div><div class="sc-package-grid"><div class="sc-package-cell"><span class="sc-muted">Integrity</span><strong>${esc(p.integrityStatus||"unchecked")}</strong></div><div class="sc-package-cell"><span class="sc-muted">Replay</span><strong>${esc(rs.status||"not-replayed")}</strong></div><div class="sc-package-cell"><span class="sc-muted">Runtime manifest</span><strong>${rs.runtimeManifestMatch===true?"match":rs.runtimeManifestMatch===false?"different":"not replayed"}</strong></div></div><details><summary>Provenance & manifest</summary><div class="sc-hash">Envelope: ${esc(p.envelopeHash||"")}</div><div class="sc-hash">Request: ${esc(p.requestHash||"")}</div><div class="sc-hash">Source calculation: ${esc(p.sourceCalculationObjectHash||"")}</div><div class="sc-hash">Runtime manifest: ${esc(p.runtimeManifestHash||"")}</div></details>${state.packageComparison?`<section><h3>Replay comparison</h3><div class="sc-package-status"><span class="sc-badge">${state.packageComparison.reproducible?"reproducible":"divergent"}</span><span class="sc-badge">${esc(state.packageComparison.comparisonMode)}</span><span class="sc-badge">${state.packageComparison.runtimeManifestMatch?"runtime match":"runtime changed"}</span></div><table class="sc-comparison-table"><thead><tr><th>Field</th><th>Status</th><th>Expected</th><th>Observed</th></tr></thead><tbody>${comparisonRows()}</tbody></table><div class="sc-hash">Certificate: ${esc(state.packageComparison.certificateHash||"")}</div></section>`:""}`:'<p class="sc-muted">Select or create a package.</p>'}</section></div>`);}function settingsView(){return simpleView("Settings",`<section class="sc-panel"><pre>${esc(fmt({version:WORKBENCH_CONFIG.version,frontendVersion:state.frontendVersion,backendVersion:state.backendVersion,versionAligned:state.versionAligned,projectId:state.projectId,session:state.session}))}</pre></section>`);}
function shell(c){const tabs=[["calculator","Calculator"],["workspace","Workspace"],["graphs","Graphs"],["history","History"],["packages","Packages"],["settings","Settings"]];return `<div class="sc-shell"><header class="sc-topbar"><div class="sc-brand">Sustainable Catalyst / Workbench</div><div class="sc-status">${state.online?"API ONLINE":"API OFFLINE"} · ${WORKBENCH_CONFIG.version} · ${state.versionAligned?"VERSION ALIGNED":"VERSION CHECK"}</div></header><div class="sc-main"><nav class="sc-nav">${tabs.map(([r,l])=>`<button data-nav="${r}" class="${state.route===r?"active":""}">${l}</button>`).join("")}</nav><main class="sc-workspace">${c}</main></div><footer class="sc-footer">Calculator experience · FastAPI authority · WordPress optional</footer>${state.message?`<div class="sc-toast sc-success">${esc(state.message)}</div>`:""}${state.error?`<div class="sc-toast sc-error">${esc(state.error)}</div>`:""}</div>`;}
function render(){const v={calculator:calculatorView,workspace:workspaceView,graphs:graphsView,history:historyView,packages:packagesView,settings:settingsView};document.getElementById("sc-workbench-app").innerHTML=shell((v[state.route]||calculatorView)());bind();if(state.route==="graphs"&&state.lastViewSpec)drawGraph();}
function syncOperationFields(){const op=document.getElementById("calc-operation")?.value;const vf=document.getElementById("variable-field"),gf=document.getElementById("guess-field");if(vf)vf.style.display=["solve","differentiate","integrate-symbolic","root"].includes(op)?"flex":"none";if(gf)gf.style.display=op==="root"?"flex":"none";}
function bind(){document.querySelectorAll("[data-nav]").forEach(b=>b.onclick=()=>nav(b.dataset.nav));document.querySelectorAll("[data-example]").forEach(b=>b.onclick=()=>{const e=document.getElementById("calc-expression");if(e)e.value=b.dataset.example;});document.querySelectorAll("[data-math-insert]").forEach(b=>b.onclick=()=>{const e=document.getElementById("calc-expression");if(e){insertAtCursor(e,b.dataset.mathInsert);refreshNormalization();}});const rss=document.getElementById("research-session-select");if(rss)rss.onchange=()=>activateResearchSession(rss.value);const nrs=document.getElementById("new-research-session");if(nrs)nrs.onclick=()=>createResearchSession().catch(e=>toast(String(e),true));const ps=document.getElementById("project-select");if(ps)ps.onchange=async()=>{state.projectId=ps.value||null;state.researchSessionId=null;state.activeGraphId=null;state.activeGraph=null;state.activeNotebookId=null;state.activePackageId=null;state.activePackage=null;state.packageComparison=null;sessionStorage.removeItem("scwb.research.session.id");sessionStorage.removeItem("scwb.graph.id");sessionStorage.removeItem("scwb.notebook.id");sessionStorage.removeItem("scwb.package.id");if(state.projectId)sessionStorage.setItem("scwb.project.id",state.projectId);await loadProjectData();render();};const np=document.getElementById("new-project");if(np)np.onclick=createProject;const op=document.getElementById("calc-operation");if(op){op.onchange=syncOperationFields;syncOperationFields();}const ex=document.getElementById("execute-calc");if(ex)ex.onclick=executeCalculation;const pi=document.getElementById("plan-interpret");if(pi)pi.onclick=()=>planNaturalLanguage().catch(e=>toast(String(e),true));const pa=document.getElementById("plan-apply");if(pa)pa.onclick=()=>{try{applyIntentPlan();}catch(e){toast(String(e),true);}};const pc=document.getElementById("plan-clear");if(pc)pc.onclick=()=>{state.intentPlan=null;state.intentPlanApplied=false;state.executionExplanation=null;state.naturalLanguageText="";render();};const ce=document.getElementById("calc-expression");if(ce){let nt=null;ce.oninput=()=>{clearTimeout(nt);nt=setTimeout(refreshNormalization,180);};ce.onkeydown=e=>{if(e.key==="Enter"&&(e.metaKey||e.ctrlKey)){e.preventDefault();executeCalculation();}};setTimeout(refreshNormalization,0);};const gr=document.getElementById("graph-result");if(gr)gr.onclick=()=>nav("graphs");const cp=document.getElementById("copy-result");if(cp)cp.onclick=()=>navigator.clipboard.writeText(state.lastPresentation?.primaryResult?.display||"").then(()=>toast("Result copied."));const gs=document.getElementById("graph-study-select");if(gs)gs.onchange=()=>activateGraphStudy(gs.value).catch(e=>toast(String(e),true));const ng=document.getElementById("new-graph-study");if(ng)ng.onclick=()=>{state.activeGraphId=null;state.activeGraph=null;state.lastViewSpec=null;sessionStorage.removeItem("scwb.graph.id");render();};const sg=document.getElementById("save-graph-study");if(sg)sg.onclick=()=>saveActiveGraph().catch(e=>toast(String(e),true));const ag=document.getElementById("annotate-graph");if(ag)ag.onclick=()=>annotateActiveGraph().catch(e=>toast(String(e),true));const addg=document.getElementById("add-graph-series");if(addg)addg.onclick=()=>addGraphSeries();bindGraphSeriesButtons();const rg=document.getElementById("render-graph");if(rg)rg.onclick=()=>{if(state.activeGraphId)renderSavedGraph().then(()=>{render();drawGraph();}).catch(e=>toast(String(e),true));else renderGraph();};const nn=document.getElementById("new-notebook");if(nn)nn.onclick=createNotebook;const ts=document.getElementById("timeline-scope");if(ts)ts.onchange=async()=>{state.timelineScope=ts.value;await loadResearchTimeline();render();};const tf=document.getElementById("timeline-filter");if(tf){tf.value=state.timelineFilter;tf.onchange=async()=>{state.timelineFilter=tf.value;await loadResearchTimeline();render();};}const rt=document.getElementById("refresh-timeline");if(rt)rt.onclick=()=>loadResearchTimeline().then(render).catch(e=>toast(String(e),true));const ns=document.getElementById("notebook-select");if(ns)ns.onchange=()=>activateNotebook(ns.value).catch(e=>toast(String(e),true));const nnh=document.getElementById("new-notebook-history");if(nnh)nnh.onclick=createNotebook;const ann=document.getElementById("add-notebook-note");if(ann)ann.onclick=()=>addNotebookNote().catch(e=>toast(String(e),true));document.querySelectorAll("[data-attach-type]").forEach(b=>b.onclick=()=>attachSelectedObject(b.dataset.attachType).catch(e=>toast(String(e),true)));document.querySelectorAll("[data-timeline-index]").forEach(b=>b.onclick=()=>openTimelineItem(state.researchTimeline[Number(b.dataset.timelineIndex)]));const pk=document.getElementById("create-package");if(pk)pk.onclick=createPackage;document.querySelectorAll("[data-workspace-route]").forEach(b=>b.onclick=()=>unifiedHandoff(b.dataset.workspaceRoute,null,b.dataset.objectId||null));document.querySelectorAll("[data-package-id]").forEach(x=>x.onclick=()=>activatePackage(x.dataset.packageId).catch(e=>toast(String(e),true)));const vp=document.getElementById("verify-package");if(vp)vp.onclick=()=>verifyActivePackage().catch(e=>toast(String(e),true));const rp=document.getElementById("replay-package");if(rp)rp.onclick=()=>replayActivePackage().catch(e=>toast(String(e),true));const sp=document.getElementById("save-package-meta");if(sp)sp.onclick=()=>savePackageMetadata().catch(e=>toast(String(e),true));const ep=document.getElementById("export-package");if(ep)ep.onclick=downloadPackageExport;}
async function createProject(){const name=prompt("Project name","Workbench Project");if(!name)return;try{const d=await api("/standalone/v1/projects",{method:"POST",body:{name,description:"Created from Workbench v13.4",metadata:{interfaceVersion:"13.4.0"}}});state.projectId=d.project.id;await loadProjects();await loadProjectData();toast("Project created.");}catch(e){toast(String(e),true);}}
function rememberExpression(x){state.recent=[x,...state.recent.filter(v=>v!==x)].slice(0,WORKBENCH_CONFIG.state.recentExpressionLimit||8);localStorage.setItem("scwb.recent.expressions",JSON.stringify(state.recent));}
async function executeCalculation(){try{const originalExpression=document.getElementById("calc-expression").value.trim();if(!originalExpression)throw new Error("Enter an expression.");const nd=await api("/standalone/v1/calculator/normalize",{method:"POST",body:{expression:originalExpression,mode:"conservative"}});state.lastNormalization=nd.normalization;if((state.lastNormalization.ambiguities||[]).length)throw new Error("Ambiguous notation: use explicit multiplication (*) before executing.");const expression=state.lastNormalization.normalizedExpression;const operation=document.getElementById("calc-operation").value,variable=document.getElementById("calc-variable")?.value.trim()||"x",title=document.getElementById("calc-title").value.trim()||"Calculation",saveResult=document.getElementById("calc-save").value==="true";if(saveResult&&!state.projectId)throw new Error("Create or select a project before saving.");const calculation={operation,expression};if(["solve","differentiate","integrate-symbolic","root"].includes(operation))calculation.variable=variable;if(operation==="root")calculation.initialGuess=Number(document.getElementById("calc-guess").value||1);const requestedResultType=["evaluate","root"].includes(operation)?"numeric":operation==="exact"?"exact":"symbolic";const calculationRequest={calculation,requestedResultType,requireVerification:true,requireProvenance:true};state.lastRequest=calculationRequest;rememberExpression(originalExpression);const d=await api("/standalone/v1/calculator/execute",{method:"POST",body:{calculationRequest,projectId:state.projectId,saveResult,title,tags:["standalone-v13.3"],metadata:{interfaceVersion:"13.3.0",originalExpression,normalizedExpression:expression,normalizationHash:state.lastNormalization?.normalizationHash||null}}});state.lastCalculation=d.calculationObject;const p=await api("/standalone/v1/calculator/presentation",{method:"POST",body:{calculationObject:d.calculationObject,title,saved:Boolean(d.saved),savedCalculationId:d.savedCalculation?.id||null}});state.lastPresentation=p.presentation;if(state.intentPlan&&state.intentPlanApplied){await explainLastExecution();}await recordSessionActivity("calculation",title,"calculation",d.savedCalculation?.id||null,"calculator",{operation,originalExpression,normalizedExpression:expression});await loadProjectData();render();toast(saveResult?"Calculation executed and saved.":"Calculation executed.");}catch(e){toast(String(e),true);}}
async function renderGraph(){try{const expression=document.getElementById("graph-expression").value.trim(),variable=document.getElementById("graph-variable").value.trim()||"x",a=Number(document.getElementById("graph-start").value),b=Number(document.getElementById("graph-end").value);const d=await api("/standalone/v1/renderer/view-spec",{method:"POST",body:{graphing:{operation:"function-plot",expression,variable,domain:[a,b],samples:401,includeRoots:true,includeCriticalPoints:true,includeDerivative:false,includeIntegral:false}}});state.lastViewSpec=d.viewSpec||d.views||d;render();drawGraph();}catch(e){toast(String(e),true);}}function drawGraph(){const t=document.getElementById("graph-output");if(t&&state.lastViewSpec)renderViewSpec(t,state.lastViewSpec);}
async function createNotebook(){if(!state.projectId)return;const title=prompt("Notebook title","Research Notebook");if(!title)return;const d=await api("/standalone/v1/notebooks",{method:"POST",body:{projectId:state.projectId,title,description:"",metadata:{interfaceVersion:"13.6.0",researchSessionId:state.researchSessionId||null}}});state.activeNotebookId=d.notebook.id;sessionStorage.setItem("scwb.notebook.id",state.activeNotebookId);await recordSessionActivity("notebook","Notebook created","notebook",state.activeNotebookId,"history",{title});await loadProjectData();toast("Notebook created.");}
async function createPackage(){if(!state.projectId||!state.lastRequest)return;const d=await api("/standalone/v1/reproducibility/packages",{method:"POST",body:{projectId:state.projectId,calculationRequest:state.lastRequest,calculationObject:state.lastCalculation,title:"Workbench v13.7 Reproducibility Package",notes:"Captured from Reproducibility Package Workspace",metadata:{interfaceVersion:"13.7.0",researchSessionId:state.researchSessionId}}});state.activePackageId=d.package.id;sessionStorage.setItem("scwb.package.id",state.activePackageId);await api(`/standalone/v1/reproducibility/workspace/${encodeURIComponent(state.activePackageId)}`,{method:"PATCH",body:{researchSessionId:state.researchSessionId||null,metadata:{interfaceVersion:"13.7.0",researchSessionId:state.researchSessionId||null}}});await recordSessionActivity("package","Reproducibility package created","package",state.activePackageId,"packages",{});await loadProjectData();toast("Reproducibility package created.");}
async function bootstrap(){try{state.online=Boolean((await rawRequest("/health",{auth:false})).ok);await verifyVersionAlignment();await bootstrapSession();await loadProjects();await loadProjectData();}catch(e){state.error=String(e);}render();}bootstrap();
