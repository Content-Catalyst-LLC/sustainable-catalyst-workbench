/**
 * UVR-01.3 — Workbench graph-to-report handoff (v1).
 * Pure data contract; does not claim CO2 removal, certify measurements,
 * or export a rendered figure by itself.
 */
export function makeReportFigureReference({graph, projectId, researchSessionId = null, reportId = null, caption = "", figureNumber = null, sourceRefs = [], rendered = null}) {
  if (!graph || typeof graph !== "object") throw new TypeError("Saved graph required");
  if (!graph.id || typeof graph.id !== "string") throw new TypeError("Saved graph ID required");
  if (!projectId || typeof projectId !== "string") throw new TypeError("Project ID required");
  if (graph.projectId && graph.projectId !== projectId) throw new Error("Graph belongs to a different project");
  if (researchSessionId && graph.researchSessionId && researchSessionId !== graph.researchSessionId) throw new Error("Research session mismatch");
  if (!Array.isArray(sourceRefs) || sourceRefs.some(x => typeof x !== "string" || !x.trim())) throw new TypeError("sourceRefs must be nonempty strings");
  if (rendered != null && (typeof rendered !== "object" || Array.isArray(rendered))) throw new TypeError("rendered must be an object");
  const title = String(graph.title || "Untitled graph");
  return {
    schema: "sc-workbench-report-figure/1.0",
    sourceSystem: "sustainable-catalyst-workbench",
    projectId,
    researchSessionId: researchSessionId || graph.researchSessionId || null,
    graphId: graph.id,
    reportId: reportId || null,
    figureNumber: figureNumber == null ? null : String(figureNumber),
    title,
    caption: String(caption),
    sourceRefs: [...new Set(sourceRefs)],
    graphType: graph.graphType || "cartesian",
    graphRevision: graph.updatedAt || null,
    renderAvailable: rendered != null,
    provenance: { scientificVerification: "not-asserted", dataOrigin: "referenced-saved-graph" }
  };
}
export function figureReferenceMarkdown(ref) {
  if (!ref || ref.schema !== "sc-workbench-report-figure/1.0") throw new TypeError("Invalid report figure reference");
  const number = ref.figureNumber ? `Figure ${ref.figureNumber}: ` : "";
  const caption = ref.caption || ref.title;
  return `${number}${caption}\n\nSource: Sustainable Catalyst Workbench graph \`${ref.graphId}\` (project \`${ref.projectId}\`).`;
}
