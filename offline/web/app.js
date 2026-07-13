(function () {
  'use strict';
  var VERSION = '3.9.0';
  var STORE = 'scwb:offline:projects';
  var output = document.getElementById('output');
  var status = document.getElementById('service-status');

  function show(value) { output.textContent = JSON.stringify(value, null, 2); }
  function readProjects() {
    try { return JSON.parse(localStorage.getItem(STORE) || '[]'); }
    catch (error) { return []; }
  }
  function writeProjects(projects) { localStorage.setItem(STORE, JSON.stringify(projects)); }

  async function health() {
    try {
      var response = await fetch('/v380/status', { cache: 'no-store' });
      var data = await response.json();
      status.textContent = data.ok ? 'Local service online · v' + data.version : 'Local service needs review';
      status.className = 'status online';
      show(data);
    } catch (error) {
      status.textContent = 'Local service unavailable; browser-local records remain available.';
      status.className = 'status offline';
      show({ ok: false, offlineFallback: true, message: error.message });
    }
  }

  function newProject() {
    var projects = readProjects();
    var project = {
      schema: 'sc-workbench-offline-project/1.0',
      id: 'offline-' + Date.now(),
      title: 'Offline Workbench Project',
      version: VERSION,
      createdAt: new Date().toISOString(),
      records: []
    };
    projects.push(project);
    writeProjects(projects);
    show(project);
  }

  function download(value, name) {
    var blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function exportBundle() {
    var projects = readProjects();
    var bundle = {
      schema: 'sc-workbench-offline-sync-bundle/1.0',
      version: VERSION,
      exportedAt: new Date().toISOString(),
      projects: projects,
      projectCount: projects.length,
      automaticCloudUpload: false,
      requiresExplicitImport: true
    };
    show(bundle);
    download(bundle, 'sustainable-catalyst-workbench-offline-bundle.json');
  }

  function recovery() {
    show({
      schema: 'sc-workbench-offline-recovery-plan/1.0',
      version: VERSION,
      steps: [
        'Stop the local service.',
        'Copy the project store and latest bundle.',
        'Verify package checksums.',
        'Reinstall application files without deleting project data.',
        'Restart on 127.0.0.1 and run the health check.'
      ],
      automaticDeletion: false
    });
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-action]');
    if (!button) return;
    var action = button.getAttribute('data-action');
    if (action === 'health') health();
    if (action === 'new-project') newProject();
    if (action === 'export') exportBundle();
    if (action === 'recovery') recovery();
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js').catch(function () {});
  }
  health();
}());
