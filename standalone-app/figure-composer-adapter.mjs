/**
 * UVR-01.3.2 Figure Composer adapter.
 * The caller must provide an explicitly verified mapping from saved graph
 * to Figure Composer job and panel identifiers. No ID equivalence is assumed.
 * This function only builds a request, never sends it or stores an artifact.
 */
export function buildFigureComposeRequest({figureReference, mapping, panel, title, subtitle = "", columns = 1}) {
  if (figureReference?.schema !== "sc-workbench-report-figure/1.0") throw new TypeError("Invalid figure reference");
  if (!mapping || typeof mapping !== "object") throw new TypeError("Verified mapping required");
  if (mapping.graphId !== figureReference.graphId) throw new Error("Graph ID mismatch");
  if (mapping.workbenchProjectId !== figureReference.projectId) throw new Error("Workbench project mismatch");
  if (mapping.researchSessionId && figureReference.researchSessionId && mapping.researchSessionId !== figureReference.researchSessionId) throw new Error("Research session mismatch");
  if (mapping.verified !== true) throw new Error("Unverified Figure Composer mapping");
  if (typeof mapping.projectKey !== "string" || !mapping.projectKey.trim()) throw new TypeError("Figure Composer projectKey required");
  if (!Array.isArray(mapping.jobIds) || !mapping.jobIds.length || mapping.jobIds.some(x => typeof x !== "string" || !x.trim())) throw new TypeError("Nonempty verified jobIds required");
  if (!panel || typeof panel !== "object" || Array.isArray(panel)) throw new TypeError("Verified Figure Composer panel required");
  if (!Number.isInteger(columns) || columns < 1) throw new TypeError("Positive column count required");
  return {
    projectKey: mapping.projectKey,
    jobIds: [...new Set(mapping.jobIds)],
    panels: [structuredClone(panel)],
    title: String(title ?? figureReference.title),
    subtitle: String(subtitle),
    caption: figureReference.caption,
    columns
  };
}
