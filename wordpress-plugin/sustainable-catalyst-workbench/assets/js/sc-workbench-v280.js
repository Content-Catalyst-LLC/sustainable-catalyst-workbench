(function () {
  'use strict';
  const CONFIG = window.SCWBV280 || { version: '2.8.0', runnerDefaultUrl: 'http://127.0.0.1:8787', storagePrefix: 'scwb-v280:' };
  const qs = (root, selector) => root.querySelector(selector);
  const parseJSON = (value, fallback) => { try { return JSON.parse(value); } catch (_) { return fallback; } };
  const lines = (value) => String(value || '').split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
  const number = (value, fallback = 0) => { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; };
  const round = (value, digits = 8) => Number.isFinite(Number(value)) ? Number(Number(value).toFixed(digits)) : null;
  const now = () => new Date().toISOString();

  function fields(root) {
    const data = {};
    root.querySelectorAll('[data-scwb-v280-field]').forEach((node) => { data[node.dataset.scwbV280Field] = node.value; });
    return data;
  }
  function storageKey(root) { return CONFIG.storagePrefix + root.dataset.scwbV280Project + ':' + root.dataset.scwbV280Panel; }
  function status(root, text) { const node = qs(root, '[data-scwb-v280-status]'); if (node) node.textContent = text; }
  function result(root, record) {
    root._scwbV280Last = record;
    const node = qs(root, '[data-scwb-v280-result]'); if (node) node.textContent = JSON.stringify(record, null, 2);
    renderSummary(root, record);
  }
  function esc(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[character])); }
  function renderSummary(root, record) {
    const node = qs(root, '[data-scwb-v280-summary]'); if (!node) return;
    const items = [];
    [['Status', record.ok === true ? 'PASS' : record.ok === false ? 'REVIEW' : 'CREATED'], ['Schema', record.schema], ['Tasks', record.taskCount], ['Steps', record.stepCount], ['Duration', record.estimatedCriticalPathMinutes != null ? record.estimatedCriticalPathMinutes + ' min' : record.estimatedDurationMinutes != null ? record.estimatedDurationMinutes + ' min' : null], ['Occurrences', record.occurrenceCount], ['Critical failures', record.criticalFailures], ['Metric failures', record.metricFailures], ['Manifest hash', record.manifestHash ? record.manifestHash.slice(0, 16) + '…' : null]].forEach(([label, value]) => { if (value !== undefined && value !== null && value !== '') items.push('<div class="scwb-v280__metric"><span>' + esc(label) + '</span><strong>' + esc(value) + '</strong></div>'); });
    const findings = Array.isArray(record.findings) ? record.findings : Array.isArray(record.deviations) ? record.deviations.map((item) => ({ code: item })) : [];
    node.innerHTML = '<h3>Workflow record</h3>' + items.join('') + (findings.length ? '<h3 style="margin-top:14px">Findings</h3><ul>' + findings.slice(0, 12).map((item) => '<li>' + esc(item.code || item.reason || JSON.stringify(item)) + '</li>').join('') + '</ul>' : '<p>No recorded findings.</p>');
  }
  function download(filename, content, type) { const blob = content instanceof Blob ? content : new Blob([content], { type: type || 'application/json' }), url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
  function canonical(value) { if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']'; if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map((key) => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'; return JSON.stringify(value); }
  async function sha256(value) { const bytes = new TextEncoder().encode(canonical(value)), digest = await crypto.subtle.digest('SHA-256', bytes); return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join(''); }

  function graphPlan(tasks) {
    const ids = tasks.map((task) => String(task.id || '').trim()).filter(Boolean), findings = [], set = new Set(ids), indegree = {}, children = {}, taskMap = {};
    ids.forEach((id) => { indegree[id] = 0; children[id] = []; });
    tasks.forEach((task) => { const id = String(task.id || '').trim(); taskMap[id] = task; (task.dependencies || []).forEach((dep) => { if (!set.has(dep)) findings.push({ severity: 'critical', code: 'unknown-dependency', task: id, dependency: dep }); else if (dep === id) findings.push({ severity: 'critical', code: 'self-dependency', task: id }); else { indegree[id] += 1; children[dep].push(id); } }); });
    const queue = ids.filter((id) => indegree[id] === 0).sort(), order = [];
    while (queue.length) { const id = queue.shift(); order.push(id); children[id].sort().forEach((child) => { indegree[child] -= 1; if (indegree[child] === 0) queue.push(child); }); }
    if (order.length !== ids.length) findings.push({ severity: 'critical', code: 'dependency-cycle', tasks: ids.filter((id) => indegree[id] > 0) });
    const finish = {};
    order.forEach((id) => { const task = taskMap[id], deps = task.dependencies || [], start = deps.reduce((value, dep) => Math.max(value, finish[dep] || 0), 0); finish[id] = start + number(task.duration != null ? task.duration : task.duration_minutes, 1); });
    return { order, findings, duration: Math.max(0, ...Object.values(finish)), taskMap };
  }

  function evaluateRules(observed, rules) {
    const records = [], counts = { pass: 0, fail: 0 }; let criticalFailures = 0;
    rules.forEach((rule) => {
      const value = observed[rule.key], op = rule.operator || 'between', severity = rule.severity || 'critical'; let passed = false, reason = 'rule-failed';
      if (!Object.prototype.hasOwnProperty.call(observed, rule.key)) reason = 'missing-observation';
      else if (op === 'finite') { passed = Number.isFinite(Number(value)); reason = 'finite-value-required'; }
      else if (op === 'between') { passed = Number(value) >= Number(rule.lower) && Number(value) <= Number(rule.upper); reason = 'outside-allowed-range'; }
      else if (op === 'gte') { passed = Number(value) >= Number(rule.lower); reason = 'below-minimum'; }
      else if (op === 'lte') { passed = Number(value) <= Number(rule.upper); reason = 'above-maximum'; }
      else if (op === 'equal') { const tolerance = number(rule.tolerance, 0); passed = typeof rule.expected === 'number' ? Math.abs(Number(value) - Number(rule.expected)) <= tolerance : value === rule.expected; reason = 'outside-equality-tolerance'; }
      else if (op === 'not_equal') { passed = value !== rule.expected; reason = 'unexpected-equality'; }
      counts[passed ? 'pass' : 'fail'] += 1; if (!passed && severity === 'critical') criticalFailures += 1;
      records.push({ key: rule.key, observed: value, operator: op, severity, status: passed ? 'pass' : 'fail', reason: passed ? 'within-checkpoint-rule' : reason });
    });
    return { ok: criticalFailures === 0, counts, criticalFailures, results: records };
  }

  async function analyzeAutomation(root, data) {
    const tasks = parseJSON(data.tasks, []), rules = parseJSON(data.rules, []), observed = parseJSON(data.observed, {}); if (!Array.isArray(tasks) || !tasks.length) throw new Error('Enter a valid task array.');
    const plan = graphPlan(tasks), checkpoint = evaluateRules(observed, rules), manifest = { title: data.title, objective: data.objective, tasks, rules, observed };
    result(root, { ok: !plan.findings.some((item) => item.severity === 'critical') && checkpoint.ok, schema: 'sc-workbench-experiment-automation/1.0', version: CONFIG.version, generatedAt: now(), title: data.title, objective: data.objective, taskCount: tasks.length, executionOrder: plan.order, estimatedCriticalPathMinutes: round(plan.duration), findings: plan.findings, checkpoint, automationHash: await sha256(manifest) }); status(root, 'Automation record generated');
  }
  async function analyzeProtocol(root, data) {
    const raw = parseJSON(data.steps, []); if (!Array.isArray(raw) || !raw.length) throw new Error('Enter a valid protocol-step array.');
    const steps = raw.map((step) => ({ id: String(step.id || ''), title: String(step.title || ''), procedure: String(step.procedure || ''), duration: number(step.duration, 0), dependencies: Array.isArray(step.dependencies) ? step.dependencies : [], outputs: Array.isArray(step.outputs) ? step.outputs : [], checkpoint: String(step.checkpoint || '') }));
    const plan = graphPlan(steps), findings = plan.findings.slice(); steps.forEach((step) => { if (!step.procedure) findings.push({ severity: 'warning', code: 'missing-procedure', step: step.id }); if (!step.outputs.length) findings.push({ severity: 'warning', code: 'missing-output-record', step: step.id }); if (!step.checkpoint) findings.push({ severity: 'warning', code: 'missing-checkpoint', step: step.id }); });
    const record = { ok: !findings.some((item) => item.severity === 'critical'), schema: 'sc-workbench-experiment-protocol/1.0', version: CONFIG.version, generatedAt: now(), title: data.title, objective: data.objective, stepCount: steps.length, topologicalOrder: plan.order, estimatedDurationMinutes: round(steps.reduce((sum, step) => sum + step.duration, 0)), materials: lines(data.materials), hazards: lines(data.hazards), steps, findings };
    record.protocolHash = await sha256(record); result(root, record); status(root, 'Protocol validated');
  }
  async function analyzeWorkflow(root, data) {
    const tasks = parseJSON(data.tasks, []); if (!Array.isArray(tasks) || !tasks.length) throw new Error('Enter a valid workflow task array.'); const plan = graphPlan(tasks), resourceMinutes = {};
    tasks.forEach((task) => { const resource = task.resource || 'unassigned'; resourceMinutes[resource] = (resourceMinutes[resource] || 0) + number(task.duration, 1); });
    const record = { ok: !plan.findings.some((item) => item.severity === 'critical'), schema: 'sc-workbench-reproducible-workflow/1.0', version: CONFIG.version, generatedAt: now(), title: data.title, taskCount: tasks.length, executionOrder: plan.order, estimatedCriticalPathMinutes: round(plan.duration), resourceMinutes, retryBudget: tasks.reduce((sum, task) => sum + number(task.retry, 0), 0), findings: plan.findings, tasks };
    record.workflowHash = await sha256(record); result(root, record); status(root, 'Workflow planned');
  }
  async function analyzeSchedule(root, data) {
    const tasks = parseJSON(data.schedule, []), windowMinutes = Math.max(1, number(data.window, 1440)); if (!Array.isArray(tasks) || !tasks.length) throw new Error('Enter a valid scheduled-task array.'); const intervals = [], findings = [];
    tasks.forEach((task) => { const occurrences = Math.max(1, number(task.occurrences, 1)), repeat = task.repeatEvery != null ? number(task.repeatEvery, 0) : null; for (let index = 0; index < occurrences; index += 1) { const start = number(task.start, 0) + (repeat ? index * repeat : 0), end = start + Math.max(1, number(task.duration, 1)), interval = { task: task.id, occurrence: index + 1, startMinute: start, endMinute: end, resource: task.resource || 'unassigned' }; intervals.push(interval); if (end > windowMinutes) findings.push({ severity: 'warning', code: 'outside-schedule-window', ...interval }); } });
    intervals.sort((a, b) => a.startMinute - b.startMinute || a.endMinute - b.endMinute); const grouped = {}; intervals.forEach((item) => { (grouped[item.resource] ||= []).push(item); }); Object.keys(grouped).forEach((resource) => { const values = grouped[resource]; for (let index = 1; index < values.length; index += 1) if (values[index].startMinute < values[index - 1].endMinute) findings.push({ severity: 'critical', code: 'resource-conflict', resource, first: values[index - 1], second: values[index] }); });
    result(root, { ok: !findings.some((item) => item.severity === 'critical'), schema: 'sc-workbench-experiment-schedule/1.0', version: CONFIG.version, generatedAt: now(), windowMinutes, occurrenceCount: intervals.length, intervals, findings, note: 'This browser plan does not install an operating-system scheduler or run unattended tasks by itself.' }); status(root, 'Schedule evaluated');
  }
  async function analyzeVersioning(root, data) {
    const dataset = parseJSON(data.dataset, null), configuration = parseJSON(data.configuration, null), environment = parseJSON(data.environment, {}), rules = parseJSON(data.rules, []), observed = parseJSON(data.observed, {}); if (dataset === null || configuration === null) throw new Error('Dataset and configuration must be valid JSON.');
    const manifest = { projectId: data.project_id, datasetHash: await sha256(dataset), configurationHash: await sha256(configuration), codeRevision: data.code_revision, environmentHash: await sha256(environment) }; manifest.manifestHash = await sha256(manifest); const checkpoint = evaluateRules(observed, rules);
    result(root, { ok: checkpoint.ok, schema: 'sc-workbench-version-checkpoint/1.0', version: CONFIG.version, generatedAt: now(), ...manifest, dataset, configuration, environment, checkpoint }); status(root, 'Version manifest created');
  }
  async function analyzeReproducibility(root, data) {
    const runIds = lines(data.run_ids), datasets = lines(data.dataset_hashes), configs = lines(data.configuration_hashes), revisions = lines(data.code_revisions), metrics = parseJSON(data.metrics, []), deviations = lines(data.deviations), count = runIds.length; if (count < 2 || [datasets.length, configs.length, revisions.length].some((length) => length !== count)) throw new Error('Provide matching run, dataset, configuration, and revision lists.');
    const metricRecords = metrics.map((metric) => { if (!Array.isArray(metric.values) || metric.values.length !== count) throw new Error('Each metric requires one value per run.'); const values = metric.values.map(Number), reference = values[0], absolute = values.map((value) => Math.abs(value - reference)), relative = absolute.map((value) => value / Math.max(Math.abs(reference), 1e-15)), meanValue = values.reduce((sum, value) => sum + value, 0) / values.length, variance = values.reduce((sum, value) => sum + Math.pow(value - meanValue, 2), 0) / values.length, passed = Math.max(...absolute) <= number(metric.absoluteTolerance, 0) || Math.max(...relative) <= number(metric.relativeTolerance, 0); return { key: metric.key, status: passed ? 'pass' : 'fail', mean: round(meanValue), standardDeviation: round(Math.sqrt(variance)), coefficientOfVariation: round(meanValue ? Math.sqrt(variance) / Math.abs(meanValue) : 0), maximumAbsoluteDelta: round(Math.max(...absolute)), maximumRelativeDelta: round(Math.max(...relative)), absoluteTolerance: number(metric.absoluteTolerance, 0), relativeTolerance: number(metric.relativeTolerance, 0) }; });
    const metadataConsistency = { sameDataset: new Set(datasets).size === 1, sameConfiguration: new Set(configs).size === 1, sameCodeRevision: new Set(revisions).size === 1 }, metricFailures = metricRecords.filter((item) => item.status === 'fail').length, record = { ok: Object.values(metadataConsistency).every(Boolean) && metricFailures === 0 && deviations.length === 0, schema: 'sc-workbench-reproducibility-comparison/1.0', version: CONFIG.version, generatedAt: now(), runCount: count, metadataConsistency, metricFailures, metrics: metricRecords, deviations };
    record.reproducibilityHash = await sha256({ runIds, datasets, configs, revisions, metrics, deviations }); result(root, record); status(root, 'Reproducibility compared');
  }

  async function analyze(root) { const data = fields(root), panel = root.dataset.scwbV280Panel; status(root, 'Evaluating…'); try { if (panel === 'automation') await analyzeAutomation(root, data); else if (panel === 'protocol') await analyzeProtocol(root, data); else if (panel === 'workflow') await analyzeWorkflow(root, data); else if (panel === 'scheduler') await analyzeSchedule(root, data); else if (panel === 'versioning') await analyzeVersioning(root, data); else await analyzeReproducibility(root, data); } catch (error) { status(root, 'Input needs review'); result(root, { ok: false, version: CONFIG.version, generatedAt: now(), error: error.message }); } }
  async function connect(root) { const data = fields(root), base = (data.runner_url || CONFIG.runnerDefaultUrl).replace(/\/$/, ''), code = String(data.pairing_code || '').trim(); status(root, 'Connecting…'); try { let token = localStorage.getItem(CONFIG.storagePrefix + 'runner-token'); if (code) { const response = await fetch(base + '/pair', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, origin: window.location.origin }) }), payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Pairing failed'); token = payload.token; localStorage.setItem(CONFIG.storagePrefix + 'runner-token', token); } if (!token) throw new Error('Enter the one-time pairing code shown by the local runner.'); const response = await fetch(base + '/experiment-tools', { headers: { Authorization: 'Bearer ' + token } }), payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Experiment-tool discovery failed'); status(root, 'Local runner paired'); result(root, payload); } catch (error) { status(root, 'Runner unavailable'); result(root, { ok: false, version: CONFIG.version, error: error.message, runnerUrl: base }); } }
  async function exportBundle(root) { if (!root._scwbV280Last) await analyze(root); const payload = { schema: 'sc-workbench-reproducible-experiment-bundle/1.0', version: CONFIG.version, exportedAt: now(), project: root.dataset.scwbV280Project, panel: root.dataset.scwbV280Panel, inputs: fields(root), record: root._scwbV280Last }; payload.bundleHash = await sha256(payload); download('workbench-v280-' + root.dataset.scwbV280Panel + '-bundle.json', JSON.stringify(payload, null, 2) + '\n', 'application/json'); }
  function initialize(root) { const saved = parseJSON(localStorage.getItem(storageKey(root)), null); if (saved && saved.fields) root.querySelectorAll('[data-scwb-v280-field]').forEach((node) => { if (Object.prototype.hasOwnProperty.call(saved.fields, node.dataset.scwbV280Field)) node.value = saved.fields[node.dataset.scwbV280Field]; }); root.addEventListener('click', async (event) => { const button = event.target.closest('[data-scwb-v280-action]'); if (!button) return; const action = button.dataset.scwbV280Action; if (action === 'analyze') await analyze(root); else if (action === 'connect') await connect(root); else if (action === 'save') { localStorage.setItem(storageKey(root), JSON.stringify({ version: CONFIG.version, savedAt: now(), fields: fields(root), result: root._scwbV280Last || null })); status(root, 'Saved in this browser'); } else if (action === 'export-json') download('workbench-v280-' + root.dataset.scwbV280Panel + '.json', JSON.stringify(root._scwbV280Last || { version: CONFIG.version, fields: fields(root) }, null, 2) + '\n', 'application/json'); else if (action === 'export-bundle') await exportBundle(root); }); }
  document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('[data-scwb-v280-panel]').forEach(initialize));
}());
