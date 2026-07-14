(function () {
  'use strict';
  var VERSION = '4.0.2';
  var SELECTOR = '[data-scwb-v402]';
  var JOURNAL_KEY = 'scwb:v402:sync-journal:';

  function all(scope, selector) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }
  function hash(value) {
    var text = JSON.stringify(value, Object.keys(value || {}).sort());
    var result = 2166136261;
    for (var index = 0; index < text.length; index += 1) { result ^= text.charCodeAt(index); result = Math.imul(result, 16777619); }
    return ('00000000' + (result >>> 0).toString(16)).slice(-8);
  }
  function output(root, value) { var node = root.querySelector('[data-scwb-v402-output]'); if (node) node.textContent = JSON.stringify(value, null, 2); }
  function project(root) { return root.getAttribute('data-project') || 'default'; }
  function workbenchPanels() { return all(document, '[data-scwb-primary-panel]'); }
  function graphAudit() {
    var panels = workbenchPanels();
    var nodes = panels.map(function (panel) { return panel.getAttribute('data-scwb-primary-panel'); }).filter(Boolean);
    var duplicates = nodes.filter(function (item, index) { return nodes.indexOf(item) !== index; });
    return { schema: 'sc-workbench-project-graph-browser-audit/1.0', version: VERSION, nodeCount: nodes.length, duplicateNodeIds: duplicates, expectedStudioCount: 22, ready: nodes.length >= 22 && duplicates.length === 0, automaticMutationAuthorized: false };
  }
  function localRecords() {
    var records = [];
    try { for (var index = 0; index < localStorage.length; index += 1) { var key = localStorage.key(index); if (key && key.indexOf('scwb') === 0) records.push({ id: key, hash: hash(localStorage.getItem(key)) }); } } catch (error) { records.push({ id: 'storage-unavailable', error: error.message }); }
    return records;
  }
  function checkpoint(root) {
    var records = localRecords();
    var value = { schema: 'sc-workbench-recovery-checkpoint/1.0', version: VERSION, projectId: project(root), records: records, recordCount: records.length, graphHash: hash(graphAudit()), automaticRestoreAuthorized: false };
    value.checkpointHash = hash(value);
    return value;
  }
  function reconciliation(root) {
    var records = localRecords();
    return { schema: 'sc-workbench-sync-reconciliation-preview/1.0', version: VERSION, projectId: project(root), threeWayReconciliation: true, localRecordCount: records.length, baseRequiredForThreeWayMerge: true, strategies: ['manual','keep-local','keep-remote','newest','rename'], verifiedBackupRequiredBeforeOverwrite: true, automaticExecutionAuthorized: false, automaticDeletionAuthorized: false };
  }
  function journal(root) {
    var value = { schema: 'sc-workbench-sync-transaction-journal/1.0', version: VERSION, transactionId: 'txn-' + hash([project(root), Date.now()]), projectId: project(root), state: 'prepared', phases: ['prepared','applying','verifying','committed'], checkpointHash: checkpoint(root).checkpointHash, operations: [], resumeSupported: true, automaticCommitAuthorized: false };
    value.journalHash = hash(value);
    try { localStorage.setItem(JOURNAL_KEY + project(root), JSON.stringify(value)); } catch (error) { value.storageError = error.message; }
    return value;
  }
  function recovery(root) {
    var saved = null;
    try { saved = JSON.parse(localStorage.getItem(JOURNAL_KEY + project(root)) || 'null'); } catch (error) { saved = { parseError: error.message }; }
    return { schema: 'sc-workbench-interrupted-sync-recovery-plan/1.0', version: VERSION, projectId: project(root), journal: saved, actions: saved ? ['resume-idempotent-operations','re-run-receipt-verification'] : ['inspect-sync-history'], rollbackRequiresVerifiedBackup: true, rollbackConfirmation: 'ROLLBACK CONNECTED PROJECT', automaticRollbackAuthorized: false, automaticDeletionAuthorized: false };
  }
  function receipt() { return { schema: 'sc-workbench-sync-receipt-verification/1.0', version: VERSION, requiredFields: ['transactionId','journalHash','checkpointHash','state','operations'], acceptedStates: ['committed'], automaticAcceptanceAuthorized: false }; }
  function stress() { var panels = workbenchPanels().length; return { schema: 'sc-workbench-project-graph-sync-stress-report/1.0', version: VERSION, observedNodes: panels, budgets: { durationSeconds: 30, memoryMb: 512, conflictRatio: 0.05 }, humanReviewRequired: true }; }
  function execute(root, action) {
    var value = action === 'graph' ? graphAudit() : action === 'reconcile' ? reconciliation(root) : action === 'journal' ? journal(root) : action === 'checkpoint' ? checkpoint(root) : action === 'recovery' ? recovery(root) : action === 'receipt' ? receipt() : stress();
    output(root, value);
    root.dispatchEvent(new CustomEvent('scwb:graph-sync-check-complete', { bubbles: true, detail: { action: action, result: value } }));
    return value;
  }
  function init(root) { if (!root || root.getAttribute('data-scwb-v402-ready') === 'true') return; root.setAttribute('data-scwb-v402-ready', 'true'); root.setAttribute('data-scwb-v402-state', 'ready'); }
  function initAll(scope) { all(scope || document, SELECTOR).forEach(init); }
  document.addEventListener('click', function (event) { var button = event.target.closest('[data-scwb-v402-action]'); if (!button) return; var root = button.closest(SELECTOR); if (root) execute(root, button.getAttribute('data-scwb-v402-action')); });
  document.addEventListener('scwb:sync-failed', function (event) { try { var detail = event.detail || {}; localStorage.setItem(JOURNAL_KEY + (detail.projectId || 'default'), JSON.stringify(detail.journal || detail)); } catch (error) {} });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { initAll(document); }); else initAll(document);
  if ('MutationObserver' in window) new MutationObserver(function () { initAll(document); }).observe(document.documentElement, { childList: true, subtree: true });
  window.SCWBGraphSyncRecovery = { version: VERSION, graphAudit: graphAudit, checkpoint: checkpoint, reconciliation: reconciliation, journal: journal, recovery: recovery, receipt: receipt, stress: stress, automaticExecutionAuthorized: false, automaticRollbackAuthorized: false, automaticDeletionAuthorized: false };
}());
