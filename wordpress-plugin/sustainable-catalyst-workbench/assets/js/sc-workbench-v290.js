(() => {
  'use strict';

  const VERSION = (window.SCWBV290 && window.SCWBV290.version) || '2.9.0';
  const PREFIX = (window.SCWBV290 && window.SCWBV290.storagePrefix) || 'scwb-v290:';

  const $ = (root, selector) => root.querySelector(selector);
  const $$ = (root, selector) => Array.from(root.querySelectorAll(selector));
  const cleanLines = (value) => String(value || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const now = () => new Date().toISOString();
  const slug = (value) => String(value || 'record').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'record';

  function parseJSON(value, label) {
    try {
      return JSON.parse(String(value || '').trim() || '[]');
    } catch (error) {
      throw new Error(`${label} must contain valid JSON: ${error.message}`);
    }
  }

  function fields(root) {
    const result = {};
    $$ (root, '[data-scwb-v290-field]').forEach((input) => {
      result[input.dataset.scwbV290Field] = input.value;
    });
    return result;
  }

  function canonical(value) {
    if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
    if (value && typeof value === 'object') {
      return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
    }
    return JSON.stringify(value);
  }

  async function sha256(value) {
    const data = new TextEncoder().encode(typeof value === 'string' ? value : canonical(value));
    const digest = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  function download(filename, body, type) {
    const blob = new Blob([body], { type: type || 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function traceability(input) {
    const requirements = parseJSON(input.requirements, 'Requirements');
    const verifications = parseJSON(input.verifications, 'Verification records');
    const known = new Map(requirements.map((item) => [String(item.id), item]));
    const links = new Map(requirements.map((item) => [String(item.id), []]));
    const unknown = [];
    verifications.forEach((record) => {
      (record.requirement_ids || []).forEach((id) => {
        if (known.has(String(id))) links.get(String(id)).push(String(record.id));
        else unknown.push({ verificationId: record.id, requirementId: id });
      });
    });
    const uncovered = requirements.filter((item) => !links.get(String(item.id)).length).map((item) => item.id);
    const failedCritical = [];
    verifications.filter((item) => item.status === 'fail').forEach((item) => {
      (item.requirement_ids || []).forEach((id) => {
        const requirement = known.get(String(id));
        if (requirement && requirement.priority === 'critical') failedCritical.push(id);
      });
    });
    return {
      ok: unknown.length === 0 && failedCritical.length === 0,
      schema: 'sc-workbench-requirements-traceability/1.0',
      version: VERSION,
      generatedAt: now(),
      requirementCount: requirements.length,
      verificationCount: verifications.length,
      coveragePercent: requirements.length ? Number((((requirements.length - uncovered.length) / requirements.length) * 100).toFixed(4)) : 0,
      uncoveredRequirements: uncovered,
      failedCriticalRequirements: [...new Set(failedCritical)],
      unknownRequirementLinks: unknown,
      traceability: requirements.map((item) => ({ requirementId: item.id, verificationIds: links.get(String(item.id)) })),
      requirements,
      verifications,
    };
  }

  function dossier(input, productMode) {
    const sections = parseJSON(input.sections, 'Sections');
    const empty = sections.filter((section) => !String(section.content || '').trim()).map((section) => section.id);
    return {
      ok: empty.length === 0,
      schema: productMode ? 'sc-workbench-product-dossier/1.0' : 'sc-workbench-technical-document/1.0',
      version: VERSION,
      generatedAt: now(),
      projectId: 'default',
      title: input.title || (productMode ? 'Product technical dossier' : 'Technical document'),
      productName: input.product_name || '',
      revision: input.revision || '0.1.0',
      owner: input.owner || '',
      tableOfContents: sections.map((section, index) => ({ number: index + 1, id: section.id, title: section.title, status: section.status || 'draft' })),
      sections,
      assumptions: cleanLines(input.assumptions),
      limitations: cleanLines(input.limitations),
      risks: cleanLines(input.risks),
      completeness: {
        sectionCount: sections.length,
        completeSections: sections.length - empty.length,
        emptySections: empty,
        percent: sections.length ? Number((((sections.length - empty.length) / sections.length) * 100).toFixed(4)) : 0,
      },
    };
  }

  function revisions(input) {
    const revisions = parseJSON(input.revisions, 'Revision history');
    const changes = parseJSON(input.changes, 'Engineering changes');
    const known = new Set(revisions.map((item) => String(item.revision)));
    return {
      ok: changes.every((item) => !item.target_revision || known.has(String(item.target_revision))),
      schema: 'sc-workbench-revision-change-audit/1.0',
      version: VERSION,
      generatedAt: now(),
      revisionCount: revisions.length,
      changeCount: changes.length,
      latestRevision: revisions.length ? revisions[revisions.length - 1].revision : null,
      unapprovedRevisions: revisions.filter((item) => !item.approved).map((item) => item.revision),
      revisionsMissingArtifactHash: revisions.filter((item) => !item.artifact_hash).map((item) => item.revision),
      openChanges: changes.filter((item) => ['proposed', 'approved', 'implemented'].includes(item.status)).map((item) => item.id),
      changesWithUnknownTargetRevision: changes.filter((item) => item.target_revision && !known.has(String(item.target_revision))).map((item) => item.id),
      revisions,
      changes,
    };
  }

  function evidence(input) {
    const records = parseJSON(input.records, 'Evidence records');
    const ids = new Set();
    const duplicateIds = [];
    records.forEach((item) => {
      if (ids.has(String(item.id))) duplicateIds.push(item.id);
      ids.add(String(item.id));
    });
    const kindCounts = {};
    records.forEach((item) => { kindCounts[item.kind || 'other'] = (kindCounts[item.kind || 'other'] || 0) + 1; });
    return {
      ok: duplicateIds.length === 0 && records.every((item) => item.content_hash),
      schema: 'sc-workbench-evidence-register/1.0',
      version: VERSION,
      generatedAt: now(),
      recordCount: records.length,
      duplicateIds,
      recordsMissingHash: records.filter((item) => !item.content_hash).map((item) => item.id),
      recordsMissingSource: records.filter((item) => !item.source_uri).map((item) => item.id),
      unapprovedRecords: records.filter((item) => !item.approved).map((item) => item.id),
      kindCounts,
      records,
    };
  }

  function readiness(input) {
    const items = parseJSON(input.items, 'Readiness items');
    const weights = { 'not-started': 0, 'in-progress': 0.5, complete: 1, blocked: 0, 'not-applicable': 1 };
    const categories = {};
    items.forEach((item) => {
      if (!categories[item.category]) categories[item.category] = [];
      categories[item.category].push(weights[item.status] ?? 0);
    });
    const categoryScores = {};
    Object.keys(categories).sort().forEach((category) => {
      const values = categories[category];
      categoryScores[category] = Number(((values.reduce((sum, value) => sum + value, 0) / values.length) * 100).toFixed(4));
    });
    const overall = items.length ? items.reduce((sum, item) => sum + (weights[item.status] ?? 0), 0) / items.length * 100 : 0;
    const blockers = items.filter((item) => item.status === 'blocked').map((item) => item.id);
    const criticalIncomplete = items.filter((item) => item.critical && !['complete', 'not-applicable'].includes(item.status)).map((item) => item.id);
    return {
      ok: blockers.length === 0 && criticalIncomplete.length === 0 && overall >= 90,
      schema: 'sc-workbench-product-readiness/1.0',
      version: VERSION,
      generatedAt: now(),
      gate: blockers.length === 0 && criticalIncomplete.length === 0 && overall >= 90 ? 'ready' : 'not-ready',
      overallPercent: Number(overall.toFixed(4)),
      categoryScores,
      blockers,
      criticalIncompleteItems: criticalIncomplete,
      completeItemsMissingEvidence: items.filter((item) => item.status === 'complete' && !(item.evidence_ids || []).length).map((item) => item.id),
      items,
    };
  }

  async function analyze(root) {
    const panel = root.dataset.scwbV290Panel;
    const input = fields(root);
    let record;
    if (panel === 'traceability') record = traceability(input);
    else if (panel === 'revision') record = revisions(input);
    else if (panel === 'evidence') record = evidence(input);
    else if (panel === 'readiness') record = readiness(input);
    else record = dossier(input, panel === 'product');
    record.recordHash = await sha256(record);
    return record;
  }

  function markdown(record) {
    const lines = [`# ${record.title || record.schema}`, '', `- Version: ${record.version}`, `- Generated: ${record.generatedAt}`, `- Record hash: ${record.recordHash || ''}`, ''];
    if (record.productName) lines.push(`**Product:** ${record.productName}`, '');
    if (record.revision) lines.push(`**Revision:** ${record.revision}`, '');
    if (record.tableOfContents) {
      lines.push('## Table of contents', '');
      record.tableOfContents.forEach((item) => lines.push(`${item.number}. ${item.title} (${item.status})`));
      lines.push('');
    }
    if (record.sections) {
      record.sections.forEach((section, index) => {
        lines.push(`## ${index + 1}. ${section.title}`, '', section.content || '_No content_', '');
        if ((section.source_records || []).length) lines.push(`Sources: ${(section.source_records || []).join(', ')}`, '');
      });
    } else {
      lines.push('## Structured record', '', '```json', JSON.stringify(record, null, 2), '```', '');
    }
    return lines.join('\n');
  }

  function htmlDocument(record) {
    const escaped = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
    const body = record.sections
      ? record.sections.map((section, index) => `<section><h2>${index + 1}. ${escaped(section.title)}</h2><p>${escaped(section.content || '').replace(/\n/g, '<br>')}</p></section>`).join('')
      : `<pre>${escaped(JSON.stringify(record, null, 2))}</pre>`;
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escaped(record.title || record.schema)}</title><style>body{font-family:system-ui,sans-serif;max-width:920px;margin:40px auto;padding:0 24px;line-height:1.6;color:#161616}h1,h2{line-height:1.15}section{border-top:1px solid #ddd;padding-top:24px;margin-top:24px}pre{white-space:pre-wrap;background:#f5f5f5;padding:20px}</style></head><body><h1>${escaped(record.title || record.schema)}</h1><p><strong>Version:</strong> ${escaped(record.version)}<br><strong>Generated:</strong> ${escaped(record.generatedAt)}<br><strong>Record hash:</strong> ${escaped(record.recordHash || '')}</p>${body}</body></html>`;
  }

  function setResult(root, record, message) {
    root.__scwbV290Record = record;
    const result = $(root, '[data-scwb-v290-result]');
    const summary = $(root, '[data-scwb-v290-summary]');
    const status = $(root, '[data-scwb-v290-status]');
    if (result) result.textContent = JSON.stringify(record, null, 2);
    if (summary) summary.innerHTML = `<strong>${record.ok ? 'Record ready' : 'Review required'}</strong><span>${message || record.schema}</span><span>SHA-256: ${record.recordHash || 'pending'}</span>`;
    if (status) status.textContent = record.ok ? 'Validated browser-local record' : 'Review findings before release';
  }

  async function connect(root) {
    const input = fields(root);
    const base = String(input.runner_url || 'http://127.0.0.1:8787').replace(/\/$/, '');
    const code = String(input.pairing_code || '').trim();
    if (!code) throw new Error('Enter the six-digit pairing code shown by the local Workbench Runner.');
    const pairResponse = await fetch(`${base}/pair`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, origin: window.location.origin }),
    });
    const pair = await pairResponse.json();
    if (!pairResponse.ok || !pair.token) throw new Error(pair.error || 'Runner pairing failed.');
    const toolsResponse = await fetch(`${base}/documentation-tools`, { headers: { Authorization: `Bearer ${pair.token}` } });
    const tools = await toolsResponse.json();
    if (!toolsResponse.ok) throw new Error(tools.error || 'Documentation-tool discovery failed.');
    return { ok: true, schema: 'sc-workbench-documentation-tools/1.0', version: VERSION, generatedAt: now(), runner: base, tools: tools.tools || [], executionBoundary: tools.executionBoundary || {} };
  }

  function storageKey(root) {
    return `${PREFIX}${root.dataset.scwbV290Project || 'default'}:${root.dataset.scwbV290Panel || 'documentation'}`;
  }

  async function handle(root, action) {
    try {
      if (action === 'analyze') {
        const record = await analyze(root);
        setResult(root, record);
      } else if (action === 'connect') {
        const record = await connect(root);
        record.recordHash = await sha256(record);
        setResult(root, record, 'Local documentation-tool discovery completed.');
      } else if (action === 'save') {
        const record = root.__scwbV290Record || await analyze(root);
        localStorage.setItem(storageKey(root), JSON.stringify({ fields: fields(root), record }));
        setResult(root, record, 'Saved to this browser.');
      } else {
        const record = root.__scwbV290Record || await analyze(root);
        const name = `${slug(record.title || root.dataset.scwbV290Panel)}-${record.revision || VERSION}`;
        if (action === 'export-json') download(`${name}.json`, JSON.stringify(record, null, 2), 'application/json');
        if (action === 'export-markdown') download(`${name}.md`, markdown(record), 'text/markdown');
        if (action === 'export-html') download(`${name}.html`, htmlDocument(record), 'text/html');
        setResult(root, record, 'Export generated from the current versioned record.');
      }
    } catch (error) {
      const summary = $(root, '[data-scwb-v290-summary]');
      const status = $(root, '[data-scwb-v290-status]');
      if (summary) summary.innerHTML = `<strong>Unable to complete action</strong><span>${String(error.message || error)}</span>`;
      if (status) status.textContent = 'Input or connection error';
    }
  }

  function restore(root) {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey(root)) || 'null');
      if (!saved || !saved.fields) return;
      Object.entries(saved.fields).forEach(([key, value]) => {
        const input = $(root, `[data-scwb-v290-field="${CSS.escape(key)}"]`);
        if (input) input.value = value;
      });
      if (saved.record) setResult(root, saved.record, 'Restored from this browser.');
    } catch (_) { /* Ignore damaged local state. */ }
  }

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-scwb-v290-action]');
    if (!button) return;
    const root = button.closest('[data-scwb-v290-panel]');
    if (!root) return;
    event.preventDefault();
    handle(root, button.dataset.scwbV290Action);
  });

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-scwb-v290-panel]').forEach(restore);
  });
})();
