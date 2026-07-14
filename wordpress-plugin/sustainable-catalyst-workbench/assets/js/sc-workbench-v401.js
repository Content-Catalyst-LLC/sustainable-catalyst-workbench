(function () {
  'use strict';
  var VERSION = '4.0.1';
  var SELECTOR = '[data-scwb-v401]';
  var EXPECTED = 22;

  function all(scope, selector) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }
  function output(root, value) {
    var node = root.querySelector('[data-scwb-v401-output]');
    if (node) node.textContent = JSON.stringify(value, null, 2);
  }
  function moduleState(panel) {
    if (!panel) return 'missing';
    if (panel.querySelector('.scwb-primary__module-error,[data-scwb-error]')) return 'error';
    var mount = panel.querySelector('[data-scwb-module-mount]');
    if (!mount) return 'empty';
    var literal = (mount.textContent || '').match(/\[sc_workbench_[a-z0-9_]+[^\]]*\]/ig);
    if (literal && literal.length) return 'literal-shortcode';
    return 'ready';
  }
  function activationAudit(root) {
    var primary = root.closest('[data-scwb-primary]') || document.querySelector('[data-scwb-primary]');
    var panels = primary ? all(primary, '[data-scwb-primary-panel]') : [];
    var report = panels.map(function (panel) {
      return { studio: panel.getAttribute('data-scwb-primary-panel'), state: moduleState(panel) };
    });
    var failures = report.filter(function (item) { return item.state !== 'ready'; });
    return {
      schema: 'sc-workbench-connected-reliability-browser-audit/1.0',
      version: VERSION,
      expectedStudios: EXPECTED,
      observedStudios: report.length,
      failures: failures,
      ready: report.length >= EXPECTED && failures.length === 0,
      automaticRepairAuthorized: false
    };
  }
  function schemaReport() {
    return {
      schema: 'sc-workbench-connected-reliability-browser-schema-report/1.0',
      version: VERSION,
      supportedSchemas: [
        'sc-workbench-connected-environment-project/1.0',
        'sc-workbench-persistent-project/1.0',
        'sc-workbench-platform-handoff/1.0',
        'sc-workbench-domain-laboratory-contract/1.0',
        'sc-workbench-offline-sync-bundle/1.0'
      ],
      destructiveMigrationAuthorized: false
    };
  }
  function projectPropagation(root) {
    var projectId = root.getAttribute('data-project') || 'default';
    var primary = root.closest('[data-scwb-primary]') || document.querySelector('[data-scwb-primary]');
    if (primary) {
      primary.setAttribute('data-scwb-project', projectId);
      primary.dispatchEvent(new CustomEvent('scwb:active-project-updated', { bubbles: true, detail: { projectId: projectId, source: 'v4.0.1-reliability' } }));
    }
    document.dispatchEvent(new CustomEvent('scwb:project-changed', { bubbles: true, detail: { projectId: projectId, source: 'v4.0.1-reliability' } }));
    return { schema: 'sc-workbench-connected-reliability-project-propagation/1.0', version: VERSION, projectId: projectId, eventDispatched: true, automaticOverwriteAuthorized: false };
  }
  function handoffReport() {
    return { schema: 'sc-workbench-connected-reliability-handoff-check/1.0', version: VERSION, checks: ['required-fields','packet-hash','target-receipt','project-link'], humanReviewRequired: true };
  }
  function assetAudit() {
    var scripts = all(document, 'script[src*="sc-workbench"],link[href*="sc-workbench"]');
    var shortcodes = (document.body && document.body.textContent || '').match(/\[sc_workbench_[a-z0-9_]+[^\]]*\]/ig) || [];
    return { schema: 'sc-workbench-connected-reliability-asset-audit/1.0', version: VERSION, workbenchAssets: scripts.length, literalShortcodes: shortcodes.slice(0, 20), cacheBustStrategy: 'filemtime', ready: shortcodes.length === 0 };
  }
  function fallbackPlan() {
    return { schema: 'sc-workbench-connected-reliability-fallback-plan/1.0', version: VERSION, order: ['wordpress-private','browser-local','offline-fastapi'], backupRequiredBeforeDestructiveRepair: true, automaticDeletionAuthorized: false, automaticRepairAuthorized: false };
  }
  function execute(root, action) {
    var value = action === 'activation' ? activationAudit(root)
      : action === 'schemas' ? schemaReport()
      : action === 'projects' ? projectPropagation(root)
      : action === 'handoffs' ? handoffReport()
      : action === 'assets' ? assetAudit()
      : fallbackPlan();
    output(root, value);
    root.dispatchEvent(new CustomEvent('scwb:reliability-check-complete', { bubbles: true, detail: { action: action, result: value } }));
    return value;
  }
  function init(root) {
    if (!root || root.getAttribute('data-scwb-v401-ready') === 'true') return;
    root.setAttribute('data-scwb-v401-ready', 'true');
    root.setAttribute('data-scwb-v401-state', 'ready');
  }
  function initAll(scope) { all(scope || document, SELECTOR).forEach(init); }
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-scwb-v401-action]');
    if (!button) return;
    var root = button.closest(SELECTOR);
    if (!root) return;
    execute(root, button.getAttribute('data-scwb-v401-action'));
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { initAll(document); });
  else initAll(document);
  if ('MutationObserver' in window) new MutationObserver(function () { initAll(document); }).observe(document.documentElement, { childList: true, subtree: true });
  window.SCWBConnectedReliability = {
    version: VERSION,
    expectedStudios: EXPECTED,
    activationAudit: activationAudit,
    schemaReport: schemaReport,
    projectPropagation: projectPropagation,
    handoffReport: handoffReport,
    assetAudit: assetAudit,
    fallbackPlan: fallbackPlan,
    automaticRepairAuthorized: false,
    automaticDeletionAuthorized: false
  };
}());
