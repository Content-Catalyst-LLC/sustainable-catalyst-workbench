(function () {
  'use strict';
  var VERSION = '4.0.0';
  var SELECTOR = '[data-scwb-v400]';
  var STORE = 'scwb:v400:connected-records';
  var PLATFORMS = ['workbench','sustainable-catalyst-lab','site-intelligence','decision-studio','research-librarian','knowledge-library'];
  var CAPABILITIES = ['projects','calculations','code','simulation','devices','experiments','evidence','reviews','documentation','offline'];

  function stableString(value) {
    if (Array.isArray(value)) return '[' + value.map(stableString).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(function (key) { return JSON.stringify(key) + ':' + stableString(value[key]); }).join(',') + '}';
    return JSON.stringify(value);
  }

  function hash(value) {
    var text = stableString(value), h = 2166136261;
    for (var i = 0; i < text.length; i += 1) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
    return ('00000000' + (h >>> 0).toString(16)).slice(-8);
  }

  function readStore() {
    try { return JSON.parse(localStorage.getItem(STORE) || '[]'); }
    catch (error) { return []; }
  }
  function writeStore(records) { localStorage.setItem(STORE, JSON.stringify(records)); }
  function fields(root) {
    var result = {};
    root.querySelectorAll('[data-scwb-v400-field]').forEach(function (field) { result[field.getAttribute('data-scwb-v400-field')] = field.value; });
    return result;
  }
  function show(root, value) {
    var output = root.querySelector('[data-scwb-v400-output]');
    if (output) output.textContent = JSON.stringify(value, null, 2);
  }
  function save(record) {
    var records = readStore();
    records.push(record);
    writeStore(records.slice(-100));
  }
  function baseRecord(root, type) {
    var data = fields(root);
    var record = {
      schema: 'sc-workbench-connected-environment-' + type + '/1.0',
      version: VERSION,
      type: type,
      projectId: data.projectId || root.getAttribute('data-scwb-v400-project') || 'default',
      title: data.title || 'Connected Workbench Project',
      notes: data.notes || '',
      createdAt: new Date().toISOString(),
      humanControlRequired: true,
      automaticPublicationAuthorized: false,
      remoteShellAllowed: false
    };
    record.recordHash = hash(record);
    return record;
  }
  function build(root, action) {
    var record = baseRecord(root, action);
    if (action === 'project') {
      record.storageMode = 'browser-local';
      record.platforms = PLATFORMS.slice();
      record.capabilities = CAPABILITIES.slice();
      record.reviewState = 'draft';
    }
    if (action === 'registry') {
      record.platforms = PLATFORMS.slice();
      record.availableCapabilities = CAPABILITIES.slice();
      record.missingCapabilities = [];
      record.ready = true;
    }
    if (action === 'health') {
      record.integrations = PLATFORMS.map(function (id) { return { id: id, required: id === 'workbench', status: id === 'workbench' ? 'ready' : 'unverified' }; });
      record.offlineFallbackAvailable = true;
      record.ready = true;
      record.degraded = true;
    }
    if (action === 'graph') record.nodes = [{ id: record.projectId, type: 'project' }], record.edges = [];
    if (action === 'workflow') record.steps = [], record.automaticExecutionAuthorized = false;
    if (action === 'context') record.variables = [], record.assumptions = [], record.evidence = [], record.uncertainties = [];
    if (action === 'traceability') record.requirements = [], record.coveragePercent = 100, record.gaps = [];
    if (action === 'dossier') record.sections = ['project','graph','workflow','evidence','reviews','evaluations','artifacts'], record.certificationClaim = false;
    if (action === 'release') record.status = 'hold', record.blockingIssues = ['human-approval-required'], record.humanApproval = false;
    save(record);
    show(root, record);
    root.dispatchEvent(new CustomEvent('scwb:connected-record-built', { bubbles: true, detail: record }));
    return record;
  }
  function exportRecords(root) {
    var value = {
      schema: 'sc-workbench-connected-environment-export/1.0',
      version: VERSION,
      exportedAt: new Date().toISOString(),
      records: readStore(),
      automaticCloudUpload: false,
      requiresExplicitImport: true
    };
    show(root, value);
    var blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = 'sustainable-catalyst-workbench-connected-records.json';
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }
  function activate(root, key) {
    root.querySelectorAll('[data-scwb-v400-tab]').forEach(function (tab) {
      var active = tab.getAttribute('data-scwb-v400-tab') === key;
      tab.classList.toggle('is-active', active); tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    root.querySelectorAll('[data-scwb-v400-panel-view]').forEach(function (panel) {
      var active = panel.getAttribute('data-scwb-v400-panel-view') === key;
      panel.classList.toggle('is-active', active); panel.hidden = !active;
    });
  }
  function init(root) {
    if (!root || root.getAttribute('data-scwb-v400-ready') === 'true') return;
    root.setAttribute('data-scwb-v400-ready', 'true');
    var initial = root.getAttribute('data-scwb-v400-panel') || 'workspace';
    activate(root, initial);
    show(root, { ok: true, version: VERSION, milestone: 'Connected Scientific and Engineering Workbench', browserLocal: true, recordCount: readStore().length });
  }
  document.addEventListener('click', function (event) {
    var tab = event.target.closest('[data-scwb-v400-tab]');
    if (tab) { var root = tab.closest(SELECTOR); if (root) activate(root, tab.getAttribute('data-scwb-v400-tab')); return; }
    var button = event.target.closest('[data-scwb-v400-action]');
    if (!button) return;
    var owner = button.closest(SELECTOR); if (!owner) return;
    var action = button.getAttribute('data-scwb-v400-action');
    if (action === 'export') exportRecords(owner); else build(owner, action);
  });
  function start(scope) { (scope || document).querySelectorAll(SELECTOR).forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { start(document); }); else start(document);
  if ('MutationObserver' in window) new MutationObserver(function (items) { items.forEach(function (item) { item.addedNodes.forEach(function (node) { if (node && node.nodeType === 1) { if (node.matches && node.matches(SELECTOR)) init(node); if (node.querySelectorAll) start(node); } }); }); }).observe(document.documentElement, { childList: true, subtree: true });

  window.SCWBConnectedWorkbench = {
    version: VERSION,
    platforms: PLATFORMS.slice(),
    capabilities: CAPABILITIES.slice(),
    build: build,
    activate: activate,
    readStore: readStore,
    automaticPublicationAuthorized: false,
    automaticDeviceControlAuthorized: false,
    remoteShellAllowed: false
  };
}());
