"""ERW 1.3.8.1.2 unified model → chart → save → exports workspace."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v13811_ui import build_page as inherited
router=APIRouter(tags=["erw-1.3.8.1.2-ui"])
PANEL="""<section id="sc13812" class="controls">
<h3>Wexford Scenario Model & Scientific Figures</h3>
<p>Hypothetical researcher-controlled inputs only. Default coefficients are illustrative, not sourced from Wexford measurements. Preview before creating an immutable research calculation. No verified CDR.</p>
<label>Trial area (ha)<input id="marea" type="number" min="1" max="100000" step="1" value="100"></label>
<label>Application rates (t/ha, comma separated; include 0)<input id="mrates" value="0,10,20"></label>
<label>Assumed theoretical proxy yield (t CO₂ per t basalt)<input id="myield" type="number" min="0" max="1" step="0.01" value="0.15"></label>
<label>Assumed annual realization fraction<input id="mreal" type="number" min="0" max="1" step="0.01" value="0.10"></label>
<label>Assumed annual attenuation fraction<input id="matten" type="number" min="0" max="1" step="0.01" value="0.05"></label>
<label>Study years<input id="myears" type="number" min="1" max="30" step="1" value="10"></label>
<label>Required assumptions and rationale<textarea id="mnote">Illustrative assumptions for methods exploration; none are field-calibrated or verified as Irish ERW carbon-removal measurements.</textarea></label>
<button type="button" id="mpreview">Preview source-derived model</button>
<button type="button" id="msave">Save immutable scenario package</button>
<button type="button" id="mrefresh">Load previously saved model packages</button>
<label>Previously saved scenario packages<select id="mobjects"></select></label>
<button type="button" id="mload">Display saved model package</button>
<div id="mplot" role="img" aria-label="Hypothetical saved or previewed ERW scenario trajectories"></div>
<button type="button" id="msvg" disabled>Download SVG</button>
<button type="button" id="mpng" disabled>Download PNG (300 DPI equivalent)</button>
<button type="button" id="mcsv" disabled>Download CSV</button>
<pre id="mstatus" role="status" aria-live="polite" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre>
</section>"""
JS=r"""
(function(){
 const n=id=>document.getElementById(id);
 let active=null,svg='';
 const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 const qs=()=>({
 areaHa:n('marea').value,ratesTonnesPerHa:n('mrates').value.split(',').map(v=>v.trim()),
 potentialTonnesCO2PerTonneBasalt:n('myield').value,
 annualRealizationFraction:n('mreal').value,annualAttenuationFraction:n('matten').value,
 years:Number(n('myears').value),assumptionNote:n('mnote').value
 });
 function reset(){active=null;svg='';n('mplot').replaceChildren();['msvg','mpng','mcsv'].forEach(id=>n(id).disabled=true)}
 function draw(v,saved,id){
  if(v.verifiedCDR!==false||v.netDurableAtmosphericRemoval!==null)throw Error('Unsupported scientific verification state');
  const chart=v.views.find(x=>x.id==='scenario-trajectories');
  if(!chart||!chart.series.length)throw Error('Missing scenario trajectories');
  const data=chart.series.flatMap(s=>s.points),xmax=Math.max(1,...data.map(p=>Number(p.year))),
   ymax=Math.max(1,...data.map(p=>Number(p.incrementalPotentialProxyTonnesCO2)));
  const pal=['#666','#9c3545','#207789','#635399','#84743d','#222'];
  const lines=chart.series.map((s,i)=>'<polyline fill="none" stroke="'+pal[i%pal.length]+'" stroke-width="3" points="'+s.points.map(p=>(70+Number(p.year)*570/xmax).toFixed(2)+','+(290-Number(p.incrementalPotentialProxyTonnesCO2)*200/ymax).toFixed(2)).join(' ')+'"/>').join('');
  const ticks=[0,.25,.5,.75,1].map(t=>'<path d="M70 '+(290-t*200)+'H642" stroke="#eee"/><text x="8" y="'+(295-t*200)+'" font-size="11">'+(t*ymax).toFixed(2)+'</text>').join('');
  svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 730 445"><rect width="730" height="445" fill="#fff"/>'+
   '<text x="24" y="29" font-size="18" font-weight="bold">Wexford — hypothetical annual potential proxy</text>'+
   '<path d="M70 72V290H642" stroke="#333" fill="none"/>'+ticks+lines+
   chart.series.map((s,i)=>'<text x="'+(22+i%4*163)+'" y="'+(325+Math.floor(i/4)*19)+'" font-size="12" fill="'+pal[i%pal.length]+'">'+esc(s.rateTonnesPerHa)+' t/ha</text>').join('')+
   '<text x="22" y="370" font-size="12">Years 1–'+esc(v.model.years)+' · modeled potential proxy (tonnes CO₂ per year)</text>'+
   '<text x="22" y="389" font-size="12">Researcher-assumed, NOT measured, NOT verified net atmospheric CDR</text>'+
   '<text x="22" y="408" font-size="10">SHA-256 '+esc(v.calculationObjectHash)+'</text>'+
   '<text x="22" y="426" font-size="10">'+(saved?'Saved immutable research calculation':'UNSAVED PREVIEW')+' · annual assumed yield; not creditable</text></svg>';
  active={v,saved,id,series:chart.series};n('mplot').innerHTML=svg;
  ['msvg','mpng','mcsv'].forEach(k=>n(k).disabled=false);
  n('mstatus').textContent=(saved?'SAVED SOURCE':'UNSAVED PREVIEW')+'\n'+v.calculationObjectHash+
   '\nFormula: '+v.model.formula+'\nAssumptions: '+v.model.assumptionNote+
   '\nNo verified CDR, no field calibration or scientific confidence intervals.';
 }
 async function action(kind){
  try{
   n('mstatus').textContent=kind+' request running…';
   const d=await api('/erw/v1.3.8.1.2/projects/'+project()+'/'+kind,qs());
   if(!d.ok||!d.visual)throw Error('Model endpoint returned no visual');
   draw(d.visual,kind==='save',d.id||null);
   if(kind==='save')await refresh();
  }catch(err){n('mstatus').textContent=String(err.message||err)}
 }
 async function refresh(){
  const d=await api('/erw/v1.3.8.1.1/projects/'+project()+'/discover');
  const matches=d.objects.filter(x=>x.chartReady && x.schema==='sc.erw.visual-research-package.v0.6.0');
  n('mobjects').replaceChildren();
  matches.forEach(o=>{const op=document.createElement('option');op.value=o.id;op.textContent=o.title+' · '+o.hash.slice(0,12);op.dataset.hash=o.hash;n('mobjects').append(op)});
  n('mstatus').textContent=matches.length+' compatible saved visual packages (of '+d.total+' project objects).';
 }
 function saveFile(name,blob){
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 n('mpreview').onclick=()=>action('preview');
 n('msave').onclick=()=>action('save');
 n('mrefresh').onclick=async()=>{try{await refresh()}catch(e){n('mstatus').textContent=String(e.message||e)}};
 n('mload').onclick=async()=>{
  try{
   const o=n('mobjects').selectedOptions[0];if(!o)throw Error('Select a saved visual package');
   const d=await api('/erw/v1.3.8.1.1/projects/'+project()+'/chart/'+encodeURIComponent(o.value)+'?hash='+encodeURIComponent(o.dataset.hash));
   if(!d.ok||d.sourceHash!==o.dataset.hash)throw Error('Invalid saved source hash');
   // Saved visual package itself contains model metadata; fetch same verified object through owner-scoped API.
   const detail=await api('/erw/v1.2.0/projects/'+project()+'/objects/'+encodeURIComponent(o.value));
   if(detail.object.calculationObjectHash!==d.sourceHash || !detail.object.model)throw Error('Not a supported saved model package');
   draw(detail.object,true,o.value);
  }catch(err){n('mstatus').textContent=String(err.message||err)}
 };
 n('msvg').onclick=()=>{if(active)saveFile('wexford-'+active.v.calculationObjectHash.slice(0,12)+'.svg',new Blob([svg],{type:'image/svg+xml'}))};
 n('mcsv').onclick=()=>{
  if(!active)return;
  const rows=['# '+(active.saved?'Saved object':'Unsaved model preview')+' SHA-256 '+active.v.calculationObjectHash,'# Hypothetical annual potential only — NOT verified CDR',
  'dose_t_ha,year,assumed_annual_potential_proxy_tonnes_CO2'];
  active.series.forEach(s=>s.points.forEach(p=>rows.push([s.rateTonnesPerHa,p.year,p.incrementalPotentialProxyTonnesCO2].join(','))));
  saveFile('wexford-'+active.v.calculationObjectHash.slice(0,12)+'.csv',new Blob([rows.join('\n')],{type:'text/csv'}));
 };
 n('mpng').onclick=async()=>{
  if(!active)return;
  try{
   const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
   try{
    const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=()=>reject(Error('SVG could not rasterize'));img.src=url});
    const canvas=document.createElement('canvas');canvas.width=2282;canvas.height=1391;
    const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    const png=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('PNG conversion failed')),'image/png'));
    saveFile('wexford-'+active.v.calculationObjectHash.slice(0,12)+'-300dpi.png',png);
   }finally{URL.revokeObjectURL(url)}
  }catch(e){n('mstatus').textContent=String(e.message||e)}
 };
})();
"""
def build_page():
    page=inherited()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    marker="el('addsection').onclick="
    assert page.count(marker)==1
    page=page.replace(marker,JS+"\n"+marker,1)
    page=page.replace('</head>','<style>#sc138,#sc1381,#sc13811{display:none}#sc13812 input,#sc13812 textarea{max-width:100%}#sc13812 #mplot svg{width:100%;height:auto}</style></head>',1)
    return page
@router.get("/erw/v1.3.8.1.2/report",response_class=HTMLResponse)
def report():return HTMLResponse(build_page())
