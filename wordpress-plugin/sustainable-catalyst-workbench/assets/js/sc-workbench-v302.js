(function () {
  'use strict';
  var VERSION = '3.0.2';
  var CANONICAL_PREFIX = 'scwb:v3';
  var WORKBENCH_PREFIXES = ['scwb-', 'scwb:', 'sc-workbench', 'sustainable-catalyst-workbench'];

  function all(root, selector) { return Array.prototype.slice.call(root.querySelectorAll(selector)); }
  function one(root, selector) { return root.querySelector(selector); }
  function field(root, name) {
    var node = one(root, '[data-scwb-v302-field="' + name + '"]');
    if (!node) return '';
    if (node.type === 'checkbox') return !!node.checked;
    return node.value || '';
  }
  function lines(value) { return String(value || '').split(/\r?\n/).map(function (item) { return item.trim(); }).filter(Boolean); }
  function byteSize(value) { return new Blob([String(value == null ? '' : value)]).size; }
  function safeParse(value) { try { return JSON.parse(value); } catch (error) { return value; } }
  function canonical(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    return '{' + Object.keys(value).sort().map(function (key) { return JSON.stringify(key) + ':' + canonical(value[key]); }).join(',') + '}';
  }
  async function sha256(value) {
    var bytes = new TextEncoder().encode(canonical(value));
    var digest = await crypto.subtle.digest('SHA-256', bytes);
    return Array.prototype.map.call(new Uint8Array(digest), function (item) { return item.toString(16).padStart(2, '0'); }).join('');
  }
  function slug(value) { return String(value || 'record').trim().toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 160) || 'record'; }
  function isWorkbenchKey(key) { return WORKBENCH_PREFIXES.some(function (prefix) { return String(key).toLowerCase().startsWith(prefix); }); }
  function classify(key) {
    var lower = String(key).toLowerCase();
    if (lower.startsWith(CANONICAL_PREFIX + ':')) return { source: 'canonical', studio: key.split(':')[3] || 'unified' };
    var map = [
      ['scwb-v200','research'],['scwb-v210','embedded'],['scwb-v220','electronics'],['scwb-v230','robotics'],
      ['scwb-v240','instrumentation'],['scwb-v250','simulation'],['scwb-v260','runtime'],['scwb-v270','visualization'],
      ['scwb-v280','experiments'],['scwb-v290','documentation'],['scwb-v300','unified'],['scwb-v301','unified'],
      ['sc-workbench','legacy'],['sustainable-catalyst-workbench','legacy']
    ];
    for (var i = 0; i < map.length; i += 1) if (lower.startsWith(map[i][0])) return { source: map[i][0], studio: map[i][1] };
    return { source: 'unknown', studio: 'other' };
  }
  async function records() {
    var output = [];
    for (var index = 0; index < localStorage.length; index += 1) {
      var key = localStorage.key(index);
      if (!key || !isWorkbenchKey(key)) continue;
      var raw = localStorage.getItem(key);
      var parsed = safeParse(raw);
      output.push({
        key: key,
        value: parsed,
        size_bytes: byteSize(raw),
        content_hash: await sha256(parsed),
        updated_at: parsed && typeof parsed === 'object' ? (parsed.updatedAt || parsed.updated_at || '') : '',
        protected: /project|backup|manifest|settings/i.test(key),
        dependencies: parsed && typeof parsed === 'object' && Array.isArray(parsed.dependencies) ? parsed.dependencies : [],
        category: classify(key).studio
      });
    }
    return output.sort(function (a, b) { return a.key.localeCompare(b.key); });
  }
  function download(name, value) {
    var blob = new Blob([typeof value === 'string' ? value : JSON.stringify(value, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url; link.download = name; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }
  function render(root, result) {
    root.__scwbV302Result = result;
    one(root, '[data-scwb-v302-result]').textContent = JSON.stringify(result, null, 2);
    var summary = one(root, '[data-scwb-v302-summary]');
    summary.innerHTML = '<strong>' + (result.ok ? 'PASS' : 'REVIEW') + '</strong><span>' + (result.schema || 'record') + ' · Workbench ' + (result.version || VERSION) + '</span>';
    one(root, '[data-scwb-v302-status]').textContent = result.ok ? 'Recovery record validated' : 'Review required';
  }
  function targetKey(project, studio, source, index) { return CANONICAL_PREFIX + ':' + slug(project) + ':' + slug(studio) + ':' + slug(String(source).split(':').pop() || index); }
  async function migrationPreview(root, current) {
    var project = field(root, 'target_project') || root.dataset.scwbV302Project || 'default';
    var preserveUnknown = field(root, 'preserve_unknown') !== false;
    var mappings = [], targets = {}, unknown = [], studios = {};
    current.forEach(function (record, index) {
      var family = classify(record.key), target, action;
      if (family.source === 'canonical') { target = record.key; action = 'keep'; }
      else if (family.source === 'unknown') { unknown.push(record.key); target = targetKey(project, record.category || 'legacy', record.key, index); action = preserveUnknown ? 'preserve' : 'skip'; }
      else { target = targetKey(project, family.studio, record.key, index); action = 'migrate'; }
      targets[target] = (targets[target] || 0) + 1;
      studios[family.studio] = (studios[family.studio] || 0) + 1;
      mappings.push({ sourceKey: record.key, targetKey: target, sourceFamily: family.source, studioId: family.studio, action: action, sizeBytes: record.size_bytes, protected: record.protected, contentHash: record.content_hash });
    });
    var collisions = Object.keys(targets).filter(function (key) { return targets[key] > 1; });
    var manifest = { project_id: project, title: 'Migrated Workbench project: ' + project, revision: VERSION, owner: '', studios: Object.keys(studios).sort().map(function (studio) { return { id: studio, label: studio.replace(/-/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); }), version: VERSION, status: 'active', record_count: studios[studio], evidence_ids: [], warnings: [] }; }), artifacts: [], evidence_ids: [], assumptions: [], limitations: ['Migrated records require studio-level validation before consequential reuse.'], metadata: { sourceVersion: field(root, 'source_version') || 'auto-detect', migrationSchema: 'sc-workbench-migration-plan/2.0', legacyRecordCount: current.length } };
    return { ok: current.length > 0 && !collisions.length, schema: 'sc-workbench-migration-plan/2.0', version: VERSION, generatedAt: new Date().toISOString(), projectId: project, recordCount: current.length, targetCollisions: collisions, unknownKeys: unknown, mappings: mappings, projectManifest: manifest, backupRequired: true, destructiveActions: false, executionAllowed: current.length > 0 && !collisions.length, planHash: await sha256({ projectId: project, mappings: mappings, manifest: manifest }) };
  }
  async function audit(current, quota) {
    var counts = {}, known = new Set(current.map(function (r) { return r.key; })), duplicate = [], orphan = {}, invalid = [], categories = {}, total = 0;
    current.forEach(function (record) { counts[record.key] = (counts[record.key] || 0) + 1; total += record.size_bytes || 0; categories[record.category] = (categories[record.category] || 0) + 1; var missing = (record.dependencies || []).filter(function (key) { return !known.has(key); }); if (missing.length) orphan[record.key] = missing; if (typeof record.value === 'string' && /^[\[{]/.test(record.value.trim())) { try { JSON.parse(record.value); } catch (e) { invalid.push(record.key); } } });
    duplicate = Object.keys(counts).filter(function (key) { return counts[key] > 1; });
    var orphanKeys = Object.keys(orphan), quotaPercent = total / quota * 100, candidates = Array.from(new Set(duplicate.concat(orphanKeys, invalid))).sort();
    return { ok: !duplicate.length && !orphanKeys.length && quotaPercent < 90, schema: 'sc-workbench-storage-health/2.0', version: VERSION, generatedAt: new Date().toISOString(), recordCount: current.length, totalBytes: total, quotaBytes: quota, quotaPercent: +quotaPercent.toFixed(4), categoryCounts: categories, duplicateKeys: duplicate, orphanDependencies: orphan, orphanKeys: orphanKeys, invalidJsonRecords: invalid, cleanupCandidates: candidates, backupRecommended: candidates.length > 0 || quotaPercent > 75, workspaceHash: await sha256(current) };
  }
  async function backup(root, current, downloadFile) {
    var ordered = current.slice().sort(function (a,b) { return a.key.localeCompare(b.key); });
    var envelope = { schema: 'sc-workbench-backup/2.0', version: VERSION, projectId: root.dataset.scwbV302Project || 'default', revision: VERSION, label: field(root, 'backup_label') || 'Workbench recovery backup', generatedAt: new Date().toISOString(), previousBackupHash: field(root, 'previous_backup_hash') || '', records: ordered, recordCount: ordered.length, totalBytes: ordered.reduce(function (sum, record) { return sum + (record.size_bytes || 0); }, 0), recordsHash: await sha256(ordered) };
    envelope.backupHash = await sha256(envelope);
    var result = { ok: ordered.length > 0, schema: envelope.schema, version: VERSION, backup: envelope, backupHash: envelope.backupHash, recordCount: ordered.length, totalBytes: envelope.totalBytes, downloadRequired: true };
    root.__scwbV302Backup = envelope;
    if (downloadFile && ordered.length) download('workbench-' + slug(envelope.projectId) + '-backup-' + envelope.backupHash.slice(0, 12) + '.json', envelope);
    return result;
  }
  async function validateBackup(envelope) {
    if (!envelope || envelope.schema !== 'sc-workbench-backup/2.0' || !Array.isArray(envelope.records)) return { valid: false, warnings: ['Unsupported or malformed backup.'] };
    var copy = Object.assign({}, envelope), claimed = copy.backupHash || ''; delete copy.backupHash;
    var calculated = await sha256(copy), recordsHash = await sha256(envelope.records), warnings = [];
    if (claimed !== calculated) warnings.push('Backup envelope hash mismatch.');
    if (envelope.recordsHash !== recordsHash) warnings.push('Backup record hash mismatch.');
    if (envelope.recordCount !== envelope.records.length) warnings.push('Backup record count mismatch.');
    return { valid: warnings.length === 0, warnings: warnings, calculatedBackupHash: calculated, calculatedRecordsHash: recordsHash };
  }
  async function restorePlan(root, envelope, current) {
    var validation = await validateBackup(envelope), strategy = String(field(root, 'restore_strategy') || 'skip').toLowerCase(), existing = new Set(current.map(function (r) { return r.key; })), conflicts = [], operations = [];
    envelope.records.forEach(function (record) { var conflict = existing.has(record.key); if (conflict) conflicts.push(record.key); var action = conflict ? strategy : 'create', target = record.key; if (action === 'rename') target = record.key + ':restored-' + String(envelope.backupHash || 'backup').slice(0, 12); operations.push({ action: action, sourceKey: record.key, targetKey: target }); });
    var backupConfirmed = field(root, 'backup_before_restore') !== false, allowed = validation.valid && envelope.records.length > 0 && (backupConfirmed || !conflicts.length);
    return { ok: allowed, schema: 'sc-workbench-restore-plan/2.0', version: VERSION, generatedAt: new Date().toISOString(), strategy: strategy, backupValid: validation.valid, backupValidation: validation, conflictKeys: conflicts, operations: operations, rollbackBackupRequired: conflicts.length > 0, rollbackBackupConfirmed: backupConfirmed, executionAllowed: allowed, restorePlanHash: await sha256({ backupHash: envelope.backupHash, strategy: strategy, operations: operations }), warnings: validation.warnings.concat(conflicts.length && !backupConfirmed ? ['Create a rollback backup before restoring conflicting keys.'] : []) };
  }
  async function readFile(root) {
    var input = one(root, '[data-scwb-v302-file]');
    if (!input || !input.files || !input.files[0]) throw new Error('Choose a Workbench JSON backup file first.');
    return JSON.parse(await input.files[0].text());
  }
  async function applyRestore(root, envelope, plan) {
    if (!plan.executionAllowed) throw new Error('Restore plan is not approved.');
    if (field(root, 'backup_before_restore') !== false) await backup(root, await records(), true);
    var map = new Map(envelope.records.map(function (record) { return [record.key, record]; }));
    plan.operations.forEach(function (operation) { if (operation.action === 'skip') return; var record = map.get(operation.sourceKey); localStorage.setItem(operation.targetKey, JSON.stringify(record.value)); });
    return { ok: true, schema: 'sc-workbench-restore-execution/2.0', version: VERSION, generatedAt: new Date().toISOString(), appliedCount: plan.operations.filter(function (op) { return op.action !== 'skip'; }).length, skippedCount: plan.operations.filter(function (op) { return op.action === 'skip'; }).length, finalRecordCount: (await records()).length };
  }
  async function cleanupPlan(root, current, health) {
    var scope = String(field(root, 'cleanup_scope') || 'selected'), selected;
    if (scope === 'duplicates') selected = health.duplicateKeys || [];
    else if (scope === 'orphans') selected = health.orphanKeys || [];
    else if (scope === 'all-candidates') selected = health.cleanupCandidates || [];
    else selected = lines(field(root, 'cleanup_keys'));
    selected = Array.from(new Set(selected)).filter(function (key) { return current.some(function (record) { return record.key === key; }); });
    var backupConfirmed = !!field(root, 'cleanup_backup'), confirmation = String(field(root, 'cleanup_confirmation')).trim().toUpperCase() === 'CLEAN WORKSPACE', protectedKeys = current.filter(function (record) { return selected.indexOf(record.key) >= 0 && record.protected; }).map(function (record) { return record.key; });
    return { ok: selected.length > 0 && backupConfirmed && confirmation, schema: 'sc-workbench-cleanup-plan/2.0', version: VERSION, generatedAt: new Date().toISOString(), scope: scope, selectedKeys: selected, selectedCount: selected.length, protectedKeys: protectedKeys, backupRequired: true, backupConfirmed: backupConfirmed, confirmationValid: confirmation, executionAllowed: selected.length > 0 && backupConfirmed && confirmation, cleanupPlanHash: await sha256({ scope: scope, keys: selected }) };
  }
  async function handle(root, action) {
    var current = await records();
    if (action === 'scan') return { ok: true, schema: 'sc-workbench-storage-inventory/2.0', version: VERSION, generatedAt: new Date().toISOString(), recordCount: current.length, records: current, families: current.reduce(function (acc, record) { var key = classify(record.key).source; acc[key] = (acc[key] || 0) + 1; return acc; }, {}) };
    if (action === 'health') { var result = await audit(current, +(field(root, 'quota_bytes') || 5242880)); root.__scwbV302Health = result; return result; }
    if (action === 'migration-preview') { var preview = await migrationPreview(root, current); root.__scwbV302Migration = preview; return preview; }
    if (action === 'migration-apply') { var plan = root.__scwbV302Migration || await migrationPreview(root, current); if (!plan.executionAllowed) throw new Error('Migration preview is not executable. Resolve collisions first.'); await backup(root, current, true); var byKey = new Map(current.map(function (r) { return [r.key, r]; })); plan.mappings.forEach(function (mapping) { if (mapping.action === 'skip' || mapping.action === 'keep') return; var record = byKey.get(mapping.sourceKey); localStorage.setItem(mapping.targetKey, JSON.stringify(record.value)); }); localStorage.setItem(CANONICAL_PREFIX + ':' + slug(plan.projectId) + ':project:manifest', JSON.stringify(plan.projectManifest)); return { ok: true, schema: 'sc-workbench-migration-execution/2.0', version: VERSION, migratedCount: plan.mappings.filter(function (m) { return m.action === 'migrate' || m.action === 'preserve'; }).length, backupDownloaded: true, sourceRecordsPreserved: true, finalRecordCount: (await records()).length }; }
    if (action === 'backup') return backup(root, current, true);
    if (action === 'copy-backup-hash') { var value = root.__scwbV302Backup && root.__scwbV302Backup.backupHash; if (!value) throw new Error('Create a backup first.'); await navigator.clipboard.writeText(value); return { ok: true, schema: 'sc-workbench-backup-hash-copy/1.0', version: VERSION, backupHash: value }; }
    if (action === 'restore-validate') { var envelope = await readFile(root), restore = await restorePlan(root, envelope, current); root.__scwbV302RestoreEnvelope = envelope; root.__scwbV302RestorePlan = restore; return restore; }
    if (action === 'restore-apply') { var env = root.__scwbV302RestoreEnvelope || await readFile(root), rp = root.__scwbV302RestorePlan || await restorePlan(root, env, current); return applyRestore(root, env, rp); }
    if (action === 'cleanup-plan') { var health = root.__scwbV302Health || await audit(current, +(field(root, 'quota_bytes') || 5242880)), cp = await cleanupPlan(root, current, health); root.__scwbV302CleanupPlan = cp; return cp; }
    if (action === 'cleanup-apply') { var cp2 = root.__scwbV302CleanupPlan || await cleanupPlan(root, current, root.__scwbV302Health || await audit(current, 5242880)); if (!cp2.executionAllowed) throw new Error('Cleanup plan is not authorized.'); cp2.selectedKeys.forEach(function (key) { localStorage.removeItem(key); }); return { ok: true, schema: 'sc-workbench-cleanup-execution/2.0', version: VERSION, removedKeys: cp2.selectedKeys, finalRecordCount: (await records()).length }; }
    if (action === 'rollback-plan') { var parsed = JSON.parse(field(root, 'rollback_backup') || '{}'), validation = await validateBackup(parsed), currentKeys = new Set(current.map(function (r) { return r.key; })), restoreKeys = new Set((parsed.records || []).map(function (r) { return r.key; })), confirmation = String(field(root, 'rollback_confirmation')).trim().toUpperCase() === 'ROLLBACK WORKBENCH', confirmed = !!field(root, 'rollback_backup_confirmed'), rollback = { ok: validation.valid && confirmed && confirmation, schema: 'sc-workbench-rollback-plan/2.0', version: VERSION, createKeys: Array.from(restoreKeys).filter(function (k) { return !currentKeys.has(k); }), overwriteKeys: Array.from(restoreKeys).filter(function (k) { return currentKeys.has(k); }), removeKeys: Array.from(currentKeys).filter(function (k) { return !restoreKeys.has(k); }), backupConfirmed: confirmed, confirmationValid: confirmation, executionAllowed: validation.valid && confirmed && confirmation, validation: validation }; rollback.rollbackPlanHash = await sha256(rollback); root.__scwbV302RollbackBackup = parsed; root.__scwbV302RollbackPlan = rollback; return rollback; }
    if (action === 'rollback-apply') { var rb = root.__scwbV302RollbackBackup, rplan = root.__scwbV302RollbackPlan; if (!rb || !rplan || !rplan.executionAllowed) throw new Error('Create and approve a rollback plan first.'); rplan.removeKeys.forEach(function (key) { localStorage.removeItem(key); }); rb.records.forEach(function (record) { localStorage.setItem(record.key, JSON.stringify(record.value)); }); return { ok: true, schema: 'sc-workbench-rollback-execution/2.0', version: VERSION, restoredCount: rb.records.length, finalRecordCount: (await records()).length }; }
    if (action === 'export-report') { if (!root.__scwbV302Result) throw new Error('Run an audit first.'); download('workbench-storage-audit.json', root.__scwbV302Result); return root.__scwbV302Result; }
    throw new Error('Unknown recovery action: ' + action);
  }
  function activate(root, key) { all(root, '[data-scwb-v302-tab]').forEach(function (tab) { tab.classList.toggle('is-active', tab.dataset.scwbV302Tab === key); }); all(root, '[data-scwb-v302-view]').forEach(function (panel) { var active = panel.dataset.scwbV302View === key; panel.classList.toggle('is-active', active); panel.hidden = !active; }); root.dataset.scwbV302Panel = key; }
  function init(root) { if (root.dataset.scwbV302Ready === 'true') return; root.dataset.scwbV302Ready = 'true'; activate(root, root.dataset.scwbV302Panel || 'overview'); }
  document.addEventListener('click', async function (event) { var tab = event.target.closest('[data-scwb-v302-tab]'); if (tab) { var rt = tab.closest('[data-scwb-v302]'); if (rt) activate(rt, tab.dataset.scwbV302Tab); return; } var button = event.target.closest('[data-scwb-v302-action]'); if (!button) return; var root = button.closest('[data-scwb-v302]'); if (!root) return; button.disabled = true; try { render(root, await handle(root, button.dataset.scwbV302Action)); } catch (error) { render(root, { ok: false, schema: 'sc-workbench-recovery-error/2.0', version: VERSION, error: error.message }); } finally { button.disabled = false; } });
  function start() { document.querySelectorAll('[data-scwb-v302]').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  if ('MutationObserver' in window) new MutationObserver(function (mutations) { mutations.forEach(function (mutation) { mutation.addedNodes.forEach(function (node) { if (!node || node.nodeType !== 1) return; if (node.matches && node.matches('[data-scwb-v302]')) init(node); if (node.querySelectorAll) node.querySelectorAll('[data-scwb-v302]').forEach(init); }); }); }).observe(document.documentElement, { childList: true, subtree: true });
  window.SCWBRecovery = { version: VERSION, scan: records, classify: classify, audit: audit, migrationPreview: migrationPreview, validateBackup: validateBackup };
})();
