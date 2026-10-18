"""ERW 1.3.5 — read-only publication readiness review panel."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v134 import build_page as inherited_page
router=APIRouter(tags=["erw-1.3.5-publication-review"])
PANEL="""<section id="publication-audit" class="controls">
<h3>Publication readiness audit</h3>
<p>Inspect the selected saved manuscript, PDF source inventory, linked evidence, figure references and native export smoke tests. A passing technical audit does not certify the science or authorize publication.</p>
<label for="audit-draft">Saved report version</label><select id="audit-draft"></select>
<button id="audit-refresh" type="button">Load saved versions</button>
<button id="audit-run" type="button">Run read-only audit (including DOCX/PDF smoke generation)</button>
<pre id="audit-result" role="status" style="white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 ui-monospace,monospace"></pre>
</section>"""
SCRIPT=r"""
async function scAuditDrafts(){
 const d=await api('/erw/v1.2.2/projects/'+project()+'/report-drafts');
 options('audit-draft',d.drafts.map(x=>({id:x.id,title:x.title})));
 el('audit-result').textContent=d.drafts.length+' saved report versions available';
}
el('audit-refresh').onclick=async()=>{try{await scAuditDrafts()}catch(e){notice(e)}};
el('audit-run').onclick=async()=>{
 try{
  if(!el('audit-draft').options.length)await scAuditDrafts();
  const id=el('audit-draft').value;if(!id)throw Error('Save a manuscript snapshot first');
  el('audit-result').textContent='Running read-only audit...';
  const r=await api('/erw/v1.3.5/projects/'+project()+'/reports/'+encodeURIComponent(id)+'/audit?render=true');
  el('audit-result').textContent=
   'Publication certified: NO\nReport hash: '+r.reportHash+
   '\nFigures/tables/equations linked: '+r.researchObjects+
   '\nPDF sources: '+r.pdfSources+'\nEvidence annotations: '+r.evidenceAnnotations+
   '\n'+r.checks.map(x=>(x.passed?'PASS ':'PENDING ') + x.gate+': '+(typeof x.detail==='string'?x.detail:JSON.stringify(x.detail))).join('\n')+
   '\n\n'+r.warning;
 }catch(e){el('audit-result').textContent=e.message||String(e)}
};
"""
def build_page():
    page=inherited_page()
    anchor='<label>Saved object</label>'
    if page.count(anchor)!=1:raise ValueError("Audit insert anchor missing")
    page=page.replace(anchor,PANEL+anchor,1)
    marker="el('addsection').onclick="
    if page.count(marker)!=1:raise ValueError("Audit JS anchor missing")
    return page.replace(marker,SCRIPT+"\n"+marker,1)
@router.get("/erw/v1.3.5/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
