"""ERW 1.3.3 — evidence-inspection controls for authenticated report canvas."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v132 import build_page as previous
router=APIRouter(tags=["erw-1.3.3-evidence-editor"])
PANEL="""<section id="evidence-studio" class="controls">
<h3>Claim-to-source evidence</h3>
<p>Researcher-supplied claim, page reference and excerpt. PDF contents are NOT automatically parsed or verified.</p>
<label for="evidence-section">Manuscript section</label><select id="evidence-section"></select>
<label for="evidence-claim">Scientific claim</label><textarea id="evidence-claim" placeholder="A specific assertion to evaluate"></textarea>
<label for="evidence-page">Source page(s)</label><input id="evidence-page" placeholder="p. 12 or pp. 12–13">
<label for="evidence-excerpt">Source excerpt (optional; manually transcribed)</label><textarea id="evidence-excerpt"></textarea>
<label for="evidence-class">Evidence classification</label><select id="evidence-class"><option>unclassified</option><option>literature-derived</option><option>measured</option><option>hypothetical</option></select>
<label for="evidence-assessment">Assessment</label><select id="evidence-assessment"><option>uncertain</option><option>supports</option><option>contradicts</option><option>context</option></select>
<label for="evidence-note">Limitations and review notes</label><textarea id="evidence-note"></textarea>
<label><input id="evidence-checked" type="checkbox"> I manually compared this excerpt with the original PDF</label>
<button id="evidence-save" type="button">Save evidence annotation</button>
<button id="evidence-refresh" type="button">Inspect saved evidence</button>
<label for="evidence-records">Saved evidence records</label><select id="evidence-records"></select>
<button id="evidence-open" type="button">Inspect selected record</button>
<pre id="evidence-results" aria-live="polite"></pre></section>"""
STYLE="""<style id="erw133style">
#evidence-studio{border-top:2px solid #a42b39;padding:14px 0}
#evidence-studio p{font-size:12px;color:#667}
#evidence-studio pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
#evidence-studio input[type=checkbox]{width:auto;display:inline}
</style>"""
SCRIPT=r"""
function evidenceOptions(){
 options('evidence-section',sections.map(s=>({id:s.id,title:s.heading})));
}
async function evidenceRefresh(){
 const d=await api('/erw/v1.3.3/projects/'+project()+'/evidence');
 options('evidence-records',d.evidence.map(x=>({id:x.id,title:x.assessment+' · '+x.pageReference+' · '+x.claim.slice(0,55)})));
 el('evidence-results').textContent=d.evidence.length+' saved annotation(s). These are researcher-authored, not machine-verified.';
}
el('evidence-save').onclick=async()=>{
 try{
  const sourceId=el('pdfsources').value;if(!sourceId)throw Error('Choose a PDF in the Source Library first');
  const body={sourceId,sectionId:el('evidence-section').value,claim:el('evidence-claim').value,
   pageReference:el('evidence-page').value,excerpt:el('evidence-excerpt').value,
   evidenceClass:el('evidence-class').value,assessment:el('evidence-assessment').value,
   note:el('evidence-note').value,excerptCheckedAgainstPdf:el('evidence-checked').checked};
  const d=await api('/erw/v1.3.3/projects/'+project()+'/evidence',body);
  await evidenceRefresh();el('evidence-records').value=d.id;
  el('evidence-results').textContent='Saved annotated claim '+d.id+' · original PDF SHA-256 '+d.evidence.sourceSha256;
 }catch(e){notice(e)}
};
el('evidence-refresh').onclick=async()=>{try{evidenceOptions();await evidenceRefresh()}catch(e){notice(e)}};
el('evidence-open').onclick=async()=>{
 try{
  const id=el('evidence-records').value;if(!id)throw Error('Select an evidence record');
  const d=await api('/erw/v1.3.3/projects/'+project()+'/evidence/'+encodeURIComponent(id));
  const o=d.evidence;el('evidence-results').textContent=
   'Claim: '+o.claim+'\nSource: '+d.sourceFilename+' · '+o.sourceSha256+
   '\nPage reference (manual): '+o.pageReference+'\nExcerpt (manual): '+o.researcherProvidedExcerpt+
   '\nAssessment: '+o.assessment+' · '+o.evidenceClass+
   '\nResearcher checked: '+o.excerptCheckedAgainstPdf+
   '\nMachine verified: NO\nNotes: '+o.note;
 }catch(e){notice(e)}
};
evidenceOptions();
"""
def build_page():
    page=previous()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    page=page.replace('</head>',STYLE+'</head>',1)
    marker="el('addsection').onclick="
    assert page.count(marker)==1
    page=page.replace(marker,SCRIPT+"\n"+marker,1)
    return page
@router.get("/erw/v1.3.3/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
