import { createHash } from "node:crypto";
import { makeReportFigureReference } from "./report-figure-reference.mjs";

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  if (typeof value === "number" && !Number.isFinite(value)) throw new TypeError("Non-finite value");
  return value;
}
function sha256(value) { return createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex"); }

/**
 * Construct a deterministic, portable JSON *view-spec* artifact from an
 * authorized Graph Studio render response. This is not SVG/PNG and not a
 * persisted report attachment. Authorization must be enforced by the API
 * caller; this function enforces only returned resource consistency.
 */
export function packageGraphRenderForReport({response, expectedProjectId, expectedGraphId, researchSessionId = null, reportId = null, figureNumber = null, caption = "", sourceRefs = []}) {
  if (response?.ok !== true || !response.render || typeof response.render !== "object") throw new TypeError("Successful render response required");
  const { graph, views, renderHash, graphObjectHash } = response.render;
  if (!graph || typeof graph !== "object") throw new TypeError("Rendered graph missing");
  if (!expectedProjectId || graph.projectId !== expectedProjectId) throw new Error("Project identity mismatch");
  if (!expectedGraphId || graph.id !== expectedGraphId) throw new Error("Graph identity mismatch");
  if (!Array.isArray(views) || !views.length) throw new TypeError("Nonempty render views required");
  if (typeof renderHash !== "string" || !renderHash) throw new TypeError("Render hash missing");
  if (typeof graph.graphObjectHash !== "string" || !graph.graphObjectHash) throw new TypeError("Graph object hash missing");
  if (graphObjectHash !== undefined && graphObjectHash !== graph.graphObjectHash) throw new Error("Conflicting graph hashes");
  const reference = makeReportFigureReference({graph, projectId:expectedProjectId,researchSessionId,reportId,figureNumber,caption,sourceRefs,rendered:response.render});
  const payload = {
    schema: "sc-workbench-report-view-spec/1.0",
    figureReference:reference,
    sourceIntegrity:{graphObjectHash:graph.graphObjectHash,renderHash},
    renderer:response.render.renderer || null,
    viewSpecAuthority:response.render.viewSpecAuthority || null,
    views:structuredClone(views),
    representation:"json-view-spec",
    scientificVerification:"not-asserted"
  };
  return {...payload, artifactSha256:sha256(payload)};
}
export function verifyGraphReportPackage(pkg) {
  if (!pkg || pkg.schema !== "sc-workbench-report-view-spec/1.0" || typeof pkg.artifactSha256 !== "string") return false;
  const {artifactSha256,...payload}=pkg;
  try { return sha256(payload) === artifactSha256; } catch { return false; }
}
