function svgEl(name,attrs={}){const e=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));return e;}
function pickViews(spec){if(Array.isArray(spec))return spec;if(Array.isArray(spec?.views))return spec.views;if(Array.isArray(spec?.viewSpec?.views))return spec.viewSpec.views;if(spec?.viewSpec)return [spec.viewSpec];return [spec];}
function pointsOf(v){return v.points||v.series?.[0]?.points||v.data?.points||v.samples||[];}
function renderCartesian(host,v){
  const card=document.createElement("div");card.className="math-card";
  const h=document.createElement("h3");h.textContent=v.title||v.kind||"Mathematical view";card.appendChild(h);
  const pts=pointsOf(v).map(p=>Array.isArray(p)?{x:Number(p[0]),y:Number(p[1])}:{x:Number(p.x),y:Number(p.y)}).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
  if(!pts.length){const pre=document.createElement("pre");pre.textContent=JSON.stringify(v,null,2);card.appendChild(pre);host.appendChild(card);return;}
  const w=900,hg=420,pad=34,xs=pts.map(p=>p.x),ys=pts.map(p=>p.y),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const dx=(xmax-xmin)||1,dy=(ymax-ymin)||1;
  const X=x=>pad+(x-xmin)/dx*(w-2*pad),Y=y=>hg-pad-(y-ymin)/dy*(hg-2*pad);
  const svg=svgEl("svg",{viewBox:`0 0 ${w} ${hg}`});
  if(xmin<=0&&xmax>=0)svg.appendChild(svgEl("line",{x1:X(0),x2:X(0),y1:pad,y2:hg-pad,class:"math-axis"}));
  if(ymin<=0&&ymax>=0)svg.appendChild(svgEl("line",{x1:pad,x2:w-pad,y1:Y(0),y2:Y(0),class:"math-axis"}));
  svg.appendChild(svgEl("polyline",{points:pts.map(p=>`${X(p.x)},${Y(p.y)}`).join(" "),class:"math-series"}));
  card.appendChild(svg);host.appendChild(card);
}
export function renderViewSpec(host,spec){
  host.innerHTML="";
  for(const v of pickViews(spec)){
    if(["cartesian-function","derivative","accumulated-integral","parametric","polar"].includes(v?.kind)||pointsOf(v||{}).length) renderCartesian(host,v);
    else{const card=document.createElement("div");card.className="math-card";const pre=document.createElement("pre");pre.textContent=JSON.stringify(v,null,2);card.appendChild(pre);host.appendChild(card);}
  }
}
