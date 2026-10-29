import test from "node:test";
import assert from "node:assert/strict";
import {packageGraphRenderForReport} from "../report-render-package.mjs";
import {renderReportSvg} from "../report-svg-export.mjs";
const response={ok:true,render:{graph:{id:"g",projectId:"p",title:"Sine <model>",graphObjectHash:"g-hash",series:[]},views:[{series:[{points:[{x:0,y:0},{x:1,y:1},{x:2,y:0}]}]}],renderHash:"r-hash",renderer:"Graph Studio"}};
const build=(r=response)=>packageGraphRenderForReport({response:r,expectedProjectId:"p",expectedGraphId:"g",caption:"Test & validate"});
test("produces deterministic SVG from explicit numeric data",()=>{const svg=renderReportSvg(build());assert.equal(svg,renderReportSvg(build()));assert.match(svg,/^<svg /);assert.match(svg,/<polyline /);assert.match(svg,/Sine &lt;model&gt;/);assert.match(svg,/Test &amp; validate/);});
test("rejects modified package",()=>{const p=build();p.views[0].series[0].points[0].y=12;assert.throws(()=>renderReportSvg(p),/modified/);});
test("rejects unsupported nonnumeric view series",()=>{const r=structuredClone(response);r.render.views[0].series[0].points=[{x:"bad",y:0},{x:1,y:1}];assert.throws(()=>renderReportSvg(build(r)),/numeric/);});
test("rejects missing point values",()=>{const r=structuredClone(response);r.render.views[0].series[0].points=[{x:0,y:0}];assert.throws(()=>renderReportSvg(build(r)),/at least two/);});
test("rejects invalid dimensions",()=>assert.throws(()=>renderReportSvg(build(),{width:4}),/size/));

test("supports live Graph Studio parallel numeric x/y series",()=>{
 const r=structuredClone(response);
 r.render.views=[{kind:"cartesian-function",series:[{expression:"sin(x)",label:"Sine",seriesId:"s1",x:[0,1,2],y:[0,1,0]}]}];
 const svg=renderReportSvg(build(r));
 assert.match(svg,/<polyline /);
});
test("rejects mismatched parallel x/y array lengths",()=>{
 const r=structuredClone(response);
 r.render.views=[{kind:"cartesian-function",series:[{x:[0,1],y:[0]}]}];
 assert.throws(()=>renderReportSvg(build(r)),/matching lengths/);
});
test("rejects nonfinite parallel x/y entries",()=>{
 const r=structuredClone(response);
 r.render.views=[{kind:"cartesian-function",series:[{x:[0,1],y:[0,null]}]}];
 assert.throws(()=>renderReportSvg(build(r)),/finite numeric/);
});
