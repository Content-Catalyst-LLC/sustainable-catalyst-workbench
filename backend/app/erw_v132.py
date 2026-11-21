"""ERW 1.3.2 — PDF source library and Harvard reference sidebar in composer."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v131 import build_page as previous_page

router=APIRouter(tags=["erw-1.3.2-citation-composer"])
PANEL="""<section id="citation-studio" class="controls">
<h3>PDF Source Library</h3><label for="pdfupload">Upload source paper (PDF, up to 20 MiB)</label>
<input id="pdfupload" type="file" accept=".pdf,application/pdf">
<button type="button" id="pdfsave">Save PDF source</button>
<button type="button" id="pdfrefresh">Refresh sources</button>
<label for="pdfsources">Uploaded PDF source</label><select id="pdfsources"></select>
<h3>Harvard Reference Manager</h3>
<p>Enter metadata from the paper or publisher record. No information is automatically invented or externally verified.</p>
<label for="citeauthors">Authors (one full name per line; surname first)</label><textarea id="citeauthors" placeholder="Beerling, D.J."></textarea>
<label for="citeyear">Year</label><input id="citeyear" type="number" min="1500" max="2200">
<label for="citetitle">Article title</label><input id="citetitle">
<label for="citejournal">Journal</label><input id="citejournal">
<label for="citevolume">Volume</label><input id="citevolume">
<label for="citeissue">Issue</label><input id="citeissue">
<label for="citepages">Pages</label><input id="citepages">
<label for="citedoi">DOI (optional)</label><input id="citedoi">
<label><input type="checkbox" id="citereviewed"> I reviewed these details against the source</label>
<button type="button" id="citesave">Generate and save Harvard reference</button>
<button type="button" id="citeinsert">Add approved reference to bibliography</button>
<p id="citestatus" role="status"></p></section>"""
STYLE="""<style id="sc-citation-style">
#citation-studio{border-top:2px solid #982b39;padding:14px 0;margin-top:16px}
#citation-studio p{font-size:12px;color:#59616a}#citation-studio textarea{min-height:70px}
#citation-studio input[type=checkbox]{width:auto;display:inline}
#citestatus{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}
</style>"""
SCRIPT=r"""
let scApprovedCitation=null;
async function scSources(){
 const r=await api('/erw/v1.3.2/projects/'+project()+'/sources');
 options('pdfsources',r.sources.map(s=>({id:s.sourceId,title:s.name+' · '+s.sha256.slice(0,12)})));
 el('citestatus').textContent=r.sources.length+' source PDF(s) in this project';
}
el('pdfrefresh').onclick=async()=>{try{await scSources()}catch(e){notice(e)}};
el('pdfsave').onclick=async()=>{
 try{
  if(!token)throw Error('Sign in first');
  const f=el('pdfupload').files[0];
  if(!f||!f.name.toLowerCase().endsWith('.pdf')||f.size>20*1024*1024)throw Error('Select a PDF under 20 MiB');
  const r=await fetch('/erw/v1.3.2/projects/'+project()+'/sources',{method:'POST',
   headers:{Authorization:'Bearer '+token,'Content-Type':'application/pdf','X-Filename':f.name},
   body:f,cache:'no-store'});
  const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'PDF upload failed HTTP '+r.status);
  el('pdfupload').value='';await scSources();el('pdfsources').value=d.sourceId;
  el('citestatus').textContent='Saved private PDF; SHA-256 '+d.sha256;
 }catch(e){notice(e)}
};
el('citesave').onclick=async()=>{
 try{
  const sourceId=el('pdfsources').value;if(!sourceId)throw Error('Select an uploaded source');
  const fields={authors:el('citeauthors').value.split('\n').map(x=>x.trim()).filter(Boolean),
   year:el('citeyear').value?Number(el('citeyear').value):null,title:el('citetitle').value,
   journal:el('citejournal').value,volume:el('citevolume').value,
   issue:el('citeissue').value,pages:el('citepages').value,
   doi:el('citedoi').value,verifiedByResearcher:el('citereviewed').checked};
  const d=await api('/erw/v1.3.2/projects/'+project()+'/citations',{sourceId,fields});
  scApprovedCitation=d.formattedCitation;
  el('citestatus').textContent=scApprovedCitation.reference+'\n'+scApprovedCitation.inText+'\n'+scApprovedCitation.warnings.join(' ');
 }catch(e){notice(e)}
};
el('citeinsert').onclick=()=>{
 if(!scApprovedCitation?.reference){el('citestatus').textContent='Generate an approved reference first';return}
 const box=el('bibliography'),entry=scApprovedCitation.reference;
 if(!box.value.split('\n').includes(entry))box.value+=(box.value.trim()?'\n':'')+entry;
 el('citestatus').textContent='Reference inserted into bibliography; save a new report snapshot to preserve it.';
};
"""
def build_page():
    page=previous_page()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    page=page.replace('</head>',STYLE+'</head>',1)
    script_anchor="el('addsection').onclick="
    assert page.count(script_anchor)==1
    page=page.replace(script_anchor,SCRIPT+"\n"+script_anchor,1)
    return page

def status():
    return {"ok":True,"extensionVersion":"1.3.2",
        "pdfSourceUpload":True,"originalPdfRetention":True,
        "harvardCitationDrafts":True,"manualMetadataReviewRequired":True,
        "bibliographyInsertion":True,"externalMetadataVerification":False,
        "pdfTextExtraction":False,"pageSpecificEvidence":False,
        "nativeDocxExport":False,"nativePdfExport":False,
        "publicationEnabled":False,"verifiedCDR":False}
@router.get("/erw/v1.3.2/status")
def status_route():return status()
@router.get("/erw/v1.3.2/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
