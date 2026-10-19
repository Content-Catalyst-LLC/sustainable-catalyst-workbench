"""ERW 1.3.8 — browser-only scientific exploration, no persisted or verified removal data."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_style_ui import build_page as inherited
router=APIRouter(tags=["erw-1.3.8-graphics"])
PANEL=r"""<section id="sc138" class="controls">
<h3>Dynamic scientific graphics — exploratory</h3>
<p>Illustrative normalized dose-response INDEX only, not tonnes CO₂, removals, or empirical predictions. No project data are overwritten. Reference the actual saved research object when constructing publication evidence.</p>
<label for="sc138dose">Treatment dose: <output id="sc138doseout">10</output> t/ha</label>
<input id="sc138dose" type="range" min="0" max="20" step="1" value="10">
<label for="sc138year">Study year: <output id="sc138yearout">5</output></label>
<input id="sc138year" type="range" min="0" max="10" step="1" value="5">
<label for="sc138decay">Illustrative response attenuation: <output id="sc138decayout">0</output>%</label>
<input id="sc138decay" type="range" min="0" max="100" step="5" value="0">
<label for="sc138source">Evidence or calculation object hash (optional; not verified by this viewer)</label>
<input id="sc138source" placeholder="Manually enter source identifier for export annotation">
<div id="sc138plot" role="img" aria-label="Hypothetical normalized scenario comparison graphic"></div>
<div id="sc138path" role="img" aria-label="Enhanced weathering conceptual carbon pathway"></div>
<button type="button" id="sc138svg">Download scenario SVG</button>
<button type="button" id="sc138pathsvg">Download pathway SVG</button>
<button type="button" id="sc138csv">Download scenario CSV</button>
<label for="sc138resolution">Raster export</label><select id="sc138resolution"><option value="300">300 DPI (Word default)</option><option value="600">600 DPI (print quality)</option></select>
<button type="button" id="sc138png">Download scenario PNG</button>
<button type="button" id="sc138pathpng">Download pathway PNG</button>
<p id="sc138msg" role="status"></p>
<p>Both charts are editable browser explorations. SVG/PNG/CSV downloads include assumptions and non-verification notices; PDF/DOCX outputs remain on the existing saved-report export routes.</p>
</section>"""
JS=r"""
(function(){
 const g=id=>document.getElementById(id);
 const e=t=>String(t).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;').replaceAll('>','&gt;');
 const ns='http://www.w3.org/2000/svg';
 let chart='',path='';
 function draw(){
  const dose=Number(g('sc138dose').value),year=Number(g('sc138year').value),
   attenuation=Number(g('sc138decay').value)/100;
  g('sc138doseout').textContent=dose;g('sc138yearout').textContent=year;
  g('sc138decayout').textContent=Math.round(attenuation*100);
  const source=g('sc138source').value.trim().slice(0,90);
  // This deliberately dimensionless index is not a scientific estimate.
  const index=(d,y)=>d/20*y/10*(1-attenuation);
  const vals=[0,10,20,dose];
  const colors=['#777','#407d91','#9b3947','#1e1e1e'];
  const paths=vals.map((d,i)=>{
    const xy=Array.from({length:11},(_,y)=>[70+y*53,280-index(d,y)*205]);
    return '<polyline fill="none" stroke="'+colors[i]+'" stroke-width="'+(i===3?4:2.5)+'" points="'+xy.map(p=>p.join(',')).join(' ')+'"/>';
  }).join('');
  chart='<svg xmlns="'+ns+'" viewBox="0 0 680 385" role="img" aria-label="Illustrative normalized scenario index"><rect width="680" height="385" fill="white"/>'+
   '<text x="24" y="29" font-size="18" font-weight="bold">Wexford dose scenarios — hypothetical index</text>'+
   '<path d="M70 70V280H610" stroke="#333" fill="none"/>'+
   [0,0.25,0.5,0.75,1].map(v=>'<path d="M70 '+(280-v*205)+'H610" stroke="#ddd"/><text x="25" y="'+(285-v*205)+'" font-size="11">'+v+'</text>').join('')+paths+
   vals.map((d,i)=>'<text x="'+(52+i*148)+'" y="320" fill="'+colors[i]+'" font-size="12">'+(i===3?'Selected '+d:d+' t/ha')+'</text>').join('')+
   '<text x="260" y="345" font-size="12">Years 0–10 · selected year '+year+' · index '+index(dose,year).toFixed(3)+'</text>'+
   '<text x="20" y="366" font-size="11">Dimensionless demonstration only · attenuation '+Math.round(attenuation*100)+'% · NOT verified CDR</text>'+
   '<text x="20" y="380" font-size="9">Source identifier (user-supplied, unverified): '+e(source||'none')+'</text></svg>';
  const stages=['Basalt application','Mineral dissolution','Carbon / acid attribution','Aqueous product export','Downstream fate','Candidate durable storage'];
  path='<svg xmlns="'+ns+'" viewBox="0 0 680 245" role="img" aria-label="Conceptual pathway; stages are not verified removal"><rect width="680" height="245" fill="white"/>'+
   '<text x="20" y="25" font-size="18" font-weight="bold">ERW carbon pathway — conceptual, not measured</text>'+
   stages.map((name,i)=>{const x=18+(i%3)*225,y=44+Math.floor(i/3)*88;return '<rect x="'+x+'" y="'+y+'" width="207" height="57" rx="5" stroke="#888" fill="#f4f4f4"/><text x="'+(x+8)+'" y="'+(y+22)+'" font-size="12">'+e(name)+'</text><text x="'+(x+8)+'" y="'+(y+43)+'" fill="#9b3947" font-size="10">Evidence required</text>'}).join('')+
   '<text x="18" y="233" font-size="11">Dissolution ≠ additional atmospheric capture ≠ verified durable storage · NOT verified CDR</text></svg>';
  g('sc138plot').innerHTML=chart;g('sc138path').innerHTML=path;
 }
 function download(name,content,mime){
   const u=URL.createObjectURL(new Blob([content],{type:mime}));const a=document.createElement('a');
   a.href=u;a.download=name;document.body.append(a);a.click();a.remove();
   setTimeout(()=>URL.revokeObjectURL(u),1000);
 }
 ['sc138dose','sc138year','sc138decay','sc138source'].forEach(id=>g(id).addEventListener('input',draw));
 g('sc138svg').onclick=()=>download('wexford-hypothetical-index.svg',chart,'image/svg+xml');
 g('sc138pathsvg').onclick=()=>download('erw-conceptual-pathway.svg',path,'image/svg+xml');
 async function downloadPng(svgText,name,baseWidth,baseHeight){
  const dpi=Number(g('sc138resolution').value);
  if(![300,600].includes(dpi))throw Error('Unsupported DPI setting');
  const scale=dpi/96;
  const width=Math.round(baseWidth*scale),height=Math.round(baseHeight*scale);
  const svgUrl=URL.createObjectURL(new Blob([svgText],{type:'image/svg+xml;charset=utf-8'}));
  try{
   const image=await new Promise((resolve,reject)=>{
    const img=new Image();
    img.onload=()=>resolve(img);
    img.onerror=()=>reject(Error('SVG rendering failed'));
    img.src=svgUrl;
   });
   const canvas=document.createElement('canvas');
   canvas.width=width;canvas.height=height;
   const context=canvas.getContext('2d');
   if(!context)throw Error('Canvas drawing unavailable');
   context.fillStyle='#fff';context.fillRect(0,0,width,height);
   context.drawImage(image,0,0,width,height);
   const png=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('PNG conversion failed')),'image/png'));
   const url=URL.createObjectURL(png);
   try{
    const a=document.createElement('a');a.href=url;a.download=name+'-'+dpi+'dpi.png';
    document.body.append(a);a.click();a.remove();
   }finally{setTimeout(()=>URL.revokeObjectURL(url),1000);}
   g('sc138msg').textContent='Exported '+name+' as '+width+' × '+height+' PNG at '+dpi+' DPI-equivalent scale. Review layout before Word insertion.';
  }finally{URL.revokeObjectURL(svgUrl);}
 }
 g('sc138png').onclick=async()=>{try{await downloadPng(chart,'wexford-hypothetical-index',680,385)}catch(err){g('sc138msg').textContent=err.message||String(err)}};
 g('sc138pathpng').onclick=async()=>{try{await downloadPng(path,'erw-conceptual-pathway',680,245)}catch(err){g('sc138msg').textContent=err.message||String(err)}};
 g('sc138csv').onclick=()=>{
  const att=Number(g('sc138decay').value)/100,dose=Number(g('sc138dose').value);
  let rows=['# HYPOTHETICAL DIMENSIONLESS INDEX — NOT VERIFIED CDR','# Reference hash entered in UI is NOT independently validated',
  'year,control_0t,index_10t,index_20t,index_selected,selected_dose_t_ha,attenuation_fraction'];
  for(let y=0;y<=10;y++)rows.push([y,0,(0.5*y/10*(1-att)).toFixed(6),(y/10*(1-att)).toFixed(6),(dose/20*y/10*(1-att)).toFixed(6),dose,att].join(','));
  download('wexford-hypothetical-index.csv',rows.join('\n'),'text/csv');
 };
 draw();
})();
"""
def build_page():
    page=inherited()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    marker="el('addsection').onclick="
    assert page.count(marker)==1
    return page.replace(marker,JS+"\n"+marker,1)
@router.get("/erw/v1.3.8/report",response_class=HTMLResponse)
def report():return HTMLResponse(build_page())
@router.get("/erw/v1.3.8/status")
def status():return {"ok":True,"extensionVersion":"1.3.8","dynamicGraphics":True,"conceptualPathway":True,"interactiveNormalizedScenarioIndex":True,"downloadSvgCsv":True,"downloadPng300600":True,"savedDataMutated":False,"empiricalCarbonEstimation":False,"verifiedCDR":False,"publicationCertified":False}
