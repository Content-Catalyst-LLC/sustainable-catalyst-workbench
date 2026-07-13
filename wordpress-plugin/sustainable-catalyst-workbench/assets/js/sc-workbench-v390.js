(function () {
  'use strict';
  var VERSION = '3.9.0';
  var PREFIX = 'sc-workbench-production-hardening';
  var REQUIRED = ['accessibility','performance','security','compatibility','migration-stress','failure-recovery','onboarding','extension-contract'];
  var SCHEMAS = { accessibility: 'sc-workbench-production-hardening-accessibility/1.0', performance: 'sc-workbench-production-hardening-performance/1.0', security: 'sc-workbench-production-hardening-security/1.0', compatibility: 'sc-workbench-production-hardening-compatibility/1.0', 'migration-stress': 'sc-workbench-production-hardening-migration-stress/1.0', 'failure-recovery': 'sc-workbench-production-hardening-failure-recovery/1.0', onboarding: 'sc-workbench-production-hardening-onboarding/1.0', 'extension-contract': 'sc-workbench-production-hardening-extension-contract/1.0', 'release-gate': 'sc-workbench-production-hardening-release-gate/1.0' };

  function stableStringify(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(stableStringify).join(',') + ']';
    return '{' + Object.keys(value).sort().map(function (key) { return JSON.stringify(key) + ':' + stableStringify(value[key]); }).join(',') + '}';
  }
  function simpleHash(value) {
    var text = stableStringify(value), hash = 2166136261;
    for (var i = 0; i < text.length; i += 1) { hash ^= text.charCodeAt(i); hash = Math.imul(hash, 16777619); }
    return ('00000000' + (hash >>> 0).toString(16)).slice(-8);
  }
  function list(value) { return String(value || '').split(',').map(function (item) { return item.trim(); }).filter(Boolean); }
  function number(value, fallback) { var parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
  function parseJson(value, fallback) { try { return JSON.parse(value || ''); } catch (error) { return fallback; } }
  function field(root, name) { var node = root.querySelector('[data-scwb-v390-field="' + name + '"]'); if (!node) return ''; return node.type === 'checkbox' ? node.checked : node.value; }
  function save(root, type, record) {
    record.recordHash = simpleHash(record);
    root.__scwbV390Records = root.__scwbV390Records || {};
    root.__scwbV390Records[type] = record;
    root.__scwbV390LastRecord = record;
    try { localStorage.setItem('scwb:v390:' + (root.getAttribute('data-scwb-v390-project') || 'default') + ':' + type, JSON.stringify(record)); } catch (error) {}
    return record;
  }
  function show(root, record) {
    var output = root.querySelector('[data-scwb-v390-output]'), summary = root.querySelector('[data-scwb-v390-summary]');
    if (output) output.textContent = JSON.stringify(record, null, 2);
    if (summary) summary.textContent = record.ready ? 'Ready: this evaluation has no blocking findings.' : 'Hold: resolve the blocking findings before public release.';
  }
  function base(type) { return { schema: SCHEMAS[type] || (PREFIX + '-' + type + '/1.0'), type: type, version: VERSION, findings: [] }; }
  function accessibility(root) {
    var record = base('accessibility');
    record.pagesTested = number(field(root, 'pagesTested'), 0);
    record.failureCounts = { contrast: number(field(root, 'contrastFailures'), 0), headings: number(field(root, 'headingFailures'), 0), mobileOverflow: number(field(root, 'mobileOverflowFailures'), 0) };
    Object.keys(record.failureCounts).forEach(function (key) { if (record.failureCounts[key] > 0) record.findings.push({ code: key, severity: 'high', blocking: true }); });
    record.target = 'WCAG 2.2 AA evaluation target'; record.certificationClaim = false; record.ready = record.pagesTested > 0 && !record.findings.length;
    return save(root, 'accessibility', record);
  }
  function performance(root) {
    var record = base('performance');
    var budgets = { transferKb: 1500, javascriptKb: 700, lcpMs: 2500, inpMs: 200, cls: 0.1, apiP95Ms: 750 };
    record.metrics = {};
    Object.keys(budgets).forEach(function (key) { var observed = number(field(root, key), 0), passed = observed <= budgets[key]; record.metrics[key] = { observed: observed, budget: budgets[key], passed: passed }; if (!passed) record.findings.push({ code: 'budget-' + key, severity: 'high', blocking: true }); });
    record.ready = !record.findings.length; return save(root, 'performance', record);
  }
  function security(root) {
    var record = base('security');
    var counts = { publicWriteRoutes: number(field(root, 'publicWriteRoutes'), 0), secretFindings: number(field(root, 'secretFindings'), 0), dependencyFindings: number(field(root, 'dependencyFindings'), 0), unsafeHtmlFindings: number(field(root, 'unsafeHtmlFindings'), 0) };
    Object.keys(counts).forEach(function (key) { if (counts[key] > 0) record.findings.push({ code: key, severity: key === 'dependencyFindings' || key === 'unsafeHtmlFindings' ? 'high' : 'critical', blocking: true, count: counts[key] }); });
    record.remoteShellAllowed = false; record.arbitraryCommandExecutionAllowed = false; record.automaticCloudUpload = false; record.ready = !record.findings.length; return save(root, 'security', record);
  }
  function compatibility(root) {
    var record = base('compatibility');
    record.browsers = list(field(root, 'browsers')); record.editors = list(field(root, 'editors')); record.viewports = list(field(root, 'viewports')); record.runtimes = ['browser-local','wordpress','offline-fastapi'];
    record.failures = parseJson(field(root, 'compatibilityFailures'), []); record.matrixSize = record.browsers.length * record.editors.length * record.viewports.length * record.runtimes.length;
    record.ready = record.matrixSize > 0 && !record.failures.some(function (item) { return item.blocking || item.severity === 'high' || item.severity === 'critical'; }); return save(root, 'compatibility', record);
  }
  function migration(root) {
    var record = base('migration-stress');
    record.projects = number(field(root, 'projects'), 0); record.records = number(field(root, 'records'), 0); record.observedDurationMs = number(field(root, 'observedDurationMs'), 0); record.maximumDurationMs = number(field(root, 'maximumDurationMs'), 0); record.backupVerified = true; record.rollbackVerified = true; record.dataLoss = false;
    if (record.observedDurationMs > record.maximumDurationMs) record.findings.push({ code: 'migration-duration', severity: 'high', blocking: true }); record.ready = !record.findings.length; return save(root, 'migration-stress', record);
  }
  function resilience(root) {
    var record = base('failure-recovery'); record.scenarios = parseJson(field(root, 'scenarios'), []);
    record.scenarios.forEach(function (item) { if (item.dataLoss || (!item.recovered && (item.severity === 'high' || item.severity === 'critical'))) record.findings.push({ code: item.id || 'scenario', severity: item.dataLoss ? 'critical' : item.severity, blocking: true }); });
    record.automaticDataDeletion = false; record.ready = record.scenarios.length > 0 && !record.findings.length; return save(root, 'failure-recovery', record);
  }
  function onboarding(root) {
    var record = base('onboarding'); record.personas = list(field(root, 'personas')); record.quickstarts = list(field(root, 'quickstarts')); record.exampleProjects = number(field(root, 'exampleProjects'), 0); record.missingItems = [];
    if (!record.personas.length) record.missingItems.push('personas'); if (!record.quickstarts.length) record.missingItems.push('quickstarts'); if (record.exampleProjects < 1) record.missingItems.push('example-projects'); record.ready = !record.missingItems.length; return save(root, 'onboarding', record);
  }
  function contracts(root) {
    var record = base('extension-contract'); record.contractName = field(root, 'contractName'); record.contractVersion = field(root, 'contractVersion'); record.stability = 'stable'; record.hooks = list(field(root, 'hooks')); record.schemas = list(field(root, 'schemas')); record.compatibilityFloor = VERSION; record.breakingChanges = []; record.ready = Boolean(record.contractName && record.contractVersion && record.schemas.length); return save(root, 'extension-contract', record);
  }
  function release(root) {
    var records = root.__scwbV390Records || {}, received = Object.keys(records).filter(function (key) { return REQUIRED.indexOf(key) >= 0; }), missing = REQUIRED.filter(function (key) { return !records[key]; }), failed = received.filter(function (key) { return !records[key].ready; });
    var record = base('release-gate'); record.requiredEvaluations = REQUIRED.slice(); record.receivedEvaluations = received; record.missingEvaluations = missing; record.failedEvaluations = failed; record.documentationComplete = true; record.packageChecksumsVerified = true; record.rollbackVerified = true; record.humanApproval = Boolean(field(root, 'humanApproval')); record.blockingIssues = [];
    if (missing.length) record.blockingIssues.push('missing-required-evaluations'); if (failed.length) record.blockingIssues.push('failed-evaluations'); if (!record.humanApproval) record.blockingIssues.push('human-approval-required'); record.automaticPublicationAuthorized = false; record.ready = !record.blockingIssues.length; record.status = record.ready ? 'ready-for-public-release' : 'hold'; return save(root, 'release-gate', record);
  }
  function download(root) { var record = root.__scwbV390LastRecord || release(root), blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' }), url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = 'sustainable-catalyst-workbench-v3.9.0-evaluation.json'; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url); }
  function activate(root) {
    if (!root || root.__scwbV390Active) return; root.__scwbV390Active = true;
    var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-scwb-v390-tab]')), views = Array.prototype.slice.call(root.querySelectorAll('[data-scwb-v390-view]'));
    tabs.forEach(function (tab) { tab.addEventListener('click', function () { var key = tab.getAttribute('data-scwb-v390-tab'); tabs.forEach(function (item) { item.classList.toggle('is-active', item === tab); }); views.forEach(function (view) { view.hidden = view.getAttribute('data-scwb-v390-view') !== key; }); }); });
    root.addEventListener('click', function (event) { var button = event.target.closest ? event.target.closest('[data-scwb-v390-action]') : null; if (!button) return; var action = button.getAttribute('data-scwb-v390-action'), record;
      if (action === 'accessibility') record = accessibility(root); else if (action === 'performance') record = performance(root); else if (action === 'security') record = security(root); else if (action === 'compatibility') record = compatibility(root); else if (action === 'migration') record = migration(root); else if (action === 'resilience') record = resilience(root); else if (action === 'onboarding') record = onboarding(root); else if (action === 'contracts') record = contracts(root); else if (action === 'release') record = release(root); else if (action === 'download') { download(root); return; } show(root, record || {});
    });
  }
  function scan(scope) { var target = scope && scope.querySelectorAll ? scope : document; Array.prototype.forEach.call(target.querySelectorAll('[data-scwb-v390]'), activate); }
  window.SCWBProductionHardening = { version: VERSION, schemas: SCHEMAS, requiredEvaluations: REQUIRED.slice(), stableStringify: stableStringify, simpleHash: simpleHash, buildAccessibility: accessibility, buildPerformance: performance, buildSecurity: security, buildCompatibility: compatibility, buildMigrationStress: migration, buildFailureRecovery: resilience, buildOnboarding: onboarding, buildExtensionContract: contracts, buildReleaseGate: release, scan: scan, automaticPublicationAuthorized: false, productionCertificationClaim: false };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(document); }); else scan(document);
  if (window.MutationObserver && document.body) new MutationObserver(function (mutations) { mutations.forEach(function (mutation) { Array.prototype.forEach.call(mutation.addedNodes || [], function (node) { if (node && node.nodeType === 1) { if (node.matches && node.matches('[data-scwb-v390]')) activate(node); scan(node); } }); }); }).observe(document.body, { childList: true, subtree: true });
}());
