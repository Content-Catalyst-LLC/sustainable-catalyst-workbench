"""ERW 1.1 authenticated saved-project explorer and SVG scientific figure export.
No anonymous access to stored objects; no publishing or crediting.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from .release import APP_VERSION
from .v1220 import _owner,list_projects,get_project,list_calculations,get_calculation
from .erw_v010 import PROJECT_KEY
from .v510 import content_hash
router=APIRouter(tags=["erw-1.1.0"])
KINDS={
 "sc.erw.visual-research-package.v0.6.0":"visualization",
 "sc.erw.equations-maps-diagrams.v0.7.0":"diagrams"}
def projects_for(owner):
    return [p for p in list_projects(owner) if p.get("metadata",{}).get("researchId")==PROJECT_KEY]
def project_for(project_id,owner):
    p=get_project(project_id,owner)
    if p.get("metadata",{}).get("researchId")!=PROJECT_KEY:raise HTTPException(404,detail="ERW project not found")
    return p
def figures_for(project_id,owner):
    project_for(project_id,owner)
    result=[]
    for saved in list_calculations(project_id,owner):
        obj=saved.get("calculationObject",{})
        kind=KINDS.get(obj.get("schema"))
        if kind:
            digest=obj.get("calculationObjectHash")
            valid=isinstance(digest,str) and digest==content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"})
            result.append({"id":saved["id"],"title":saved["title"],"kind":kind,
                           "schema":obj["schema"],"objectHash":digest,"digestConsistent":valid})
    return result
@router.get("/erw/v1.1.0/status")
def status():return {"ok":True,"extension":"erw","extensionVersion":"1.1.0","workbenchVersion":APP_VERSION,
                       "signedSessionRequired":True,"publicationEnabled":False,"verifiedCDR":False}
@router.get("/erw/v1.1.0/projects")
def projects(authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"projects":projects_for(owner),"ownerScoped":True}
@router.get("/erw/v1.1.0/projects/{project_id}/figures")
def figures(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"project":project_for(project_id,owner),"figures":figures_for(project_id,owner)}
@router.get("/erw/v1.1.0/projects/{project_id}/figures/{calculation_id}")
def figure(project_id:str,calculation_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization);project_for(project_id,owner)
    saved=get_calculation(calculation_id,owner)
    if saved.get("projectId")!=project_id:raise HTTPException(404,detail="Figure not in selected project")
    obj=saved.get("calculationObject",{})
    if obj.get("schema") not in KINDS:raise HTTPException(404,detail="Not an ERW visual research object")
    h=obj.get("calculationObjectHash")
    if not isinstance(h,str) or h!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        raise HTTPException(409,detail="Stored figure hash mismatch")
    if obj.get("verifiedCDR") is not False or obj.get("netDurableAtmosphericRemoval") is not None:
        raise HTTPException(409,detail="Unsupported scientific verification status")
    return {"ok":True,"figure":obj,"savedCalculationId":calculation_id,
            "exportCaution":"Illustrative research visualization only. Not measured or verified atmospheric carbon removal."}
@router.get("/erw/v1.1.0/explorer",response_class=HTMLResponse)
def explorer():return HTMLResponse(EXPLORER)
EXPLORER=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ERW Research Explorer · Sustainable Catalyst</title>
<style>body{font:16px system-ui,sans-serif;max-width:1100px;margin:auto;padding:24px;color:#171717;background:#fafafa}h1{font-size:1.6rem}label{display:block;margin-top:12px}input,select,button{padding:10px;font:inherit;margin:4px 0}input{width:min(600px,90%)}button{background:#111;color:white;border:0;cursor:pointer}button:disabled{background:#aaa}#figure svg{max-width:100%;height:auto;border:1px solid #ddd;background:white}.notice{padding:12px;border-left:4px solid #950000;background:#fff}#status{white-space:pre-wrap}small{color:#555}</style>
</head><body><h1>Sustainable Catalyst · ERW Research Explorer</h1>
<p class="notice">Private, signed-session research only. Hypothetical model outputs are not verified atmospheric CO₂ removal. No publication or outbound submission.</p>
<label for="token">Workbench signed-session bearer token (kept only in this tab's memory)</label><input id="token" type="password" autocomplete="off" spellcheck="false"><button id="load">Load my ERW projects</button>
<label for="projects">Project</label><select id="projects"><option>Select project</option></select><button id="loadfig">Load visual objects</button>
<label for="figures">Saved visual or equation object</label><select id="figures"><option>Select object</option></select>
<label for="view">Visual</label><select id="view"><option value="pathway">Carbon pathway (conceptual)</option><option value="scenarios">Scenario trajectories</option><option value="mrv">MRV evidence matrix</option><option value="equations">Four model equations</option><option value="lifecycle">Lifecycle category burdens</option></select>
<button id="render">Render SVG</button><button id="export" disabled>Export SVG</button><p id="status" role="status"></p><div id="figure"></div>
<p><small>Figures are generated locally in your browser from the selected saved object. SVG files contain source schema and hash notes; no browser-side project information is sent to third parties. Export is SVG (Word-compatible); PNG conversion is not included in this release.</small></p>
<script>
(()=>{'use strict';
const E=id=>document.getElementById(id);let token='',catalog=[],payload=null,svg='';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const txt=(x,y,s,size=18,weight='normal')=>'<text x="'+x+'" y="'+y+'" font-size="'+size+'" font-weight="'+weight+'" fill="#171717">'+esc(s)+'</text>';
const box=(x,y,w,h,fill='#edf4f0')=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="8" fill="'+fill+'" stroke="#777"/>';
const line=(x,y,a,b)=>'<path d="M'+x+' '+y+' L'+a+' '+b+'" stroke="#444" stroke-width="2" fill="none" marker-end="url(#arrow)"/>';
const wrap=(body,title,hash)=>'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="680" viewBox="0 0 1100 680" role="img" aria-label="'+esc(title)+'"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#444"/></marker></defs><rect width="1100" height="680" fill="white"/>'+txt(35,47,title,25,'bold')+body+txt(35,646,'Illustrative / not verified carbon removal · object hash '+String(hash||'').slice(0,20),15)+'</svg>';
function diagram(d){const ns=d.materialFlow?.nodes||[],edges=d.materialFlow?.edges||[];if(!ns.length)throw Error('No material-flow nodes');let body='';const coords={};ns.forEach((n,i)=>{let x=45+(i%3)*365,y=100+Math.floor(i/3)*218;coords[n.id]=[x+155,y+55];body+=box(x,y,310,110)+txt(x+14,y+54,n.label,16,'bold')});edges.forEach(e=>{const a=coords[e.from],b=coords[e.to];if(a&&b)body+=line(a[0],a[1]+30,b[0],b[1]-30)});return body}
function pathway(){const nodes=['Atmospheric / recently cycled CO₂','Basalt + soil water: dissolution','Ca²⁺, Mg²⁺ and bicarbonate','Drainage → rivers → ocean','Potential long-lived storage'];let b='';nodes.forEach((n,i)=>{let y=95+i*102;b+=box(230,y,640,67,i===4?'#fff0e8':'#e8f3ed')+txt(250,y+39,n,21,'bold');if(i<4)b+=line(550,y+67,550,y+99)});return b+txt(60,620,'Carbon source, acid source, life-cycle and downstream losses require separate verification.',16)}
function chart(v){const s=v.views.find(x=>x.id==='scenario-trajectories');if(!s)throw Error('Scenario trajectories missing');let series=s.series||[];let b='',max=1;series.forEach(t=>(t.points||[]).forEach(p=>{max=Math.max(max,+p.incrementalPotentialProxyTonnesCO2||0)}));b+=line(100,545,1040,545)+line(100,545,100,115);series.forEach((t,j)=>{let pts=t.points||[];let color=['#27734b','#164e9e','#aa4235','#666'][j%4],poly=pts.map((p,i)=>[(130+i*870/Math.max(1,pts.length-1)),545-(+p.incrementalPotentialProxyTonnesCO2/max)*390].join(',')).join(' ');b+='<polyline points="'+poly+'" fill="none" stroke="'+color+'" stroke-width="4"/>'+txt(140+j*265,590,t.rateTonnesPerHa+' t/ha',18)});return b+txt(130,95,'Incremental modeled potential proxy over study years (tonnes CO₂)',19)}
function matrix(v){const m=v.views.find(x=>x.id==='mrv-evidence-matrix');if(!m)throw Error('MRV matrix missing');let cells=m.cells||[],b='';cells.slice(0,11).forEach((c,i)=>{let y=110+i*42;b+=box(40,y,1020,39,i%2?'#f5f5f5':'#e8f3ed')+txt(53,y+26,c.requirement.slice(0,49),15)+txt(600,y+26,c.state.slice(0,20),15)+txt(800,y+26,c.evidenceClass.slice(0,22),15)});return b}
function eqs(d){let b='';(d.equations||[]).slice(0,4).forEach((e,i)=>{let y=120+i*117;b+=box(50,y,1000,100)+txt(70,y+33,e.label,18,'bold')+txt(70,y+76,e.latex,23)});return b}
function lifecycle(v){const s=v.views.find(x=>x.id==='lifecycle-breakdown');if(!s)throw Error('Lifecycle breakdown missing');let bars=s.bars||[],max=Math.max(1,...bars.map(x=>+x.tonnesCO2e||0)),b='';bars.slice(0,8).forEach((p,i)=>{let y=100+i*58,w=(+p.tonnesCO2e/max)*520;b+=txt(40,y+25,p.category.slice(0,35),17)+ '<rect x="380" y="'+y+'" width="'+w+'" height="36" fill="#27684e"/>'+txt(390+w,y+25,p.tonnesCO2e+' tCO₂e',15)});return b}
async function api(path){if(!token)throw Error('Enter a Workbench signed-session token');let r=await fetch(path,{headers:{Authorization:'Bearer '+token},cache:'no-store'});if(!r.ok)throw Error('API HTTP '+r.status+' '+(await r.text()).slice(0,300));return r.json()}
function options(id,arr,fn){E(id).replaceChildren(...arr.map(v=>{let o=document.createElement('option');o.value=fn(v);o.textContent=v.name||v.title||v.id;return o}))}
function error(e){E('status').textContent=e.message||String(e)}
E('load').onclick=async()=>{try{token=E('token').value.trim().replace(/^Bearer\s+/i,'');E('token').value='';let d=await api('/erw/v1.1.0/projects');options('projects',d.projects,x=>x.id);E('status').textContent=d.projects.length+' owner-scoped ERW project(s) found. Other session identities cannot view certification studies.'}catch(e){error(e)}};
E('loadfig').onclick=async()=>{try{let d=await api('/erw/v1.1.0/projects/'+encodeURIComponent(E('projects').value)+'/figures');catalog=d.figures;options('figures',catalog,x=>x.id);E('status').textContent=catalog.length+' saved figure objects';}catch(e){error(e)}};
E('render').onclick=async()=>{try{let id=E('figures').value,entry=catalog.find(x=>x.id===id);if(!entry)throw Error('Select a saved visual object');if(!entry.digestConsistent)throw Error('Stored object digest mismatch');let d=await api('/erw/v1.1.0/projects/'+encodeURIComponent(E('projects').value)+'/figures/'+encodeURIComponent(id));payload=d.figure;let view=E('view').value;if(['scenarios','mrv','lifecycle'].includes(view)&&entry.kind!=='visualization')throw Error('Select a v0.6 visual research object');if(view==='equations'&&entry.kind!=='diagrams')throw Error('Select a v0.7 equation/diagram object');let body=view==='pathway'?pathway():view==='scenarios'?chart(payload):view==='mrv'?matrix(payload):view==='equations'?eqs(payload):lifecycle(payload);svg=wrap(body,'ERW · '+view,payload.calculationObjectHash);E('figure').replaceChildren();let parser=new DOMParser().parseFromString(svg,'image/svg+xml');if(parser.querySelector('parsererror'))throw Error('Invalid SVG');E('figure').append(document.importNode(parser.documentElement,true));E('export').disabled=false;E('status').textContent='Rendered from '+entry.schema+'; scientific status: hypothetical / unverified.'}catch(e){E('export').disabled=true;error(e)}};
E('export').onclick=()=>{if(!svg)return;let a=document.createElement('a'),u=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));a.href=u;a.download='sustainable-catalyst-erw-'+E('view').value+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
})();
</script></body></html>"""
