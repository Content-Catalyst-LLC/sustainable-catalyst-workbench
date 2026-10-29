// UVR-01.3.7: Browser-independent SVG renderer regression tests.
// Run: node --test standalone-app/tests/uvr-01-3-7-numerical-precision.test.cjs
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {pathToFileURL}=require("node:url");
const source=fs.readFileSync(path.join(__dirname,"..","math-renderer.js"),"utf8").replace("./display-range.mjs",pathToFileURL(path.join(__dirname,"..","display-range.mjs")).href);
function element(name){return {name,attributes:{},children:[],textContent:"",setAttribute(k,v){this.attributes[k]=v;},appendChild(child){this.children.push(child);return child;}};}
function descendants(node,name){return (node.children||[]).flatMap(x=>[...(x.name===name?[x]:[]),...descendants(x,name)]);}
async function plot(values){
  const previous=global.document;
  global.document={createElement:element,createElementNS:(_ns,name)=>element(name)};
  try{
    const uri="data:text/javascript;base64,"+Buffer.from(source).toString("base64");
    const {renderViewSpec}=await import(uri);
    const host=element("host");
    renderViewSpec(host,{views:[{kind:"cartesian-function",series:[{label:"sample",points:values.map((y,x)=>({x,y}))}]}]});
    const line=descendants(host,"polyline")[0];
    assert.ok(line,"SVG polyline should render");
    return line.attributes.points.trim().split(/\s+/).map(pair=>pair.split(",").map(Number));
  }finally{global.document=previous;}
}
function yrange(pts){const ys=pts.map(p=>p[1]);return Math.max(...ys)-Math.min(...ys);}
test("sin²(x)+cos²(x) does not amplify round-off into spikes",async()=>{
  const values=Array.from({length:401},(_,i)=>{const x=-10+i/20;return Math.sin(x)**2+Math.cos(x)**2;});
  const pts=await plot(values);
  assert.equal(pts.length,401);
  assert.ok(yrange(pts)<1e-8,`unexpected vertical spread: ${yrange(pts)}`);
});
test("exact constant y=1 remains a horizontal line",async()=>{
  const pts=await plot([1,1,1,1,1]);
  assert.equal(yrange(pts),0);
  assert.ok(pts.every(p=>Number.isFinite(p[1])));
});
test("genuine small-amplitude changes remain visible",async()=>{
  const pts=await plot([1,1+1e-8,1+2e-8]);
  assert.ok(yrange(pts)>300);
});
test("tiny-magnitude nonconstant scientific values remain visible",async()=>{
  const pts=await plot([1e-12,2e-12,3e-12]);
  assert.ok(yrange(pts)>300);
});
test("negative constants and zero stay centered and finite",async()=>{
  for(const y of [-5,0]){
    const pts=await plot([y,y,y]);
    assert.equal(yrange(pts),0);
    assert.ok(pts.every(p=>Number.isFinite(p[1])&&p[1]>34&&p[1]<386));
  }
});
test("existing Graph Studio SVG export implementation stays in frontend",()=>{
  const shell=fs.readFileSync(path.join(__dirname,"..","app-shell.js"),"utf8");
  assert.match(shell,/downloadActiveGraphSvg/);
  assert.match(shell,/export-graph-svg/);
  assert.match(shell,/export\.svg/);
});
