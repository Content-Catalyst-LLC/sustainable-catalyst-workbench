"""Style selector for existing ERW 1.3.6 research report workspace."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v136 import build_page as parent_page
router=APIRouter(tags=["erw-styled-workspace"])
PANEL="""<section id="style-engine" class="controls">
<h3>Scientific Publication Styles</h3>
<p>Styles affect saved-snapshot DOCX/PDF downloads only; the manuscript and earlier exports are preserved.</p>
<label for="style-preset">Export preset</label><select id="style-preset">
<option value="modern-academic">Modern Academic — Cambria, 11 pt, 1.5 spacing</option>
<option value="institutional">Sustainable Catalyst Institutional</option>
<option value="classic-academic">Classic Academic — Times New Roman</option></select>
<label for="style-font">Font</label><select id="style-font"><option>Cambria</option><option>Times New Roman</option><option>Liberation Serif</option></select>
<label for="style-size">Body size (pt)</label><input id="style-size" type="number" min="10" max="12" step="0.5" value="11">
<label for="style-line">Line spacing</label><select id="style-line"><option value="1.5">1.5</option><option value="1">Single</option><option value="2">Double</option></select>
<label for="style-margin">A4 margins (mm)</label><input id="style-margin" type="number" min="20" max="35" step="1" value="25">
<label><input id="style-number" type="checkbox"> Number section headings</label>
<button id="style-docx" type="button">Export styled Word</button>
<button id="style-pdf" type="button">Export styled PDF</button>
<p id="style-message" role="status"></p>
<p>PDF may substitute a compatible serif font when Cambria is unavailable on the export server. Confirm formatting against your module instructions.</p>
</section>"""
JS=r"""
el('style-preset').onchange=()=>{
 const p=el('style-preset').value;
 el('style-font').value=p==='classic-academic'?'Times New Roman':'Cambria';
 el('style-size').value=p==='classic-academic'?'12':'11';
 el('style-line').value=p==='classic-academic'?'2':'1.5';
};
async function scStyleExport(format){
 try{
  const original=el('export-draft').value;
  const d=await api('/erw/v1.2.2/projects/'+project()+'/report-drafts');
  options('export-draft',d.drafts.map(x=>({id:x.id,title:x.title})));
  if(original&&d.drafts.some(x=>x.id===original))el('export-draft').value=original;
  const id=el('export-draft').value;
  if(!id)throw Error('Save a manuscript snapshot and select it in Native research report exports.');
  const data={preset:el('style-preset').value,fontFamily:el('style-font').value,
   fontSizePt:Number(el('style-size').value),lineSpacing:Number(el('style-line').value),
   marginMm:Number(el('style-margin').value),headingsNumbered:el('style-number').checked};
  const route='/erw/v1.3.6/projects/'+project()+'/reports/'+encodeURIComponent(id)+'/styled-export/'+format;
  const response=await fetch(route,{method:'POST',headers:{Authorization:'Bearer '+token,
   'Content-Type':'application/json'},body:JSON.stringify(data),cache:'no-store'});
  if(!response.ok)throw Error('Export failed HTTP '+response.status+': '+(await response.text()).slice(0,300));
  const blob=await response.blob(),u=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=u;a.download='erw-'+data.preset+'.'+format;a.click();
  setTimeout(()=>URL.revokeObjectURL(u),5000);
  el('style-message').textContent='Downloaded styled '+format.toUpperCase()+'. Inspect typography and citations before use.';
 }catch(e){el('style-message').textContent=e.message||String(e)}
}
el('style-docx').onclick=()=>scStyleExport('docx');
el('style-pdf').onclick=()=>scStyleExport('pdf');
"""
def build_page():
    page=parent_page()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    mark="el('addsection').onclick="
    assert page.count(mark)==1
    return page.replace(mark,JS+"\n"+mark,1)
@router.get("/erw/v1.3.6/styled-report",response_class=HTMLResponse)
def page_route():return HTMLResponse(build_page())
