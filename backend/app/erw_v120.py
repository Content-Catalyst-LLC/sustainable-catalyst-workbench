"""ERW 1.2 Integrated Research Report Workspace.
Owner-scoped, append-only draft and table snapshots. No publication or verified CDR.
"""
from __future__ import annotations
from typing import Optional, Literal
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .v510 import content_hash
from .v1220 import _owner, get_calculation, list_calculations, save_calculation, SavedCalculationCreateRequest
from .erw_v110 import project_for, projects_for
from .erw_v010 import PROJECT_KEY

router = APIRouter(tags=["erw-1.2.0"])
REPORT = "sc.erw.report-workspace.v1.2.0"
TABLE = "sc.erw.research-table.v1.2.0"
VIS = {"sc.erw.visual-research-package.v0.6.0", "sc.erw.equations-maps-diagrams.v0.7.0"}
class SourceRef(BaseModel):
    calculationId: str = Field(min_length=1, max_length=100)
    objectHash: str = Field(min_length=16, max_length=200)
class TableRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    columns: list[str] = Field(min_length=1, max_length=12)
    rows: list[list[str]] = Field(min_length=1, max_length=100)
    caption: str = Field(default="", max_length=1200)
    sourceRefs: list[SourceRef] = Field(default_factory=list, max_length=12)
    evidenceStatus: Literal["hypothetical", "literature-derived", "measured"] = "hypothetical"
