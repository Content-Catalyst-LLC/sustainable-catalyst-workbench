"""ERW 1.3.8.1 — render authenticated saved scenario series in a separate read-only panel."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v138 import build_page as previous
router=APIRouter(tags=["erw-1.3.8.1-source-chart-ui"])
PANEL="""<section id="sc1381" class="controls">
<h3>Source-linked scientific trajectories</h3>
<p>Unlike the 1.3.8 demonstration, this chart reads saved ERW 0.6 calculation series. It verifies project ownership and immutable SHA-256 hash server-side. It remains a modeled potential proxy—not verified atmospheric removal.</p>
<button id="sc1381refresh" type="button">Load verified research objects</button>
<label for="sc1381sources">Saved ERW visual research package</label><select id="sc1381sources"></select>
<button id="sc1381load" type="button">Plot selected saved calculation</button>
<div id="sc1381chart" role="img" aria-label="Source-linked saved research trajectories"></div>
<button id="sc1381svg" type="button" disabled>Download source-linked SVG</button>
<button id="sc1381csv" type="button" disabled>Download source-linked CSV</button>
<pre id="sc1381details" role="status" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre>
</section>"""
SCRIPT=r"""
(function(){
 const node=id=>document.getElementById(id);
 let candidates=[],series=[],source=null,svgText='';
 const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 function file(name,value,type){
  const u=URL.createObjectURL(new Blob([value],{type})),a=document.createElement('a');
  a.href=u;a.download=name;document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(u),1000);
 }
 node('sc1381refresh').onclick=async()=>{
  try{
   const res=await api('/erw/v1.3.8.1/projects/'+project()+'/sources');
   candidates=res.sources;node('sc1381sources').replaceChildren();
   candidates.forEach(x=>{let op=document.createElement('option');op.value=x.id;op.textContent=x.title+' · '+x.hash.slice(0,16);node('sc1381sources').append(op)});
   node('sc1381details').textContent=candidates.length+' digest-consistent visual research packages.';
  }catch(err){node('sc1381details').textContent=err.message||String(err)}
 };
 node('sc1381load').onclick=async()=>{
  try{
   const chosen=candidates.find(x=>x.id===node('sc1381sources').value);
   if(!chosen)throw Error('Select an available research package first');
   const d=await api('/erw/v1.3.8.1/projects/'+project()+'/sources/'+encodeURIComponent(chosen.id)+'?hash='+encodeURIComponent(chosen.hash));
   if(!d.ok||d.sourceHash!==chosen.hash||d.verifiedCDR!==false)throw Error('Source integrity or scientific status mismatch');
   source=d;series=d.series;
   const all=series.flatMap(s=>s.points);
   if(!all.length)throw Error('Source has no chart data');
   const maxYear=Math.max(1,...all.map(p=>p.year)),maxVal=Math.max(1,...all.map(p=>p.incrementalPotentialProxyTonnesCO2));
   const colors=['#7f3040','#207284','#575a99','#868044','#222','#876291'];
   const traces=series.map((s,i)=>{
    const pts=s.points.map(p=>(70+p.year*540/maxYear).toFixed(2)+','+(270-p.incrementalPotentialProxyTonnesCO2*190/maxVal).toFixed(2)).join(' ');
    return '<polyline points="'+pts+'" fill="none" stroke="'+colors[i%colors.length]+'" stroke-width="2.8"/>';
   }).join('');
   svgText='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 420"><rect width="700" height="420" fill="white"/>'+
    '<text x="18" y="27" font-size="17" font-weight="bold">Saved ERW scenario trajectories</text>'+
    '<path d="M70 70V270H625" stroke="#222" fill="none"/>'+
    traces+
    series.map((s,i)=>'<text x="'+(20+i%4*165)+'" y="'+(306+Math.floor(i/4)*18)+'" font-size="12" fill="'+colors[i%colors.length]+'">'+esc(s.rateTonnesPerHa)+' t/ha</text>').join('')+
    '<text x="20" y="363" font-size="12">Modeled incremental CO2 potential proxy (tonnes) · NOT verified CDR</text>'+
    '<text x="20" y="383" font-size="10">SHA-256 '+esc(d.sourceHash)+'</text>'+
    '<text x="20" y="403" font-size="10">Owner-scoped saved object; no statistical confidence interval is implied.</text></svg>';
   node('sc1381chart').innerHTML=svgText;
   node('sc1381svg').disabled=false;node('sc1381csv').disabled=false;
   node('sc1381details').textContent='Saved object '+d.researchObjectId+'\nSHA-256 '+d.sourceHash+'\n'+d.scientificCaution;
  }catch(err){source=null;node('sc1381chart').replaceChildren();node('sc1381svg').disabled=true;node('sc1381csv').disabled=true;node('sc1381details').textContent=err.message||String(err)}
 };
 node('sc1381svg').onclick=()=>{if(source)file('erw-source-linked-'+source.sourceHash.slice(0,12)+'.svg',svgText,'image/svg+xml')};
 node('sc1381csv').onclick=()=>{
  if(!source)return;
  const rows=['# Saved object SHA-256: '+source.sourceHash,'# Modeled proxy only; NOT verified net atmospheric CO2 removal','dose_t_ha,year,potential_proxy_tonnes_CO2'];
  series.forEach(s=>s.points.forEach(p=>rows.push([s.rateTonnesPerHa,p.year,p.incrementalPotentialProxyTonnesCO2].join(','))));
  file('erw-source-linked-'+source.sourceHash.slice(0,12)+'.csv',rows.join('\n'),'text/csv');
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
 return page.replace(marker,SCRIPT+"\n"+marker,1)
@router.get("/erw/v1.3.8.1/report",response_class=HTMLResponse)
def report():return HTMLResponse(build_page())
