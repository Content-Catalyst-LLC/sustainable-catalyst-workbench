"""ERW 1.3.1 — document import plus research-object figure embedding."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v130 import canvas_page

router=APIRouter(tags=["erw-1.3.1-scientific-composition"])
PANEL="""<section id="word-intake" class="controls"><h3>Upload completed Word document</h3>
<p>Preserve the original DOCX and import editable paragraphs and headings; tables, equations, figures, citations and styles require review.</p>
<label for="wordfile">Existing report (.docx, maximum 8 MiB)</label>
<input id="wordfile" type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
<button id="uploadword" type="button">Import Word manuscript</button></section>"""
STYLE="""<style id="erw131css">
#word-intake{padding:14px;border-top:2px solid #ac293a;margin:10px 0}
#word-intake p{color:#555;font-size:12px}
#previewbox figure{break-inside:avoid;margin:26px 0}
#previewbox figure svg{width:100%;height:auto;border:1px solid #dedee5}
#previewbox figcaption{font:12px/1.5 sans-serif;color:#59616c}
</style>"""
# The inherited editor contains all state in an IIFE. Insert the code inside
# that closure to reuse its session token, sections, project and api functions.
SCRIPT=r"""
function scText(x,y,s,size){return '<text x="'+x+'" y="'+y+'" font-family="Arial,sans-serif" font-size="'+size+'" fill="#252b33">'+esc(s)+'</text>'}
function scSvg(title,body,hash,h=460){return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 '+h+'" role="img"><rect width="820" height="'+h+'" fill="white"/>'+scText(25,36,title,20)+body+scText(25,h-12,'Illustrative model · NOT verified CDR · source '+String(hash).slice(0,16),11)+'</svg>'}
function scFigure(obj,kind){
 const hash=obj.calculationObjectHash;
 if(kind==='equation'){
  if(!Array.isArray(obj.equations)||!obj.equations.length)throw Error('No saved equations');
  let b='';obj.equations.slice(0,4).forEach((e,i)=>{let y=65+i*84;b+='<rect x="25" y="'+y+'" width="770" height="73" rx="5" fill="#f3f5f6"/>'+scText(40,y+25,e.label,14)+scText(40,y+56,e.latex,19)});
  return scSvg('ERW · model equations (source notation)',b,hash,440);
 }
 const v=(obj.views||[]).find(x=>x.id==='scenario-trajectories');
 if(!v||!Array.isArray(v.series)||!v.series.length)throw Error('Saved scenario trajectories required');
 const series=v.series.slice(0,8),points=series.flatMap(s=>s.points||[]);
 const vals=points.map(p=>Number(p.incrementalPotentialProxyTonnesCO2));
 const yrs=points.map(p=>Number(p.year));
 if(!vals.length||vals.some(n=>!Number.isFinite(n)||n<0)||yrs.some(n=>!Number.isFinite(n)||n<0))throw Error('Invalid saved chart data');
 const top=Math.max(1,...vals),last=Math.max(1,...yrs);
 let b='<path d="M85 70 V345 H790" stroke="#333" fill="none"/>';
 for(let t=0;t<=4;t++){let y=345-t*65;b+='<path d="M85 '+y+' H790" stroke="#e0e3e7"/>'+scText(15,y+4,(top*t/4).toFixed(1),12)}
 const colors=['#aa293b','#116978','#3958a1','#a16830','#6c549f','#5c7770','#333','#c77'];
 series.forEach((s,i)=>{const pts=(s.points||[]).map((p,j)=>(j?'L':'M')+(85+Number(p.year)*690/last).toFixed(2)+' '+(345-Number(p.incrementalPotentialProxyTonnesCO2)*260/top).toFixed(2)).join(' ');b+='<path d="'+pts+'" stroke="'+colors[i]+'" stroke-width="3" fill="none"/>'+scText(70+(i%4)*183,390+Math.floor(i/4)*22,s.rateTonnesPerHa+' t/ha',12)});
 b+=scText(300,434,'Study year · potential proxy (tonnes CO₂)',12);
 return scSvg('ERW · modeled treatment trajectories',b,hash);
}
async function scFigureHtml(insert){
 const d=await api('/erw/v1.2.0/projects/'+project()+'/objects/'+encodeURIComponent(insert.source.calculationId));
 const o=d.object;
 if(o.calculationObjectHash!==insert.source.objectHash)throw Error('Stored research object changed');
 if(o.verifiedCDR!==false||o.netDurableAtmosphericRemoval!==null)throw Error('Verification status not supported');
 return '<figure>'+scFigure(o,insert.kind)+'<figcaption>'+esc(insert.caption)+' · SHA-256 '+esc(insert.source.objectHash)+'. Unverified model evidence.</figcaption></figure>';
}
el('uploadword').onclick=async()=>{
 try{
  if(!token)throw Error('Sign in to Sustainable Catalyst first');
  const file=el('wordfile').files[0];
  if(!file||!file.name.toLowerCase().endsWith('.docx')||file.size>8*1024*1024)throw Error('Select a .docx under 8 MiB');
  const r=await fetch('/erw/v1.3.1/projects/'+project()+'/word-import',{method:'POST',
   headers:{Authorization:'Bearer '+token,'Content-Type':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','X-Filename':file.name},
   body:file,cache:'no-store'});
  const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'DOCX import failed: HTTP '+r.status);
  d.sections.forEach((s,i)=>sections.push({id:'docx'+Date.now().toString(36)+i,heading:s.heading,text:s.text}));
  paint();el('wordfile').value='';
  el('status').textContent='Original DOCX preserved · '+d.sections.length+' editable sections imported. Review layout and save a report snapshot.';
 }catch(e){notice(e)}
};
"""
def build_page():
    page=canvas_page()
    assert page.count("</head>")>=1
    page=page.replace("</head>",STYLE+"</head>",1)
    anchor="<label>Saved object</label>"
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    marker="el('addsection').onclick="
    assert page.count(marker)==1
    page=page.replace(marker,SCRIPT+"\n"+marker,1)
    # Add source-backed SVGs inside report preview and exported HTML,
    # rather than independent graphics that would be lost on export.
    before="content+='<h2>Bibliography</h2>"
    assert page.count(before)==1
    enrichment="""for(const insert of r.inserts.filter(x=>x.kind==='figure'||x.kind==='equation')){
 const figure=await scFigureHtml(insert);
 const label='<p class="insert"><strong>'+esc(insert.kind.toUpperCase())+': '+esc(insert.caption)+'</strong>';
 const at=content.indexOf(label);if(at<0)throw Error('Figure placement not found');
 const end=content.indexOf('</p>',at);if(end<0)throw Error('Figure caption missing');
 content=content.slice(0,end+4)+figure+content.slice(end+4);
}
"""
    page=page.replace(before,enrichment+before,1)
    return page

def status():
    return {"ok":True,"extensionVersion":"1.3.1","completedDocxUpload":True,
        "originalWordPreserved":True,"editableParagraphImport":True,
        "sourceBasedSvgFigures":True,"figureExportInHtml":True,
        "fullyFaithfulDocxImport":False,"nativeDocxExport":False,
        "nativePdfExport":False,"harvardReferences":False,
        "pdfSourceLibrary":False,"verifiedCDR":False,"publicationEnabled":False}
@router.get("/erw/v1.3.1/status")
def status_route():return status()
@router.get("/erw/v1.3.1/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(build_page())
