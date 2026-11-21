"""ERW 1.3.8.1.1 discover-and-plot repair surface, additive to original editor."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v1381_ui import build_page as previous
router=APIRouter(tags=["erw-1.3.8.1.1-ui"])
PANEL="""<section id="sc13811" class="controls">
<h3>Saved research objects — discovery & visual inspection</h3>
<p>List every calculation in your selected ERW project, including objects that cannot be plotted. Only chart real, hash-validated saved scenario series. No demo data are substituted.</p>
<button type="button" id="sc13811discover">Discover saved project objects</button>
<label for="sc13811list">Project object and eligibility</label><select id="sc13811list"></select>
<button type="button" id="sc13811plot">Plot eligible saved source</button>
<div id="sc13811visual" role="img" aria-label="Source-derived scenario trajectories"></div>
<button type="button" id="sc13811svg" disabled>Download verified-source SVG</button>
<button type="button" id="sc13811csv" disabled>Download verified-source CSV</button>
<pre id="sc13811message" role="status" aria-live="polite" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre>
</section>"""
JS=r"""
(function(){
 const elem=id=>document.getElementById(id);
 let inventory=[],current=null,svg='';
 const xml=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 function clear(){
   current=null;svg='';elem('sc13811visual').replaceChildren();
   elem('sc13811svg').disabled=true;elem('sc13811csv').disabled=true;
 }
 function save(name,value,type){
  let url=URL.createObjectURL(new Blob([value],{type})),a=document.createElement('a');
  a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 elem('sc13811discover').onclick=async()=>{
  clear();inventory=[];elem('sc13811list').replaceChildren();
  elem('sc13811message').textContent='Querying authenticated project inventory…';
  try{
   const d=await api('/erw/v1.3.8.1.1/projects/'+project()+'/discover');
   inventory=d.objects;
   for(const obj of inventory){
    const op=document.createElement('option');
    op.value=obj.id;op.textContent=obj.title+' · '+obj.schema+' · '+obj.status;
    elem('sc13811list').append(op);
   }
   const reasons=inventory.reduce((m,o)=>(m[o.status]=(m[o.status]||0)+1,m),{});
   elem('sc13811message').textContent=d.total+' saved object(s); '+d.chartReady+' chart-ready.\n'+
    JSON.stringify(reasons,null,2)+(d.total===0?'\nNo calculations are saved in this project.':d.chartReady===0?'\nNo compatible stored scenario trajectory is available. Existing objects are preserved.':'\nSelect a chart-ready object and click Plot.');
  }catch(err){elem('sc13811message').textContent='Discovery failed: '+String(err.message||err)}
 };
 elem('sc13811plot').onclick=async()=>{
  clear();
  const item=inventory.find(x=>x.id===elem('sc13811list').value);
  if(!item){elem('sc13811message').textContent='Discover objects first.';return}
  if(!item.chartReady){elem('sc13811message').textContent='Not plottable: '+item.status+'\nObject: '+item.title+'\nSchema: '+item.schema;return}
  try{
   const d=await api('/erw/v1.3.8.1.1/projects/'+project()+'/chart/'+encodeURIComponent(item.id)+'?hash='+encodeURIComponent(item.hash));
   if(!d.ok||d.sourceHash!==item.hash||d.verifiedCDR!==false)throw Error('Source integrity check failed');
   const all=d.series.flatMap(s=>s.points);
   if(!all.length)throw Error('No plotted data');
   const xmax=Math.max(1,...all.map(p=>p.year)),ymax=Math.max(1,...all.map(p=>p.incrementalPotentialProxyTonnesCO2));
   const palette=['#913644','#207b87','#505397','#767433','#252525','#88568e'];
   const paths=d.series.map((s,i)=>'<polyline fill="none" stroke="'+palette[i%palette.length]+'" stroke-width="3" points="'+s.points.map(p=>(75+p.year*540/xmax).toFixed(2)+','+(270-p.incrementalPotentialProxyTonnesCO2*195/ymax).toFixed(2)).join(' ')+'"/>').join('');
   svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 690 420"><rect width="690" height="420" fill="white"/>'+
   '<text x="22" y="28" font-size="17" font-weight="bold">Source-derived ERW trajectories</text><path d="M75 75V270H620" stroke="#333" fill="none"/>'+paths+
   d.series.map((s,i)=>'<text x="'+(20+(i%4)*160)+'" y="'+(308+Math.floor(i/4)*17)+'" font-size="11" fill="'+palette[i%palette.length]+'">'+xml(s.rateTonnesPerHa)+' t/ha</text>').join('')+
   '<text x="20" y="365" font-size="12">Modeled incremental CO2 potential proxy (tonnes) — NOT verified CDR</text>'+
   '<text x="20" y="386" font-size="10">SHA-256 '+xml(d.sourceHash)+'</text>'+
   '<text x="20" y="405" font-size="10">Existing research calculation; no inferred uncertainty, measurements or credits</text></svg>';
   elem('sc13811visual').innerHTML=svg;
   current=d;elem('sc13811svg').disabled=false;elem('sc13811csv').disabled=false;
   elem('sc13811message').textContent='Source-linked plot loaded.\n'+d.researchObjectId+'\n'+d.sourceHash+'\n'+d.scientificCaution;
  }catch(err){clear();elem('sc13811message').textContent='Cannot chart source: '+String(err.message||err)}
 };
 elem('sc13811svg').onclick=()=>{if(current)save('erw-'+current.sourceHash.slice(0,12)+'.svg',svg,'image/svg+xml')};
 elem('sc13811csv').onclick=()=>{
  if(!current)return;
  const rows=['# SHA-256 '+current.sourceHash,'# Saved modeled potential only; NOT verified CDR','dose_t_ha,year,incremental_potential_proxy_tonnes_CO2'];
  current.series.forEach(s=>s.points.forEach(p=>rows.push([s.rateTonnesPerHa,p.year,p.incrementalPotentialProxyTonnesCO2].join(','))));
  save('erw-'+current.sourceHash.slice(0,12)+'.csv',rows.join('\n'),'text/csv');
 };
})();
"""
def build_page():
    page=previous()
    anchor='<label>Saved object</label>'
    assert page.count(anchor)==1
    page=page.replace(anchor,PANEL+anchor,1)
    marker="el('addsection').onclick="
    assert page.count(marker)==1
    return page.replace(marker,JS+"\n"+marker,1)
@router.get("/erw/v1.3.8.1.1/report",response_class=HTMLResponse)
def report():return HTMLResponse(build_page())
