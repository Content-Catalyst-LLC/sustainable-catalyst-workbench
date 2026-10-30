/** UVR-01.3 — immutable, destination-verified report figure handoff.
 * No network writes: a reporting adapter must independently authorize and persist.
 */
import {createHash} from "node:crypto";
import {verifyGraphReportPackage} from "./report-render-package.mjs";
import {renderReportSvg} from "./report-svg-export.mjs";

const digest=value=>createHash("sha256").update(value).digest("hex");
const validId=value=>typeof value==="string"&&value.trim().length>0;
export function createReportFigureHandoff({pkg,destination,svg=null}) {
  if(!verifyGraphReportPackage(pkg))throw new Error("Invalid or modified graph render package");
  const ref=pkg.figureReference;
  if(!ref||ref.schema!=="sc-workbench-report-figure/1.0")throw new Error("Invalid graph figure reference");
  if(!validId(ref.graphId)||!validId(ref.projectId)||!validId(pkg.sourceIntegrity?.renderHash)||!validId(pkg.sourceIntegrity?.graphObjectHash))throw new Error("Missing graph identity or integrity hashes");
  if(!destination||destination.verified!==true||!validId(destination.reportId)||!validId(destination.projectId)||!validId(destination.adapter))throw new Error("Explicit verified destination mapping required");
  if(ref.reportId&&ref.reportId!==destination.reportId)throw new Error("Report identity mismatch");
  if(ref.projectId!==destination.projectId)throw new Error("Cross-project handoff refused");
  if(ref.researchSessionId&&destination.researchSessionId!==ref.researchSessionId)throw new Error("Research session mismatch");
  if(destination.graphId!==ref.graphId)throw new Error("Graph identity mismatch");
  if(destination.graphRevision!==ref.graphRevision)throw new Error("Graph revision mismatch");
  if(destination.graphObjectHash!==pkg.sourceIntegrity.graphObjectHash)throw new Error("Graph provenance mismatch");
  if(destination.renderHash!==pkg.sourceIntegrity.renderHash)throw new Error("Render provenance mismatch");
  const content=svg??renderReportSvg(pkg);
  if(typeof content!=="string"||!content.startsWith("<svg ")||!content.includes("</svg>"))throw new Error("Invalid SVG payload");
  const artifact={
    schema:"sc-workbench-report-figure-handoff/1.0",
    representation:"svg",
    source:{system:ref.sourceSystem,projectId:ref.projectId,researchSessionId:ref.researchSessionId,graphId:ref.graphId,graphRevision:ref.graphRevision,graphObjectHash:pkg.sourceIntegrity.graphObjectHash,renderHash:pkg.sourceIntegrity.renderHash,viewSpecSha256:pkg.artifactSha256},
    destination:{adapter:destination.adapter,projectId:destination.projectId,reportId:destination.reportId,researchSessionId:destination.researchSessionId??null},
    figure:{title:ref.title,caption:ref.caption,figureNumber:ref.figureNumber,sourceRefs:[...ref.sourceRefs],scientificVerification:"not-asserted"},
    svgSha256:digest(content),
    svgBytes:Buffer.byteLength(content,"utf8"),
    persistence:"not-performed",
  };
  return {manifest:artifact,svg:content};
}
export function verifyReportFigureHandoff(handoff) {
  if(!handoff?.manifest||typeof handoff.svg!=="string")return false;
  return handoff.manifest.schema==="sc-workbench-report-figure-handoff/1.0" &&
    handoff.manifest.svgSha256===digest(handoff.svg) &&
    handoff.manifest.svgBytes===Buffer.byteLength(handoff.svg,"utf8") &&
    handoff.manifest.persistence==="not-performed";
}
