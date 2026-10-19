"""ERW 1.3.6 — safe in-memory Word import reconciliation and workspace navigation.
Original DOCX and immutable report snapshots never changed by these controls.
"""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse,RedirectResponse
from .erw_v135_ui import build_page as previous
router=APIRouter(tags=["erw-1.3.6-manuscript"])
CSS="""<style id="erw136style">
#sc-workspace-menu{position:sticky;top:0;background:#fff;padding:12px;border:1px solid #dce0e5;
display:flex;flex-wrap:wrap;gap:6px;z-index:10;border-radius:7px}
#sc-workspace-menu a{display:inline-block;background:#17191e;color:#fff;text-decoration:none;padding:8px 11px;border-radius:4px;font:600 12px system-ui}
#word-intake,#publication-audit,#native-export,#evidence-studio,#pdf-library,#document-outline{scroll-margin-top:100px}
#sc-manuscript-repair{border:1px solid #dce0e5;background:#fff;padding:12px;border-radius:6px;margin:10px 0}
#sc-manuscript-repair button{margin:6px 4px 0 0}
#sc-manuscript-repair p{font:12px/1.5 system-ui;color:#555}
#document-outline #outline-items{max-height:320px;overflow:auto}
#erw136summary{white-space:pre-wrap;font:12px/1.4 ui-monospace,monospace}
</style>"""
PANEL="""<div id="sc-manuscript-repair">
<h3>Import & manuscript structure</h3>
<p>The original Word file and all saved snapshots are retained. Changes below affect only the open editor until you explicitly save a new snapshot.</p>
<label for="erw136mode">When importing a Word document</label>
<select id="erw136mode"><option value="replace-empty">Replace an empty starter template (recommended)</option><option value="append">Append to current manuscript</option></select>
<button id="erw136-clean" type="button">Preview cleanup of empty starter sections</button>
<button id="erw136-apply" type="button">Apply reviewed cleanup to editor</button>
<pre id="erw136summary" role="status"></pre></div>"""
NAV="""<nav id="sc-workspace-menu" aria-label="Research workspace modules">
<a href="#document-outline">Manuscript</a><a href="#word-intake">Word import</a>
<a href="#evidence-studio">Evidence</a><a href="#publication-audit">Audit</a>
<a href="#native-export">Export</a></nav>"""
JS=r"""
const sc136={pending:[]};
function sc136Norm(h){return String(h||'').trim().replace(/^\d+(?:\.\d+)*[.)]?\s*/, '').toLowerCase();}
function sc136Plan(){
 const substantive=sections.filter(s=>String(s.text||'').trim());
 const redundant=new Set();
 sections.forEach((s,i)=>{if(!String(s.text||'').trim())redundant.add(i)});
 // Do not auto-remove populated sections, even if they share a heading.
 return {redundant:[...redundant],substantive:substantive.length};
}
el('erw136-clean').onclick=()=>{
 const p=sc136Plan();sc136.pending=p.redundant;
 el('erw136summary').textContent=p.redundant.length+' empty section(s) eligible for removal. '+p.substantive+' populated section(s) preserved. No saved history changed.';
};
el('erw136-apply').onclick=()=>{
 if(!sc136.pending.length)throwNotice('Run cleanup preview first');
 const remove=new Set(sc136.pending);
 sections=sections.filter((_,i)=>!remove.has(i));
 sc136.pending=[];paint();el('erw136summary').textContent='Editor updated. Review manuscript before saving a NEW snapshot.';
};
function throwNotice(m){el('erw136summary').textContent=m;}
el('uploadword').onclick=async()=>{
 try{
  if(!token)throw Error('Sign in to Sustainable Catalyst first');
  const file=el('wordfile').files[0];
  if(!file||!file.name.toLowerCase().endsWith('.docx')||file.size>8*1024*1024)throw Error('Select a .docx under 8 MiB');
  const originalSections=sections.map(s=>({...s}));
  const r=await fetch('/erw/v1.3.1/projects/'+project()+'/word-import',{method:'POST',
   headers:{Authorization:'Bearer '+token,'Content-Type':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','X-Filename':file.name},
   body:file,cache:'no-store'});
  const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'DOCX import failed: HTTP '+r.status);
  const mode=el('erw136mode').value, nonempty=originalSections.filter(s=>String(s.text||'').trim());
  if(mode==='replace-empty' && nonempty.length)throw Error('Existing manuscript contains text. Select Append, or create a separate draft before replacing. Original DOCX was preserved.');
  const imported=d.sections.map((s,i)=>({id:'docx'+d.documentId.replace(/-/g,'').slice(0,12)+i,heading:s.heading,text:s.text}));
  const b=imported.find(s=>sc136Norm(s.heading)==='bibliography');
  if(b&&!el('bibliography').value.trim()){
    el('bibliography').value=b.text;
    imported.splice(imported.indexOf(b),1);
  }
  if(mode==='replace-empty')sections=imported;
  else sections.push(...imported);
  sc136.pending=[];paint();el('wordfile').value='';
  el('erw136summary').textContent='Original DOCX preserved. '+d.sections.length+' imported parts; '+(b?'bibliography moved into dedicated field. ':'')+'Review headings, tables, author, references and save a NEW snapshot.';
 }catch(e){throwNotice(e.message||String(e))}
};
"""
def build_page():
    page=previous()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    page=page.replace('<article><h2>Scientific document canvas</h2>','<article><h2>Scientific document canvas</h2>'+NAV,1)
    page=page.replace('</head>',CSS+'</head>',1)
    page=page.replace('Source PDFs, automatic Harvard citations, native DOCX/PDF files, and journal-style typesetting are planned—not available in this build. Figures and equations may still display provenance placeholders.',
      'PDF sources, manually reviewed Harvard references, native DOCX/PDF export and a publication readiness audit are available. Automatic source-text verification, full Word roundtrip and mathematical typesetting remain incomplete.')
    start=page.index("el('uploadword').onclick=async()=>{")
    end=page.index("\n};",start)+3
    page=page[:start]+JS+page[end:]
    return page
@router.get("/erw/v1.3.6/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
@router.get("/erw/report")
def current_report():return RedirectResponse(url="/erw/v1.3.6/report",status_code=307)
@router.get("/erw/v1.3.6/status")
def status():return {"ok":True,"extensionVersion":"1.3.6","reviewedEmptySectionCleanup":True,"safeWordImportMode":True,"bibliographyReconciliation":True,"workspaceNavigation":True,"permanentWorkspaceRoute":True,"faithfulWordTables":False,"publicationCertified":False,"verifiedCDR":False}
