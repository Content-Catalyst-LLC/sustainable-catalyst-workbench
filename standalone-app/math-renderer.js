const SVG="http://www.w3.org/2000/svg";

function extent(values){
  const a=values.filter(v=>Number.isFinite(v));
  if(!a.length) return [-1,1];
  let lo=Math.min(...a), hi=Math.max(...a);
  if(lo===hi){ lo-=1; hi+=1; }
  const pad=(hi-lo)*0.05;
  return [lo-pad,hi+pad];
}
function scale(v,a,b,c,d){ return c+(v-a)*(d-c)/(b-a); }
function svgEl(name,attrs={}){
  const n=document.createElementNS(SVG,name);
  for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v));
  return n;
}
function renderCartesian(view){
  const wrap=document.createElement("div");
  wrap.className="math-view";
  const w=760,h=360,p=36;
  const svg=svgEl("svg",{viewBox:`0 0 ${w} ${h}`,role:"img"});
  const allX=[],allY=[];
  for(const s of view.series||[]){ allX.push(...(s.x||[])); allY.push(...(s.y||[]).filter(Number.isFinite)); }
  const [xmin,xmax]=extent(allX),[ymin,ymax]=extent(allY);
  svg.append(svgEl("line",{x1:p,y1:scale(0,ymin,ymax,h-p,p),x2:w-p,y2:scale(0,ymin,ymax,h-p,p),class:"math-axis"}));
  svg.append(svgEl("line",{x1:scale(0,xmin,xmax,p,w-p),y1:p,x2:scale(0,xmin,xmax,p,w-p),y2:h-p,class:"math-axis"}));
  for(const s of view.series||[]){
    const pts=[];
    for(let i=0;i<Math.min(s.x?.length||0,s.y?.length||0);i++){
      const x=s.x[i],y=s.y[i];
      if(Number.isFinite(x)&&Number.isFinite(y)) pts.push(`${scale(x,xmin,xmax,p,w-p)},${scale(y,ymin,ymax,h-p,p)}`);
    }
    svg.append(svgEl("polyline",{points:pts.join(" "),class:"math-series",fill:"none"}));
  }
  for(const m of view.markers||[]){
    if(!Number.isFinite(m.x)||!Number.isFinite(m.y)) continue;
    svg.append(svgEl("circle",{cx:scale(m.x,xmin,xmax,p,w-p),cy:scale(m.y,ymin,ymax,h-p,p),r:4,class:"math-marker"}));
  }
  const crossV=svgEl("line",{x1:0,y1:p,x2:0,y2:h-p,class:"math-crosshair"});
  const crossH=svgEl("line",{x1:p,y1:0,x2:w-p,y2:0,class:"math-crosshair"});
  crossV.style.display=crossH.style.display="none";
  svg.append(crossV,crossH);
  svg.addEventListener("pointermove",e=>{
    const r=svg.getBoundingClientRect();
    const x=(e.clientX-r.left)*w/r.width,y=(e.clientY-r.top)*h/r.height;
    crossV.setAttribute("x1",x);crossV.setAttribute("x2",x);
    crossH.setAttribute("y1",y);crossH.setAttribute("y2",y);
    crossV.style.display=crossH.style.display="";
  });
  svg.addEventListener("pointerleave",()=>{crossV.style.display=crossH.style.display="none";});
  wrap.append(svg);
  return wrap;
}
function renderImplicit(view){
  const wrap=document.createElement("div");
  wrap.className="math-view";
  const canvas=document.createElement("canvas");
  canvas.width=640;canvas.height=360;
  const ctx=canvas.getContext("2d");
  const z=view.z||[], rows=z.length, cols=rows?(z[0]||[]).length:0;
  if(rows&&cols){
    for(let r=0;r<rows;r++) for(let c=0;c<cols;c++){
      const v=z[r][c];
      if(v===null||!Number.isFinite(v)) continue;
      const mag=Math.min(1,Math.abs(v)/5);
      const shade=Math.round(235-150*mag);
      ctx.fillStyle=`rgb(${shade},${shade},${shade})`;
      ctx.fillRect(c*canvas.width/cols,canvas.height-(r+1)*canvas.height/rows,canvas.width/cols+1,canvas.height/rows+1);
    }
  }
  wrap.append(canvas); return wrap;
}
function renderLinkedTable(view){
  const table=document.createElement("table"); table.className="math-table";
  const thead=document.createElement("thead"),tr=document.createElement("tr");
  for(const c of view.columns||[]){ const th=document.createElement("th");th.textContent=c;tr.append(th); }
  thead.append(tr);table.append(thead);
  const tbody=document.createElement("tbody");
  for(const row of (view.rows||[]).slice(0,200)){
    const tr=document.createElement("tr");
    for(const c of view.columns||[]){ const td=document.createElement("td");td.textContent=row[c]??"";tr.append(td); }
    tbody.append(tr);
  }
  table.append(tbody); return table;
}
function renderView(view){
  if(["cartesian-function","derivative","accumulated-integral","parametric","polar"].includes(view.kind)) return renderCartesian(view);
  if(view.kind==="implicit-field") return renderImplicit(view);
  if(view.kind==="linked-table") return renderLinkedTable(view);
  const pre=document.createElement("pre");pre.textContent=JSON.stringify(view,null,2);return pre;
}
export function renderMathematicalViews(container, viewSpec){
  container.replaceChildren();
  const views=viewSpec?.result?.views||viewSpec?.views||[];
  for(const view of views){
    const card=document.createElement("section");card.className="math-card";
    const title=document.createElement("h3");title.textContent=view.kind;
    card.append(title,renderView(view));container.append(card);
  }
  return views.length;
}
