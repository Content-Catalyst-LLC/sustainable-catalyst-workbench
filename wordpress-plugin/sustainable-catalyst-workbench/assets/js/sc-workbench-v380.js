(function () {
  'use strict';

  var VERSION = '3.8.0';
  var PREFIX = 'scwb:v380:';
  var PLATFORMS = {
    macos: { label: 'macOS', architectures: ['arm64', 'x86_64'] },
    linux: { label: 'Linux', architectures: ['x86_64', 'aarch64'] },
    'raspberry-pi': { label: 'Raspberry Pi OS', architectures: ['aarch64', 'armv7l'] }
  };
  var SCHEMAS = {
    install: 'sc-workbench-offline-install-plan/1.0',
    audit: 'sc-workbench-offline-runtime-audit/1.0',
    dependency: 'sc-workbench-offline-dependency-plan/1.0',
    sync: 'sc-workbench-offline-sync-bundle/1.0',
    update: 'sc-workbench-offline-update-plan/1.0',
    recovery: 'sc-workbench-offline-recovery-plan/1.0'
  };

  function stableStringify(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(stableStringify).join(',') + ']';
    return '{' + Object.keys(value).sort().map(function (key) {
      return JSON.stringify(key) + ':' + stableStringify(value[key]);
    }).join(',') + '}';
  }

  function simpleHash(value) {
    var source = stableStringify(value);
    var hash = 2166136261;
    for (var i = 0; i < source.length; i += 1) {
      hash ^= source.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return ('00000000' + (hash >>> 0).toString(16)).slice(-8);
  }

  function csv(value) {
    return String(value || '').split(',').map(function (item) { return item.trim(); }).filter(Boolean);
  }

  function parseJson(value, fallback) {
    try { return JSON.parse(value); } catch (error) { return fallback; }
  }

  function field(root, name) {
    var input = root.querySelector('[data-scwb-v380-field="' + name + '"]');
    return input ? input.value : '';
  }

  function platform(root) {
    var select = root.querySelector('[data-scwb-v380-platform-select]');
    return select ? select.value : root.getAttribute('data-scwb-v380-platform') || 'macos';
  }

  function show(root, value) {
    var output = root.querySelector('[data-scwb-v380-output]');
    if (output) output.textContent = JSON.stringify(value, null, 2);
    root.__scwbV380LastRecord = value;
  }

  function saveLocal(key, value) {
    try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); return true; }
    catch (error) { return false; }
  }

  function buildInstallPlan(root) {
    var target = platform(root);
    var record = {
      schema: SCHEMAS.install,
      version: VERSION,
      platform: target,
      architecture: field(root, 'architecture') || (target === 'macos' ? 'arm64' : 'x86_64'),
      installRoot: field(root, 'installRoot') || PLATFORMS[target].label + ' default',
      components: csv(field(root, 'components')),
      loopbackOnly: true,
      renderRequired: false,
      paidServiceRequired: false,
      launcherRequired: true
    };
    record.planHash = simpleHash(record);
    saveLocal('install-plan', record);
    return record;
  }

  function buildAudit(root) {
    var commands = csv(field(root, 'commands')).map(function (item) { return item.toLowerCase(); });
    var disk = Number(field(root, 'diskFreeMb') || 0);
    var memory = Number(field(root, 'memoryMb') || 0);
    var target = platform(root);
    var minimumMemory = target === 'raspberry-pi' ? 2048 : 4096;
    var record = {
      schema: SCHEMAS.audit,
      version: VERSION,
      platform: target,
      checks: {
        python: { ok: commands.indexOf('python3') !== -1, version: field(root, 'pythonVersion') },
        disk: { ok: disk >= 2048, observedMb: disk, minimumMb: 2048 },
        memory: { ok: memory >= minimumMemory, observedMb: memory, minimumMb: minimumMemory },
        loopback: { ok: true, host: '127.0.0.1' }
      },
      cloudDependency: false
    };
    record.ready = Object.keys(record.checks).every(function (key) { return record.checks[key].ok; });
    record.auditHash = simpleHash(record);
    saveLocal('runtime-audit', record);
    return record;
  }

  function buildRuntimePlan(root) {
    var requested = csv(field(root, 'languages'));
    var available = csv(field(root, 'runtimeCommands')).map(function (item) { return item.toLowerCase(); });
    var commandMap = { python: 'python3', javascript: 'node', go: 'go', r: 'rscript', rust: 'cargo' };
    var record = {
      schema: SCHEMAS.dependency,
      version: VERSION,
      platform: platform(root),
      runtimes: requested.map(function (language) {
        var command = commandMap[language] || '';
        return { language: language, command: command, available: command && available.indexOf(command) !== -1 };
      }),
      pythonPackages: ['fastapi', 'pydantic', 'uvicorn'],
      arbitraryPackageExecution: false
    };
    record.planHash = simpleHash(record);
    saveLocal('runtime-plan', record);
    return record;
  }

  function buildSyncBundle(root) {
    var records = parseJson(field(root, 'records'), []);
    if (!Array.isArray(records)) records = [];
    var recordItems = records.map(function (record, index) {
      return {
        recordId: String(record.id || record.recordId || 'record-' + (index + 1)),
        recordHash: simpleHash(record),
        record: record
      };
    });
    var bundle = {
      schema: SCHEMAS.sync,
      version: VERSION,
      projectId: field(root, 'projectId') || root.getAttribute('data-scwb-v380-project') || 'default',
      sourceNode: 'browser-local',
      target: 'portable',
      records: recordItems,
      recordCount: recordItems.length,
      attachments: [],
      requiresExplicitImport: true,
      automaticCloudUpload: false
    };
    bundle.bundleHash = simpleHash(bundle);
    saveLocal('sync-bundle', bundle);
    return bundle;
  }

  function buildUpdatePlan(root) {
    var record = {
      schema: SCHEMAS.update,
      version: VERSION,
      currentVersion: field(root, 'currentVersion') || VERSION,
      targetVersion: field(root, 'targetVersion') || VERSION,
      packageHash: field(root, 'packageHash'),
      backupRequired: true,
      automaticUpdateAuthorized: false,
      loopbackServiceMustStop: true
    };
    record.blockingIssues = [];
    if (!record.packageHash) record.blockingIssues.push('missing-package-hash');
    record.planHash = simpleHash(record);
    saveLocal('update-plan', record);
    return record;
  }

  function buildRecoveryPlan(root) {
    var record = {
      schema: SCHEMAS.recovery,
      version: VERSION,
      issue: field(root, 'issue') || 'Unknown local issue',
      steps: [
        'Stop the local service.',
        'Preserve the current project store.',
        'Verify the latest backup and package manifest.',
        'Repair application files without deleting project data.',
        'Restart on 127.0.0.1 and run the health check.'
      ],
      automaticDeletion: false,
      humanReviewRequired: true
    };
    record.planHash = simpleHash(record);
    saveLocal('recovery-plan', record);
    return record;
  }

  function download(root) {
    var record = root.__scwbV380LastRecord || buildSyncBundle(root);
    var blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' });
    var href = URL.createObjectURL(blob);
    var anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = 'workbench-v3.8.0-offline-record.json';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  }

  function activate(root) {
    if (!root || root.__scwbV380Active) return;
    root.__scwbV380Active = true;

    var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-scwb-v380-tab]'));
    var views = Array.prototype.slice.call(root.querySelectorAll('[data-scwb-v380-view]'));
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var key = tab.getAttribute('data-scwb-v380-tab');
        tabs.forEach(function (item) { item.classList.toggle('is-active', item === tab); });
        views.forEach(function (view) { view.hidden = view.getAttribute('data-scwb-v380-view') !== key; });
      });
    });

    root.addEventListener('click', function (event) {
      var button = event.target.closest ? event.target.closest('[data-scwb-v380-action]') : null;
      if (!button) return;
      var action = button.getAttribute('data-scwb-v380-action');
      var result;
      if (action === 'install') result = buildInstallPlan(root);
      else if (action === 'audit') result = buildAudit(root);
      else if (action === 'runtimes') result = buildRuntimePlan(root);
      else if (action === 'export') result = buildSyncBundle(root);
      else if (action === 'update') result = buildUpdatePlan(root);
      else if (action === 'recovery') result = buildRecoveryPlan(root);
      else if (action === 'service') {
        result = { schema: 'sc-workbench-offline-local-service/1.0', version: VERSION, host: '127.0.0.1', port: 8787, publicBind: false, remoteShell: false };
        saveLocal('service-record', result);
      } else if (action === 'backup') {
        result = { schema: 'sc-workbench-offline-backup-record/1.0', version: VERSION, projectId: root.getAttribute('data-scwb-v380-project'), createdAt: new Date().toISOString(), destructiveReset: false };
        result.backupHash = simpleHash(result);
        saveLocal('backup-record', result);
      } else if (action === 'download') {
        download(root);
        return;
      }
      show(root, result || {});
    });
  }

  function scan(scope) {
    var target = scope && scope.querySelectorAll ? scope : document;
    Array.prototype.forEach.call(target.querySelectorAll('[data-scwb-v380]'), activate);
  }

  window.SCWBOfflineInstallable = {
    version: VERSION,
    schemas: SCHEMAS,
    platforms: Object.keys(PLATFORMS),
    localServiceHost: '127.0.0.1',
    localServicePort: 8787,
    renderRequired: false,
    paidServiceRequired: false,
    remoteShell: false,
    automaticCloudUpload: false,
    stableStringify: stableStringify,
    simpleHash: simpleHash,
    buildInstallPlan: buildInstallPlan,
    buildAudit: buildAudit,
    buildRuntimePlan: buildRuntimePlan,
    buildSyncBundle: buildSyncBundle,
    buildUpdatePlan: buildUpdatePlan,
    buildRecoveryPlan: buildRecoveryPlan,
    scan: scan
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(document); });
  else scan(document);

  if (window.MutationObserver && document.body) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        Array.prototype.forEach.call(mutation.addedNodes || [], function (node) {
          if (node && node.nodeType === 1) {
            if (node.matches && node.matches('[data-scwb-v380]')) activate(node);
            scan(node);
          }
        });
      });
    }).observe(document.body, { childList: true, subtree: true });
  }
}());
