"""ERW 1.2.2 — authenticated research report workspace.

Reuses ERW 1.2 editor and the independently owned Sustainable Catalyst identity.
The report UI obtains its bearer session from login and keeps it in tab memory.
No WordPress integration, cross-account migration, or public SSO is claimed.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Header
from fastapi.responses import HTMLResponse
from .erw_v120 import PAGE as REPORT_PAGE
from .erw_v121 import owner_from_auth
from .erw_v110 import projects_for
from .erw_v120 import catalog, REPORT
from .v1220 import list_calculations

router=APIRouter(tags=["erw-1.2.2-authenticated-report"])
def status():
    return {"ok":True,"extensionVersion":"1.2.2",
            "identityAuthority":"sustainable-catalyst",
            "interactiveLogin":True,"noTokenCopyPaste":True,
            "ownedProjectSelection":True,"reportDraftRestoration":True,
            "nativeDocxExport":False,"crossProductSSO":False,
            "publicationEnabled":False,"verifiedCDR":False}
@router.get("/erw/v1.2.2/status")
def status_route():return status()

@router.get("/erw/v1.2.2/my/research-context")
def context_route(authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    projects=projects_for(owner)
    return {"ok":True,"identityId":owner,"projects":projects,
            "wordPressRequired":False}

def _unique_snapshots(items):
    """Collapse identical report hashes in the UI only; never delete saved history."""
    drafts=[i for i in items if i["schema"]==REPORT and i["digestConsistent"]]
    seen=set()
    unique=[]
    for item in reversed(drafts):
        if item["hash"] in seen:
            continue
        seen.add(item["hash"])
        unique.append({**item,"title":item["title"]+" · "+item["hash"][:10]})
    return unique

@router.get("/erw/v1.2.2/projects/{project_id}/report-drafts")
def drafts_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    items=catalog(project_id,owner)
    return {"ok":True,"drafts":_unique_snapshots(items)}

# This remains a tab-memory bearer session; it is never written to a URL or
# web storage. The existing editor's API methods retain owner validation.
LOGIN_CONTROLS="""<div class="caution">Draft research only. Hypothetical Wexford outputs are not verified atmospheric CO₂ removal.</div>
<div id="signinpanel"><h3>Sign in to Sustainable Catalyst</h3>
<label for="username">Research username</label><input id="username" autocomplete="username" maxlength="48">
<label for="password">Password</label><input id="password" type="password" autocomplete="current-password">
<button id="connect">Sign in and open my projects</button>
<p>Accounts are created through the restricted <a href="/erw/v1.2.1/onboarding">Sustainable Catalyst onboarding</a> interface. This login is independent of WordPress.</p></div>
<div id="signedin" hidden><strong>Signed in to Sustainable Catalyst</strong>
<button id="signout" type="button">Sign out of report workspace</button></div>"""
LEGACY_CONTROLS="""<div class="caution">Draft research only. This interface does not verify atmospheric CO₂ removal or publish reports.</div>
<label>Signed Workbench session token</label><input id="token" type="password" autocomplete="off"><button id="connect">My projects</button>"""
LEGACY_CONNECT="""el('connect').onclick=async()=>{try{token=el('token').value.trim().replace(/^Bearer\\s+/i,'');el('token').value='';let d=await api('/erw/v1.2.0/projects');options('project',d.projects);el('status').textContent=d.projects.length+' owned ERW project(s)'}catch(e){notice(e)}};"""
AUTH_CONNECT="""el('connect').onclick=async()=>{try{
 const r=await fetch('/erw/v1.2.1/identity/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:el('username').value,password:el('password').value}),cache:'no-store'});
 const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Invalid account credentials or input');
 token=d.token;el('password').value='';
 const context=await api('/erw/v1.2.2/my/research-context');
 options('project',context.projects);
 const wex=context.projects.find(x=>x.metadata&&x.metadata.onboardingKey==='wexford-erw-v121');
 if(wex)el('project').value=wex.id;
 el('signinpanel').hidden=true;el('signedin').hidden=false;
 el('status').textContent='Authenticated Sustainable Catalyst researcher · '+context.projects.length+' owned project(s).';
 if(wex)await refreshObjects();
 }catch(e){token='';notice(e)}};"""
LOAD_ORIGINAL="""el('load').onclick=async()=>{try{let d=await api('/erw/v1.2.0/projects/'+project()+'/objects');catalog=d.objects;options('object',catalog);el('status').textContent=catalog.length+' stored research objects'}catch(e){notice(e)}};"""
LOAD_NEW="""async function refreshObjects(){let d=await api('/erw/v1.2.0/projects/'+project()+'/objects');catalog=d.objects;options('object',catalog);el('status').textContent=catalog.length+' stored research objects';await refreshDrafts()}
el('load').onclick=async()=>{try{await refreshObjects()}catch(e){notice(e)}};
async function refreshDrafts(){const d=await api('/erw/v1.2.2/projects/'+project()+'/report-drafts');options('drafts',d.drafts.map(x=>({id:x.id,title:x.title})))}
el('restore').onclick=async()=>{try{
 if(!el('drafts').value)throw Error('No saved report snapshot selected');
 const d=await api('/erw/v1.2.0/projects/'+project()+'/objects/'+encodeURIComponent(el('drafts').value));
 const r=d.object;
 if(r.schema!=='sc.erw.report-workspace.v1.2.0'||r.projectId!==el('project').value)throw Error('Selected object is not a matching report');
 el('title').value=r.title;el('authors').value=(r.authors||[]).join(', ');
 sections=r.sections;inserts=r.inserts;el('bibliography').value=r.bibliography||'';paint();
 el('status').textContent='Restored saved report snapshot; changes require a new snapshot';
 }catch(e){notice(e)}};"""
DRAFT_CONTROLS="""<label>Saved report snapshots</label><select id="drafts"></select>
<button id="restore">Open selected saved draft</button>
<label for="manuscript">Import existing manuscript text</label>
<textarea id="manuscript" placeholder="Paste your existing report, then import as an editable section. Existing sections remain unchanged."></textarea>
<button id="importtext">Import text into manuscript</button>"""
IMPORT_SCRIPT="""el('importtext').onclick=()=>{const text=el('manuscript').value.trim();
 if(!text){el('status').textContent='Paste manuscript text first';return}
 const id='imported'+sections.length;
 sections.push({id,heading:'Imported manuscript (organize into sections)',text});
 el('manuscript').value='';paint();
 el('status').textContent='Manuscript text added as editable section; review formatting and references before saving.'};
el('signout').onclick=()=>{token='';catalog=[];inserts=[];options('project',[]);options('object',[]);options('drafts',[]);
 el('signedin').hidden=true;el('signinpanel').hidden=false;el('password').value='';
 el('previewbox').replaceChildren();el('status').textContent='Signed out of this report tab.'};"""

def build_page():
    page=REPORT_PAGE
    assert page.count(LEGACY_CONTROLS)==1
    assert page.count(LEGACY_CONNECT)==1
    assert page.count(LOAD_ORIGINAL)==1
    page=page.replace(LEGACY_CONTROLS,LOGIN_CONTROLS)
    page=page.replace('<label>Saved object</label>',DRAFT_CONTROLS+'\n<label>Saved object</label>',1)
    page=page.replace(LEGACY_CONNECT,AUTH_CONNECT)
    page=page.replace(LOAD_ORIGINAL,LOAD_NEW)
    page=page.replace("el('addsection').onclick=",IMPORT_SCRIPT+"\nel('addsection').onclick=",1)
    page=page.replace('<h1>SUSTAINABLE CATALYST / Research Report Workspace</h1>','<h1>SUSTAINABLE CATALYST / Authenticated Research Report Workspace</h1>',1)
    page=page.replace('article>h2,.caution{display:none}', 'article>h2,.caution,#signedin,#signinpanel{display:none}')
    return page
@router.get("/erw/v1.2.2/report",response_class=HTMLResponse)
def report_ui():return HTMLResponse(build_page())
