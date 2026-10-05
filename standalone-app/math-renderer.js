function svgEl(name,attrs={}){const e=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));return e;}
function pickViews(spec){
  if(Array.isArray(spec))return spec;
  if(Array.isArray(spec?.views))return spec.views;
  if(Array.isArray(spec?.result?.views))return spec.result.views;
  if(Array.isArray(spec?.viewSpec?.views))return spec.viewSpec.views;
  if(Array.isArray(spec?.viewSpec?.result?.views))return spec.viewSpec.result.views;
  if(spec?.viewSpec)return [spec.viewSpec];
  return [spec];
}
function seriesPoints(series){
  if(Array.isArray(series?.points))return series.points.map(p=>Array.isArray(p)?{x:Number(p[0]),y:Number(p[1])}:{x:Number(p.x),y:Number(p.y)});
  if(Array.isArray(series?.x)&&Array.isArray(series?.y))return series.x.map((x,i)=>({x:Number(x),y:Number(series.y[i])}));
  return [];
}
function pointsOf(v){
  if(Array.isArray(v?.points))return v.points;
  if(v?.series?.length)return seriesPoints(v.series[0]);
  if(Array.isArray(v?.data?.points))return v.data.points;
  if(Array.isArray(v?.samples))return v.samples;
  return [];
}
function allSeries(v){
  if(Array.isArray(v?.series)&&v.series.length)return v.series.map((s,i)=>({
    label:s.label||v.graphSeriesLabel||`Series ${i+1}`,
    points:seriesPoints(s).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y))
  }));
  return [{label:v?.graphSeriesLabel||v?.title||v?.kind||"Series",points:pointsOf(v).map(p=>Array.isArray(p)?{x:Number(p[0]),y:Number(p[1])}:p).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y))}];
}
function renderCartesian(host,v){
  const card=document.createElement("div");card.className="math-card";
  const title=document.createElement("h3");title.textContent=v.graphSeriesLabel||v.title||v.kind||"Mathematical view";card.appendChild(title);
  const groups=allSeries(v).filter(g=>g.points.length);
  if(!groups.length){const pre=document.createElement("pre");pre.textContent=JSON.stringify(v,null,2);card.appendChild(pre);host.appendChild(card);return;}
  const pts=groups.flatMap(g=>g.points),w=900,hg=420,pad=34;
  const xs=pts.map(p=>p.x),ys=pts.map(p=>p.y),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const dx=(xmax-xmin)||1,dy=(ymax-ymin)||1,X=x=>pad+(x-xmin)/dx*(w-2*pad),Y=y=>hg-pad-(y-ymin)/dy*(hg-2*pad);
  const svg=svgEl("svg",{viewBox:`0 0 ${w} ${hg}`,role:"img","aria-label":title.textContent});
  if(xmin<=0&&xmax>=0)svg.appendChild(svgEl("line",{x1:X(0),x2:X(0),y1:pad,y2:hg-pad,class:"math-axis"}));
  if(ymin<=0&&ymax>=0)svg.appendChild(svgEl("line",{x1:pad,x2:w-pad,y1:Y(0),y2:Y(0),class:"math-axis"}));
  groups.forEach((g,i)=>{
    const pl=svgEl("polyline",{points:g.points.map(p=>`${X(p.x)},${Y(p.y)}`).join(" "),class:`math-series math-series-${i%6}`});
    svg.appendChild(pl);
  });
  for(const m of (v.markers||[])){
    if(Number.isFinite(Number(m.x))&&Number.isFinite(Number(m.y)))svg.appendChild(svgEl("circle",{cx:X(Number(m.x)),cy:Y(Number(m.y)),r:4,class:"math-marker"}));
  }
  card.appendChild(svg);
  const legend=document.createElement("div");legend.className="math-legend";
  legend.textContent=groups.map(g=>g.label).join(" · ");card.appendChild(legend);
  host.appendChild(card);
}
export function renderViewSpec(host,spec){
  host.innerHTML="";
  for(const v of pickViews(spec)){
    if(["cartesian-function","derivative","accumulated-integral","parametric","polar"].includes(v?.kind)||pointsOf(v||{}).length)renderCartesian(host,v);
    else{const card=document.createElement("div");card.className="math-card";const pre=document.createElement("pre");pre.textContent=JSON.stringify(v,null,2);card.appendChild(pre);host.appendChild(card);}
  }
}
