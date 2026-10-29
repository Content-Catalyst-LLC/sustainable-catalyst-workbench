import test from "node:test";
import assert from "node:assert/strict";
import {makeReportFigureReference, figureReferenceMarkdown} from "../report-figure-reference.mjs";

const graph={id:"graph-123",projectId:"project-A",researchSessionId:"session-1",title:"ERW sensitivity",graphType:"cartesian",updatedAt:"2026-10-28T00:00:00Z"};
test("creates versioned project-scoped figure reference",()=>{
 const ref=makeReportFigureReference({graph,projectId:"project-A",researchSessionId:"session-1",reportId:"wexford",figureNumber:2,caption:"Illustrative scenario",sourceRefs:["doi:10.1234/example","doi:10.1234/example"],rendered:{status:"ok"}});
 assert.equal(ref.schema,"sc-workbench-report-figure/1.0");
 assert.equal(ref.graphId,graph.id);
 assert.deepEqual(ref.sourceRefs,["doi:10.1234/example"]);
 assert.equal(ref.provenance.scientificVerification,"not-asserted");
 assert.match(figureReferenceMarkdown(ref),/Figure 2: Illustrative scenario/);
});
test("rejects cross-project attachment",()=>assert.throws(()=>makeReportFigureReference({graph,projectId:"project-B"}),/different project/));
test("rejects conflicting research session",()=>assert.throws(()=>makeReportFigureReference({graph,projectId:"project-A",researchSessionId:"session-2"}),/session mismatch/));
test("rejects missing graph identity",()=>assert.throws(()=>makeReportFigureReference({graph:{},projectId:"project-A"}),/graph ID/));
test("does not infer a verification claim from rendered output",()=>{
 const ref=makeReportFigureReference({graph,projectId:"project-A",rendered:{verified:true}});
 assert.equal(ref.provenance.scientificVerification,"not-asserted");
});
test("requires valid source reference array",()=>assert.throws(()=>makeReportFigureReference({graph,projectId:"project-A",sourceRefs:[null]}),/sourceRefs/));
