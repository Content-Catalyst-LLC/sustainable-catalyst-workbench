"""ERW 1.3.4 authenticated report page and native file download controls."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v133 import build_page as previous
router=APIRouter(tags=["erw-1.3.4-report-export"])
PANEL="""<section id="native-export" class="controls">
<h3>Native research report exports</h3>
<p>Save a report snapshot, then export that exact saved version. Source-backed tables and supported figures are included. Draft/unverified status remains visible.</p>
<label for="export-draft">Report snapshot</label><select id="export-draft"></select>
<button id="download-docx" type="button">Download editable Word (.docx)</button>
<button id="download-pdf" type="button">Download native PDF (.pdf)</button>
<p id="export-status" role="status"></p>
</section>"""
SCRIPT=r"""
async function scRefreshExportDrafts(){
 const d=await api('/erw/v1.2.2/projects/'+project()+'/report-drafts');
 options('export-draft',d.drafts.map(x=>({id:x.id,title:x.title})));
}
async function scNativeExport(format){
 try{
  if(!token)throw Error('Sign in first');
  await scRefreshExportDraftsIfEmpty();
  const id=el('export-draft').value;
  if(!id)throw Error('Save a report snapshot before exporting');
  const url='/erw/v1.3.4/projects/'+project()+'/reports/'+encodeURIComponent(id)+'/export/'+format;
  const response=await fetch(url,{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  if(!response.ok)throw Error('Export HTTP '+response.status+': '+(await response.text()).slice(0,180));
  const blob=await response.blob(),link=document.createElement('a'),objectUrl=URL.createObjectURL(blob);
  link.href=objectUrl;link.download='sustainable-catalyst-erw-report.'+format;
  link.click();setTimeout(()=>URL.revokeObjectURL(objectUrl),5000);
  el('export-status').textContent='Downloaded saved '+format.toUpperCase()+' draft. Review content, figure captions, citations and scientific limitations.';
 }catch(e){el('export-status').textContent=e.message||String(e)}
}
async function scRefreshExportDraftsIfEmpty(){
 if(!el('export-draft').options.length)await scRefreshExportDrafts();
}
el('download-docx').onclick=()=>scNativeExport('docx');
el('download-pdf').onclick=()=>scNativeExport('pdf');
"""
def build_page():
    page=previous()
    marker='<label>Saved object</label>'
    assert page.count(marker)==1
    page=page.replace(marker,PANEL+marker,1)
    js="el('addsection').onclick="
    assert page.count(js)==1
    page=page.replace(js,SCRIPT+"\n"+js,1)
    return page
@router.get("/erw/v1.3.4/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