class Section(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    heading: str = Field(min_length=1, max_length=200)
    text: str = Field(default="", max_length=25000)
class Insert(BaseModel):
    sectionId: str = Field(min_length=1, max_length=80)
    kind: Literal["table", "figure", "equation"]
    source: SourceRef
    caption: str = Field(default="", max_length=1200)
class ReportRequest(BaseModel):
    title: str = Field(min_length=5, max_length=250)
    authors: list[str] = Field(default_factory=list, max_length=20)
    sections: list[Section] = Field(min_length=1, max_length=20)
    inserts: list[Insert] = Field(default_factory=list, max_length=60)
    bibliography: str = Field(default="", max_length=20000)

def valid_source(project_id, owner, ref: SourceRef, allowed: set[str]):
    row = get_calculation(ref.calculationId, owner)
    if row.get("projectId") != project_id:
        raise HTTPException(404, detail="Source not in this project")
    obj = row.get("calculationObject", {})
    digest = obj.get("calculationObjectHash")
    if digest != ref.objectHash or digest != content_hash({k: v for k, v in obj.items() if k != "calculationObjectHash"}):
        raise HTTPException(409, detail="Source hash is stale or inconsistent")
    if obj.get("schema") not in allowed or obj.get("researchId") != PROJECT_KEY:
        raise HTTPException(422, detail="Unsupported source schema")
    if obj.get("verifiedCDR") is not False or obj.get("netDurableAtmosphericRemoval") is not None:
        raise HTTPException(422, detail="Unsupported scientific verification status")
    return obj

def store(project_id, owner, obj, label):
    row = save_calculation(SavedCalculationCreateRequest(
        projectId=project_id, title=label, calculationObject=obj,
        tags=["erw", "report-workspace", "unpublished"],
        metadata={"researchId":PROJECT_KEY, "publicationEnabled":False}), owner)
    return {"ok":True, "id":row["id"], "object":obj, "immutableSnapshot":True}

def make_table(project_id, owner, req: TableRequest):
    project_for(project_id, owner)
    if len(set(req.columns)) != len(req.columns) or any(not c.strip() for c in req.columns):
        raise HTTPException(422, detail="Column labels must be distinct and nonempty")
    if any(len(r) != len(req.columns) for r in req.rows):
        raise HTTPException(422, detail="Each table row must match the column count")
    if any(len(cell) > 2000 for r in req.rows for cell in r):
        raise HTTPException(422, detail="Table cell exceeds 2000 characters")
    for ref in req.sourceRefs:
        valid_source(project_id, owner, ref, VIS | {TABLE, "sc.erw.academic-report.v0.8.0"})
    obj={"schema":TABLE,"researchId":PROJECT_KEY,"projectId":project_id,
         "title":req.title,"columns":req.columns,"rows":req.rows,"caption":req.caption,
         "sourceRefs":[r.model_dump() for r in req.sourceRefs],
         "evidenceStatus":req.evidenceStatus,"sourceIntegrityVerifiedExternally":False,
         "status":"draft-unpublished","publicationEnabled":False,
         "verifiedCDR":False,"netDurableAtmosphericRemoval":None}
    obj["calculationObjectHash"]=content_hash(obj)
    return obj

def make_report(project_id,owner,req:ReportRequest):
    project_for(project_id,owner)
    ids=[s.id for s in req.sections]
    if len(set(ids)) != len(ids):
        raise HTTPException(422,detail="Duplicate section IDs")
    for ins in req.inserts:
        if ins.sectionId not in ids:
            raise HTTPException(422,detail="Insert references unknown section")
        allowed={"table":{TABLE},"figure":VIS,"equation":{"sc.erw.equations-maps-diagrams.v0.7.0"}}[ins.kind]
        valid_source(project_id,owner,ins.source,allowed)
    obj={"schema":REPORT,"researchId":PROJECT_KEY,"projectId":project_id,
         "title":req.title,"authors":req.authors,
         "sections":[s.model_dump() for s in req.sections],
         "inserts":[i.model_dump() for i in req.inserts],
         "bibliography":req.bibliography,"status":"draft-unpublished",
         "publicationEnabled":False,"outboundSubmissionEnabled":False,
         "sourceIntegrityVerifiedExternally":False,
         "verifiedCDR":False,"verifiedAdditionality":False,
         "verifiedPermanence":False,"netDurableAtmosphericRemoval":None}
    obj["calculationObjectHash"]=content_hash(obj)
    return obj

def catalog(project_id,owner):
    project_for(project_id,owner)
    items=[]
    for row in list_calculations(project_id,owner):
        obj=row.get("calculationObject",{})
        if obj.get("schema") not in {TABLE,REPORT}|VIS: continue
        items.append({"id":row["id"],"schema":obj["schema"],
                      "title":obj.get("title",row["title"]),
                      "hash":obj.get("calculationObjectHash"),
                      "digestConsistent":obj.get("calculationObjectHash")==content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"})})
    return items

@router.get("/erw/v1.2.0/status")
def status():return {"ok":True,"extensionVersion":"1.2.0",
    "projectScopedDrafts":True,"editableResearchTables":True,
    "snapshotPersistence":True,"htmlExport":True,
    "nativeDocxExport":False,"publicationEnabled":False,"verifiedCDR":False}

@router.get("/erw/v1.2.0/projects")
def projects(authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"projects":projects_for(owner)}

@router.get("/erw/v1.2.0/projects/{project_id}/objects")
def objects(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"objects":catalog(project_id,owner)}

@router.get("/erw/v1.2.0/projects/{project_id}/objects/{object_id}")
def object_detail(project_id:str,object_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project_for(project_id,owner)
    row=get_calculation(object_id,owner)
    if row.get("projectId")!=project_id:
        raise HTTPException(404,detail="Object not in selected project")
    obj=row.get("calculationObject",{})
    h=obj.get("calculationObjectHash")
    if h!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        raise HTTPException(409,detail="Object hash mismatch")
    return {"ok":True,"object":obj}

@router.post("/erw/v1.2.0/projects/{project_id}/tables")
def create_table(project_id:str,request:TableRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return store(project_id,owner,make_table(project_id,owner,request),"ERW research table: "+request.title)

@router.post("/erw/v1.2.0/projects/{project_id}/reports")
def create_report(project_id:str,request:ReportRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    candidate=make_report(project_id,owner,request)
    # An unchanged manuscript is already preserved by the latest matching snapshot.
    for row in reversed(list_calculations(project_id,owner)):
        existing=row.get("calculationObject",{})
        if (existing.get("schema")==REPORT
            and existing.get("calculationObjectHash")==candidate["calculationObjectHash"]
            and existing.get("projectId")==project_id):
            return {"ok":True,"id":row["id"],"object":candidate,
                    "immutableSnapshot":True,"unchanged":True}
    return store(project_id,owner,candidate,"ERW research report: "+request.title)

@router.get("/erw/v1.2.0/report",response_class=HTMLResponse)
def report_ui():return HTMLResponse(PAGE)
PAGE=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Research Report Workspace — Sustainable Catalyst</title><style>
*{box-sizing:border-box}body{font:15px system-ui;margin:0;background:#f5f5f5;color:#151515}header{background:#151515;color:white;padding:22px 5vw}h1{margin:0;font-size:23px}main{max-width:1220px;margin:20px auto;padding:0 15px;display:grid;grid-template-columns:310px 1fr;gap:16px}aside,article{border:1px solid #ddd;border-radius:8px;background:#fff;padding:20px}label{font-size:13px;font-weight:600;display:block;margin:14px 0 5px}input,select,textarea{display:block;width:100%;padding:9px;border:1px solid #aaa;font:inherit}textarea{min-height:110px;resize:vertical}button{background:#111;color:white;border:0;padding:9px 12px;cursor:pointer;margin:8px 5px 4px 0}button:hover{background:#8e2323}.caution{padding:12px;background:#fff2e7;border-left:4px solid #ab3030;margin:12px 0}.section{border-bottom:1px solid #ddd;padding:12px 0}#status{white-space:pre-wrap;overflow-wrap:anywhere}.page{background:white;padding:28px;border:1px solid #ccc;margin-top:20px}.page p{white-space:pre-wrap}.page table{border-collapse:collapse;width:100%;font-size:13px}.page td,.page th{border:1px solid #999;padding:6px}.page h2{margin-top:26px}@media(max-width:820px){main{display:block}aside{margin-bottom:15px}}@media print{header,aside,.controls,.section,article>h2,.caution{display:none}main{display:block;margin:0;padding:0}article{border:0;padding:0}.page{border:0;padding:0}}</style></head>
<body><header><h1>SUSTAINABLE CATALYST / Research Report Workspace</h1></header><main><aside>
<div class="caution">Draft research only. This interface does not verify atmospheric CO₂ removal or publish reports.</div>
<label>Signed Workbench session token</label><input id="token" type="password" autocomplete="off"><button id="connect">My projects</button>
<label>Project</label><select id="project"></select><button id="load">Load research objects</button>
<label>Saved object</label><select id="object"></select><button id="insert">Insert selected source</button>
<hr><h3>Create a research table</h3><label>Table title</label><input id="tabletitle" value="Selected field evidence">
<label>Column labels (tab-separated)</label><input id="cols" value="Study&#9;Treatment&#9;Finding">
<label>Rows (one line per row; tab-separated cells)</label><textarea id="rows" placeholder="Illinois&#9;Basalt&#9;Modeled removal potential"></textarea>
<label>Caption</label><input id="caption"><label>Evidence classification</label><select id="evidence"><option>hypothetical</option><option>literature-derived</option><option>measured</option></select>
<button id="savetable">Save table as project object</button>
<p id="status" role="status"></p></aside><article><h2>Manuscript editor</h2><div class="controls"><label>Report title</label><input id="title" value="Accelerated Rock Weathering in Irish Agricultural Soils">
<label>Authors (comma-separated)</label><input id="authors"><button id="addsection">Add section</button><button id="preview">Preview report</button><button id="save">Save draft snapshot</button><button id="export">Export HTML report</button><button onclick="window.print()">Print / PDF</button></div>
<div id="sections"></div><h3>Bibliography</h3><textarea id="bibliography" placeholder="Paste verified references, one per line"></textarea><div class="controls"><h3>Linked inserts</h3><div id="insertlist"></div></div><div id="previewbox" class="page"></div></article></main>
<script>
(()=>{'use strict';const el=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let token='',catalog=[],sections=[],inserts=[];
const base=['abstract','overview','baseline','additionality','mrv','permanence','recommendations'];
function paint(){el('sections').replaceChildren();sections.forEach(s=>{let d=document.createElement('section');d.className='section';let lbl=document.createElement('label');lbl.textContent=s.heading;let a=document.createElement('textarea');a.value=s.text;a.oninput=()=>s.text=a.value;d.append(lbl,a);el('sections').append(d)});el('insertlist').textContent=inserts.map(i=>i.kind+' → '+i.sectionId+' · '+i.caption).join(' | ')}
sections=base.map(id=>({id,heading:id.charAt(0).toUpperCase()+id.slice(1),text:''}));paint();
async function api(path,body){if(!token)throw Error('Enter a Workbench signed-session token');let r=await fetch(path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status+': '+(await r.text()).slice(0,250));return r.json()}
function project(){let id=el('project').value;if(!id)throw Error('Select a project');return encodeURIComponent(id)}
function options(id,rows){el(id).replaceChildren();rows.forEach(r=>{let o=document.createElement('option');o.value=r.id;o.textContent=r.name||r.title||r.id;el(id).append(o)})}
function notice(e){el('status').textContent=e.message||String(e)}
el('connect').onclick=async()=>{try{token=el('token').value.trim().replace(/^Bearer\s+/i,'');el('token').value='';let d=await api('/erw/v1.2.0/projects');options('project',d.projects);el('status').textContent=d.projects.length+' owned ERW project(s)'}catch(e){notice(e)}};
el('load').onclick=async()=>{try{let d=await api('/erw/v1.2.0/projects/'+project()+'/objects');catalog=d.objects;options('object',catalog);el('status').textContent=catalog.length+' stored research objects'}catch(e){notice(e)}};
el('savetable').onclick=async()=>{try{let columns=el('cols').value.split('\t').map(x=>x.trim()),rows=el('rows').value.trim().split('\n').filter(Boolean).map(r=>r.split('\t').map(x=>x.trim()));let req={title:el('tabletitle').value,columns,rows,caption:el('caption').value,evidenceStatus:el('evidence').value,sourceRefs:[]};let r=await api('/erw/v1.2.0/projects/'+project()+'/tables',req);el('status').textContent='Saved table snapshot '+r.id;el('load').click()}catch(e){notice(e)}};
el('insert').onclick=async()=>{try{let entry=catalog.find(x=>x.id===el('object').value);if(!entry||!entry.digestConsistent)throw Error('Select an integrity-checked saved object');let kind=entry.schema.includes('research-table')?'table':entry.schema.includes('equations-maps')?'equation':'figure';let sectionId=prompt('Insert in which section? '+sections.map(x=>x.id).join(', '),'mrv');if(!sections.some(s=>s.id===sectionId))throw Error('Unknown section');let caption=prompt('Caption',entry.title)||entry.title;inserts.push({sectionId,kind,source:{calculationId:entry.id,objectHash:entry.hash},caption});paint()}catch(e){notice(e)}};
el('addsection').onclick=()=>{let id='custom'+sections.length;sections.push({id,heading:'Additional section',text:''});paint()};
function report(){return {title:el('title').value,authors:el('authors').value.split(',').map(x=>x.trim()).filter(Boolean),sections,inserts,bibliography:el('bibliography').value}}
async function html(){let r=report();let content='<h1>'+esc(r.title)+'</h1><p>'+esc(r.authors.join(', '))+'</p>';
for(let s of r.sections){content+='<h2>'+esc(s.heading)+'</h2><p>'+esc(s.text)+'</p>';for(let i of r.inserts.filter(x=>x.sectionId===s.id)){content+='<p class="insert"><strong>'+esc(i.kind.toUpperCase())+': '+esc(i.caption)+'</strong><br>Saved source: '+esc(i.source.calculationId)+'<br>SHA: '+esc(i.source.objectHash)+'</p>';if(i.kind==='table'){let d=await api('/erw/v1.2.0/projects/'+project()+'/objects/'+encodeURIComponent(i.source.calculationId));let t=d.object;content+='<table><thead><tr>'+t.columns.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+t.rows.map(row=>'<tr>'+row.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}}}
content+='<h2>Bibliography</h2><p>'+esc(r.bibliography)+'</p><p><small>Draft. Hypothetical outputs are not verified carbon removal. Research objects are linked by SHA-256 content fingerprints, not independently verified against external sources.</small></p>';return content}
el('preview').onclick=async()=>{try{el('previewbox').innerHTML=await html();el('status').textContent='Preview ready. Inserted tables are rendered from saved research objects.'}catch(e){notice(e)}};
el('save').onclick=async()=>{try{let d=await api('/erw/v1.2.0/projects/'+project()+'/reports',report());el('status').textContent='Saved immutable report snapshot '+d.id}catch(e){notice(e)}};
el('export').onclick=async()=>{try{let body=await html();let documentHtml='<!doctype html><html><head><meta charset="utf-8"><title>ERW research report</title><style>body{font-family:Georgia,serif;max-width:850px;margin:40px auto;line-height:1.55}table{border-collapse:collapse;width:100%}td,th{border:1px solid #999;padding:7px}p{white-space:pre-wrap}</style></head><body>'+body+'</body></html>';let u=URL.createObjectURL(new Blob([documentHtml],{type:'text/html;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download='sustainable-catalyst-erw-report.html';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}catch(e){notice(e)}};
})();
</script></body></html>"""
