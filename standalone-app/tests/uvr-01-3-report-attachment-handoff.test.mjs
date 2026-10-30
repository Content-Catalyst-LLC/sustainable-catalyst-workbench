import test from "node:test";
import assert from "node:assert/strict";
import {packageGraphRenderForReport} from "../report-render-package.mjs";
import {createReportFigureHandoff,verifyReportFigureHandoff} from "../report-attachment-handoff.mjs";
function fixture(){
 const graph={id:"graph-1",projectId:"project-1",researchSessionId:"session-1",title:"ERW estimate",updatedAt:"revision-2",graphObjectHash:"graph-hash",graphType:"cartesian"};
 const response={ok:true,render:{graph,views:[{kind:"cartesian-function",series:[{points:[{x:0,y:1},{x:1,y:1}]}]}],renderHash:"render-hash",graphObjectHash:"graph-hash"}};
 const pkg=packageGraphRenderForReport({response,expectedProjectId:"project-1",expectedGraphId:"graph-1",researchSessionId:"session-1",reportId:"report-1",caption:"Illustrative model output",sourceRefs:["source-a"]});
 const destination={verified:true,adapter:"research-reporting-adapter-v1",projectId:"project-1",reportId:"report-1",researchSessionId:"session-1",graphId:"graph-1",graphRevision:"revision-2",graphObjectHash:"graph-hash",renderHash:"render-hash"};
 return {pkg,destination};
}
test("creates a verifiable portable SVG manifest without claiming persistence",()=>{
 const {pkg,destination}=fixture();
 const handoff=createReportFigureHandoff({pkg,destination});
 assert.equal(handoff.manifest.persistence,"not-performed");
 assert.equal(handoff.manifest.figure.scientificVerification,"not-asserted");
 assert.equal(handoff.manifest.figure.sourceRefs[0],"source-a");
 assert.ok(verifyReportFigureHandoff(handoff));
 handoff.svg+="modified";
 assert.equal(verifyReportFigureHandoff(handoff),false);
});
test("rejects an unverified destination",()=>{const {pkg,destination}=fixture();destination.verified=false;assert.throws(()=>createReportFigureHandoff({pkg,destination}),/verified/);});
test("rejects cross-project and cross-report attachment",()=>{
 const {pkg,destination}=fixture();
 assert.throws(()=>createReportFigureHandoff({pkg,destination:{...destination,projectId:"foreign"}}),/Cross-project/);
 assert.throws(()=>createReportFigureHandoff({pkg,destination:{...destination,reportId:"foreign"}}),/Report identity/);
});
test("rejects stale revision, cross-session, and different render hashes",()=>{
 const {pkg,destination}=fixture();
 for(const [field,value] of [["graphRevision","old"],["researchSessionId","foreign"],["renderHash","wrong"],["graphObjectHash","wrong"],["graphId","foreign"]]){
  assert.throws(()=>createReportFigureHandoff({pkg,destination:{...destination,[field]:value}}));
 }
});
test("rejects modified render-package data",()=>{
 const {pkg,destination}=fixture();pkg.views[0].series[0].points[0].y=123;
 assert.throws(()=>createReportFigureHandoff({pkg,destination}),/modified/);
});
