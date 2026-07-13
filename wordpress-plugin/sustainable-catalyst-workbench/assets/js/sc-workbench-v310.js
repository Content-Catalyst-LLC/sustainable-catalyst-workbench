(function () {
  'use strict';

  var VERSION = '3.1.0';
  var PROJECT_SCHEMA = 'sc-workbench-persistent-project/1.0';
  var REVISION_SCHEMA = 'sc-workbench-project-revision/1.0';
  var PACKAGE_SCHEMA = 'sc-workbench-project-workspace-package/1.0';
  var ROOT_SELECTOR = '[data-scwb-v310]';
  var PREFIX = 'scwb-v310:';
  var INDEX_KEY = PREFIX + 'projects:index';
  var ACTIVE_KEY = PREFIX + 'projects:active';
  var PROJECT_PREFIX = PREFIX + 'project:';
  var REVISION_PREFIX = PREFIX + 'revisions:';
  var CONFIG = window.SCWBV310Config || {
    version: VERSION,
    restUrl: '/wp-json/scwb/v1',
    nonce: '',
    authenticated: false,
    currentUser: 0,
    autosaveDelay: 1800,
    maxLocalRevisions: 50
  };

  function now() { return new Date().toISOString(); }
  function list(scope, selector) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }
  function field(root, name) { return root.querySelector('[data-scwb-v310-field="' + name + '"]'); }
  function value(root, name) {
    var node = field(root, name);
    if (!node) return '';
    if (node.type === 'checkbox') return !!node.checked;
    return node.value;
  }
  function setValue(root, name, next) {
    var node = field(root, name);
    if (!node) return;
    if (node.type === 'checkbox') node.checked = !!next;
    else node.value = next == null ? '' : String(next);
  }
  function slug(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80) || 'project';
  }
  function unique(values) {
    return Array.from(new Set((values || []).map(function (item) { return String(item).trim(); }).filter(Boolean)));
  }
  function parseJson(value, fallback) {
    try { return JSON.parse(value); } catch (error) { return fallback; }
  }
  function safeStorage() {
    try {
      var probe = PREFIX + 'probe';
      localStorage.setItem(probe, '1');
      localStorage.removeItem(probe);
      return localStorage;
    } catch (error) { return null; }
  }
  var storage = safeStorage();

  function stable(value) {
    if (Array.isArray(value)) return value.map(stable);
    if (value && typeof value === 'object') {
      return Object.keys(value).sort().reduce(function (result, key) {
        result[key] = stable(value[key]);
        return result;
      }, {});
    }
    return value;
  }
  function canonical(value) { return JSON.stringify(stable(value)); }
  function fallbackHash(text) {
    var h1 = 0x811c9dc5;
    for (var i = 0; i < text.length; i += 1) {
      h1 ^= text.charCodeAt(i);
      h1 = Math.imul(h1, 0x01000193);
    }
    return ('00000000' + (h1 >>> 0).toString(16)).slice(-8);
  }
  function hashValue(value) {
    var text = canonical(value);
    if (window.crypto && window.crypto.subtle && window.TextEncoder) {
      return window.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)).then(function (buffer) {
        return Array.prototype.map.call(new Uint8Array(buffer), function (byte) { return byte.toString(16).padStart(2, '0'); }).join('');
      });
    }
    return Promise.resolve(fallbackHash(text));
  }

  function projectKey(id) { return PROJECT_PREFIX + slug(id); }
  function revisionsKey(id) { return REVISION_PREFIX + slug(id); }
  function readIndex() {
    if (!storage) return [];
    var raw = parseJson(storage.getItem(INDEX_KEY) || '[]', []);
    return Array.isArray(raw) ? unique(raw.map(slug)) : [];
  }
  function writeIndex(ids) {
    if (storage) storage.setItem(INDEX_KEY, JSON.stringify(unique(ids.map(slug))));
  }
  function readProject(id) {
    if (!storage) return null;
    var project = parseJson(storage.getItem(projectKey(id)) || 'null', null);
    return project && typeof project === 'object' ? project : null;
  }
  function readProjects() {
    return readIndex().map(readProject).filter(Boolean).sort(sortProjects);
  }
  function readRevisions(id) {
    if (!storage) return [];
    var items = parseJson(storage.getItem(revisionsKey(id)) || '[]', []);
    return Array.isArray(items) ? items : [];
  }
  function writeRevisions(id, revisions) {
    if (!storage) return;
    var max = Number(CONFIG.maxLocalRevisions) || 50;
    storage.setItem(revisionsKey(id), JSON.stringify(revisions.slice(0, max)));
  }
  function removeProject(id) {
    if (!storage) return;
    storage.removeItem(projectKey(id));
    storage.removeItem(revisionsKey(id));
    writeIndex(readIndex().filter(function (key) { return key !== slug(id); }));
  }
  function sortProjects(a, b) {
    if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1;
    return String(b.updated_at || '').localeCompare(String(a.updated_at || ''));
  }

  function newProject(title) {
    var timestamp = Date.now();
    var cleanTitle = String(title || 'Untitled Workbench project').trim() || 'Untitled Workbench project';
    return {
      schema: PROJECT_SCHEMA,
      project_id: slug(cleanTitle + '-' + timestamp.toString(36)),
      wordpress_id: 0,
      title: cleanTitle,
      description: '',
      status: 'draft',
      owner_id: String(CONFIG.currentUser || ''),
      storage_mode: CONFIG.authenticated ? 'hybrid' : 'browser',
      tags: [],
      pinned: false,
      created_at: now(),
      updated_at: now(),
      local_revision: 0,
      server_revision: 0,
      active_studio: 'unified',
      studio_records: {},
      evidence_ids: [],
      artifact_ids: [],
      metadata: {},
      content_hash: ''
    };
  }

  function normalize(project) {
    var base = Object.assign(newProject(project && project.title), project || {});
    base.schema = PROJECT_SCHEMA;
    base.project_id = slug(base.project_id || base.title);
    base.title = String(base.title || 'Untitled Workbench project').trim().slice(0, 180) || 'Untitled Workbench project';
    base.description = String(base.description || '');
    base.status = ['draft','active','review','complete','archived'].indexOf(base.status) >= 0 ? base.status : 'draft';
    base.storage_mode = ['browser','hybrid','wordpress'].indexOf(base.storage_mode) >= 0 ? base.storage_mode : 'browser';
    base.tags = unique(base.tags);
    base.pinned = !!base.pinned;
    base.created_at = base.created_at || now();
    base.updated_at = base.updated_at || now();
    base.local_revision = Math.max(0, Number(base.local_revision) || 0);
    base.server_revision = Math.max(0, Number(base.server_revision) || 0);
    base.active_studio = slug(base.active_studio || 'unified');
    base.studio_records = base.studio_records && typeof base.studio_records === 'object' ? base.studio_records : {};
    base.evidence_ids = unique(base.evidence_ids);
    base.artifact_ids = unique(base.artifact_ids);
    base.metadata = base.metadata && typeof base.metadata === 'object' ? base.metadata : {};
    return base;
  }

  function saveLocal(project, options) {
    options = options || {};
    project = normalize(project);
    if (!options.preserveRevision) project.local_revision += 1;
    if (!options.preserveTimestamp) project.updated_at = now();
    var unhashed = Object.assign({}, project);
    delete unhashed.content_hash;
    return hashValue(unhashed).then(function (digest) {
      project.content_hash = digest;
      if (storage) {
        storage.setItem(projectKey(project.project_id), JSON.stringify(project));
        writeIndex(readIndex().concat(project.project_id));
        storage.setItem(ACTIVE_KEY, project.project_id);
      }
      return project;
    });
  }

  function createRevision(project, reason) {
    project = normalize(project);
    var existing = readRevisions(project.project_id);
    var revision = {
      schema: REVISION_SCHEMA,
      version: VERSION,
      project_id: project.project_id,
      revision: Math.max(project.local_revision, project.server_revision) + 1,
      reason: String(reason || 'manual-save').slice(0, 100),
      created_at: now(),
      parent_hash: existing[0] ? existing[0].revision_hash : '',
      project_hash: project.content_hash || '',
      snapshot: project
    };
    var unhashed = Object.assign({}, revision);
    return hashValue(unhashed).then(function (digest) {
      revision.revision_hash = digest;
      existing.unshift(revision);
      writeRevisions(project.project_id, existing);
      return revision;
    });
  }

  function api(path, options) {
    options = options || {};
    var headers = Object.assign({'Content-Type': 'application/json'}, options.headers || {});
    if (CONFIG.nonce) headers['X-WP-Nonce'] = CONFIG.nonce;
    return fetch(String(CONFIG.restUrl || '/wp-json/scwb/v1').replace(/\/$/, '') + path, Object.assign({}, options, {headers: headers})).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) throw new Error(body.message || ('Request failed: ' + response.status));
        return body;
      });
    });
  }

  function notify(root, message, kind) {
    var node = root.querySelector('[data-scwb-v310-notice]');
    if (!node) return;
    node.textContent = message;
    node.setAttribute('data-kind', kind || 'info');
  }
  function saveState(root, message, dirty) {
    var node = root.querySelector('[data-scwb-v310-save-state]');
    if (node) node.textContent = message;
    root.setAttribute('data-scwb-v310-dirty', dirty ? 'true' : 'false');
  }
  function formatBytes(bytes) {
    bytes = Number(bytes) || 0;
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(2) + ' MB';
  }
  function download(name, content, type) {
    var blob = new Blob([content], {type: type || 'application/json'});
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    document.body.appendChild(link);
    link.click();
    window.setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 0);
  }

  function collect(root, current) {
    var project = normalize(current || newProject(value(root, 'title')));
    var id = value(root, 'project_id');
    project.project_id = slug(id || project.project_id);
    project.title = String(value(root, 'title') || project.title).trim();
    project.description = String(value(root, 'description') || '');
    project.status = value(root, 'status') || 'draft';
    project.storage_mode = value(root, 'storage_mode') || 'browser';
    project.tags = unique(String(value(root, 'tags') || '').split(','));
    project.pinned = !!value(root, 'pinned');
    var shared = parseJson(value(root, 'project_json'), null);
    if (!shared || typeof shared !== 'object') throw new Error('Project JSON is invalid.');
    project.active_studio = shared.active_studio || project.active_studio;
    project.studio_records = shared.studio_records || {};
    project.evidence_ids = shared.evidence_ids || [];
    project.artifact_ids = shared.artifact_ids || [];
    project.metadata = shared.metadata || {};
    return normalize(project);
  }

  function populate(root, project) {
    project = normalize(project);
    setValue(root, 'project_id', project.project_id);
    setValue(root, 'title', project.title);
    setValue(root, 'description', project.description);
    setValue(root, 'status', project.status);
    setValue(root, 'storage_mode', project.storage_mode);
    setValue(root, 'tags', project.tags.join(', '));
    setValue(root, 'pinned', project.pinned);
    setValue(root, 'project_json', JSON.stringify({
      active_studio: project.active_studio,
      studio_records: project.studio_records,
      evidence_ids: project.evidence_ids,
      artifact_ids: project.artifact_ids,
      metadata: project.metadata
    }, null, 2));
    var summary = root.querySelector('[data-scwb-v310-project-summary]');
    if (summary) {
      summary.innerHTML = '<strong>' + escapeHtml(project.title) + '</strong><span>' + escapeHtml(project.project_id) + ' · ' + escapeHtml(project.status) + ' · local r' + project.local_revision + ' · server r' + project.server_revision + '</span><span>Updated ' + escapeHtml(project.updated_at) + '</span>';
    }
    saveState(root, 'Project loaded. Autosave is active.', false);
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, function (char) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[char];
    });
  }

  function projectCard(project, remote) {
    var source = remote ? 'WordPress' : 'Browser';
    return '<article class="scwb-v310__project-card" data-project-id="' + escapeHtml(project.project_id) + '">' +
      '<div><strong>' + escapeHtml(project.title) + '</strong><span>' + escapeHtml(project.status) + ' · ' + source + (project.pinned ? ' · pinned' : '') + '</span></div>' +
      '<p>' + escapeHtml(project.description || 'No description.') + '</p>' +
      '<div class="scwb-v310__project-card-actions"><button type="button" data-scwb-v310-load="' + escapeHtml(project.project_id) + '">Open</button><button type="button" data-scwb-v310-duplicate="' + escapeHtml(project.project_id) + '">Duplicate</button><button type="button" data-scwb-v310-delete="' + escapeHtml(project.project_id) + '">Delete local</button></div>' +
      '</article>';
  }

  function renderProjects(root, state) {
    var local = readProjects();
    var localIds = new Set(local.map(function (project) { return project.project_id; }));
    var remoteOnly = (state.serverProjects || []).filter(function (project) { return !localIds.has(project.project_id); });
    var combined = local.concat(remoteOnly).sort(sortProjects);
    var search = String((root.querySelector('[data-scwb-v310-filter="search"]') || {}).value || '').toLowerCase();
    var status = String((root.querySelector('[data-scwb-v310-filter="status"]') || {}).value || '');
    var pinned = !!((root.querySelector('[data-scwb-v310-filter="pinned"]') || {}).checked);
    var filtered = combined.filter(function (project) {
      var haystack = [project.title, project.project_id, project.status].concat(project.tags || []).join(' ').toLowerCase();
      return (!search || haystack.indexOf(search) >= 0) && (!status || project.status === status) && (!pinned || project.pinned);
    });
    var target = root.querySelector('[data-scwb-v310-project-list]');
    if (target) target.innerHTML = filtered.length ? filtered.map(function (project) { return projectCard(project, !localIds.has(project.project_id)); }).join('') : '<p class="scwb-v310__empty">No matching projects.</p>';

    var select = root.querySelector('[data-scwb-v310-project-select]');
    if (select) {
      select.innerHTML = combined.map(function (project) { return '<option value="' + escapeHtml(project.project_id) + '">' + escapeHtml(project.title) + (localIds.has(project.project_id) ? '' : ' · WordPress') + '</option>'; }).join('');
      if (state.active) select.value = state.active.project_id;
    }
    var recent = root.querySelector('[data-scwb-v310-recent]');
    if (recent) recent.innerHTML = combined.slice(0, 5).map(function (p) { return '<button type="button" data-scwb-v310-load="' + escapeHtml(p.project_id) + '"><strong>' + escapeHtml(p.title) + '</strong><span>' + escapeHtml(p.updated_at) + '</span></button>'; }).join('') || '<p>No saved projects yet.</p>';
  }

  function renderRevisions(root, project, remoteRevisions) {
    var revisions = readRevisions(project.project_id);
    var target = root.querySelector('[data-scwb-v310-revision-list]');
    if (!target) return;
    var rows = revisions.map(function (revision) {
      return '<article><div><strong>Local revision ' + revision.revision + '</strong><span>' + escapeHtml(revision.reason) + '</span></div><time>' + escapeHtml(revision.created_at) + '</time><button type="button" data-scwb-v310-restore-revision="' + escapeHtml(revision.revision_hash) + '">Restore</button></article>';
    });
    (remoteRevisions || []).forEach(function (revision) {
      rows.push('<article class="is-server"><div><strong>Server revision ' + escapeHtml(revision.revision || '') + '</strong><span>' + escapeHtml(revision.reason || 'server-save') + '</span></div><time>' + escapeHtml(revision.created_at || revision.createdAt || '') + '</time><span>WordPress</span></article>');
    });
    target.innerHTML = rows.join('') || '<p class="scwb-v310__empty">No revisions have been created.</p>';
  }

  function updateStats(root) {
    var projects = readProjects();
    var revisionCount = projects.reduce(function (sum, p) { return sum + readRevisions(p.project_id).length; }, 0);
    var bytes = 0;
    if (storage) {
      for (var i = 0; i < storage.length; i += 1) {
        var key = storage.key(i);
        if (key && key.indexOf('scwb-') === 0) bytes += key.length + (storage.getItem(key) || '').length;
      }
    }
    var values = {'local-projects': projects.length, 'local-revisions': revisionCount, 'bytes': formatBytes(bytes), 'server': CONFIG.authenticated ? 'Available' : 'Sign in to enable'};
    Object.keys(values).forEach(function (key) {
      var node = root.querySelector('[data-scwb-v310-stat="' + key + '"]');
      if (node) node.textContent = values[key];
    });
  }

  function projectChanged(project) {
    document.dispatchEvent(new CustomEvent('scwb:project-changed', {bubbles: true, detail: {project: project, projectId: project.project_id, version: VERSION}}));
    list(document, '[data-scwb-primary]').forEach(function (primary) { primary.setAttribute('data-scwb-project', project.project_id); });
  }

  function serverProject(state, id) {
    return (state.serverProjects || []).find(function (project) { return project.project_id === id || String(project.wordpress_id) === String(id); }) || null;
  }

  function loadProject(root, state, id) {
    var project = readProject(id) || serverProject(state, id);
    if (!project) return Promise.reject(new Error('Project not found: ' + id));
    state.active = normalize(project);
    if (storage) storage.setItem(ACTIVE_KEY, state.active.project_id);
    populate(root, state.active);
    renderProjects(root, state);
    renderRevisions(root, state.active, state.remoteRevisions[state.active.project_id] || []);
    projectChanged(state.active);
    if (CONFIG.authenticated && state.active.wordpress_id) {
      api('/projects/' + state.active.wordpress_id + '/revisions', {method: 'GET'}).then(function (response) {
        state.remoteRevisions[state.active.project_id] = response.revisions || [];
        renderRevisions(root, state.active, state.remoteRevisions[state.active.project_id]);
      }).catch(function () {});
    }
    return Promise.resolve(state.active);
  }

  function persistServer(project, reason) {
    if (!CONFIG.authenticated || project.storage_mode === 'browser') return Promise.resolve(project);
    var path = project.wordpress_id ? '/projects/' + project.wordpress_id : '/projects';
    var method = project.wordpress_id ? 'PUT' : 'POST';
    var payload = Object.assign({}, project, {revision_reason: reason || 'server-save'});
    return api(path, {method: method, body: JSON.stringify(payload)}).then(function (response) { return normalize(response.project || project); });
  }

  function saveProject(root, state, reason, autosave) {
    var project;
    try { project = collect(root, state.active); }
    catch (error) { notify(root, error.message, 'error'); return Promise.reject(error); }
    saveState(root, autosave ? 'Autosaving…' : 'Saving…', true);
    return saveLocal(project).then(function (localProject) {
      state.active = localProject;
      return createRevision(localProject, reason || (autosave ? 'autosave' : 'manual-save')).then(function () {
        return persistServer(localProject, reason || (autosave ? 'autosave' : 'manual-save')).catch(function (error) {
          notify(root, 'Saved locally. WordPress synchronization failed: ' + error.message, 'warning');
          return localProject;
        });
      });
    }).then(function (finalProject) {
      state.active = finalProject;
      return saveLocal(finalProject, {preserveRevision: true, preserveTimestamp: true});
    }).then(function (finalProject) {
      state.active = finalProject;
      populate(root, finalProject);
      renderProjects(root, state);
      renderRevisions(root, finalProject, state.remoteRevisions[finalProject.project_id] || []);
      updateStats(root);
      saveState(root, (autosave ? 'Autosaved ' : 'Saved ') + new Date().toLocaleTimeString(), false);
      notify(root, autosave ? 'Project autosaved.' : 'Project saved.', 'success');
      projectChanged(finalProject);
      return finalProject;
    });
  }

  function refreshServer(root, state) {
    if (!CONFIG.authenticated) return Promise.resolve([]);
    notify(root, 'Loading private WordPress projects…');
    return api('/projects', {method: 'GET'}).then(function (response) {
      state.serverProjects = (response.projects || []).map(normalize);
      notify(root, 'Loaded ' + state.serverProjects.length + ' private WordPress projects.', 'success');
      return state.serverProjects;
    }).catch(function (error) {
      notify(root, 'WordPress project storage unavailable: ' + error.message, 'warning');
      return [];
    });
  }

  function syncProject(root, state) {
    if (!CONFIG.authenticated) return Promise.reject(new Error('Sign in to enable WordPress synchronization.'));
    var local = state.active;
    var remote = serverProject(state, local.project_id);
    var strategy = value(root, 'sync_strategy') || 'newest';
    var decision = 'none';
    if (!remote) decision = 'upload-local';
    else if (local.content_hash === remote.content_hash) decision = 'already-synchronized';
    else if (strategy === 'local') decision = 'upload-local';
    else if (strategy === 'remote') decision = 'download-remote';
    else if (strategy === 'manual') decision = 'manual-review';
    else {
      var localRank = [local.local_revision, local.server_revision, local.updated_at].join('|');
      var remoteRank = [remote.server_revision, remote.local_revision, remote.updated_at].join('|');
      decision = localRank > remoteRank ? 'upload-local' : (remoteRank > localRank ? 'download-remote' : 'manual-review');
    }
    var result = {schema: 'sc-workbench-project-sync-plan/1.0', version: VERSION, projectId: local.project_id, decision: decision, conflict: !!remote && local.content_hash !== remote.content_hash, localHash: local.content_hash || '', remoteHash: remote ? remote.content_hash || '' : ''};
    var output = root.querySelector('[data-scwb-v310-sync-result]');
    if (decision === 'upload-local') {
      return persistServer(local, 'synchronization').then(function (saved) {
        state.active = saved;
        return saveLocal(saved, {preserveRevision: true});
      }).then(function () { return refreshServer(root, state); }).then(function () {
        result.ok = true; result.message = 'Browser project uploaded to WordPress.';
        if (output) output.textContent = JSON.stringify(result, null, 2);
        populate(root, state.active); renderProjects(root, state); projectChanged(state.active); return result;
      });
    }
    if (decision === 'download-remote') {
      return saveLocal(remote, {preserveRevision: true, preserveTimestamp: true}).then(function (saved) {
        state.active = saved; result.ok = true; result.message = 'WordPress project restored to this browser.';
        if (output) output.textContent = JSON.stringify(result, null, 2);
        populate(root, saved); renderProjects(root, state); projectChanged(saved); return result;
      });
    }
    result.ok = decision === 'already-synchronized';
    result.message = decision === 'already-synchronized' ? 'Local and WordPress records already match.' : 'Manual conflict review is required.';
    if (output) output.textContent = JSON.stringify(result, null, 2);
    return Promise.resolve(result);
  }

  function activateTab(root, key) {
    list(root, '[data-scwb-v310-tab]').forEach(function (tab) {
      var active = tab.getAttribute('data-scwb-v310-tab') === key;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    list(root, '[data-scwb-v310-view]').forEach(function (panel) {
      var active = panel.getAttribute('data-scwb-v310-view') === key;
      panel.classList.toggle('is-active', active);
      panel.hidden = !active;
    });
  }

  function init(root) {
    if (root.getAttribute('data-scwb-v310-ready') === 'true') return;
    root.setAttribute('data-scwb-v310-ready', 'true');
    var state = {active: null, serverProjects: [], remoteRevisions: {}, autosaveTimer: null};
    root.__scwbV310 = state;
    var initial = root.getAttribute('data-scwb-v310-panel') || 'workspace';
    activateTab(root, initial);

    var projects = readProjects();
    if (!projects.length) {
      var first = newProject('My Workbench Project');
      first.project_id = slug(root.getAttribute('data-scwb-v310-project') || first.project_id);
      saveLocal(first, {preserveRevision: true}).then(function (saved) { return loadProject(root, state, saved.project_id); }).then(function () { renderProjects(root, state); updateStats(root); });
    } else {
      var requested = (storage && storage.getItem(ACTIVE_KEY)) || root.getAttribute('data-scwb-v310-project') || projects[0].project_id;
      loadProject(root, state, requested).catch(function () { return loadProject(root, state, projects[0].project_id); }).then(function () { renderProjects(root, state); updateStats(root); });
    }
    refreshServer(root, state).then(function () { renderProjects(root, state); });

    root.addEventListener('input', function (event) {
      if (!event.target.closest('[data-scwb-v310-field]')) return;
      saveState(root, 'Unsaved changes. Autosave pending…', true);
      window.clearTimeout(state.autosaveTimer);
      state.autosaveTimer = window.setTimeout(function () { saveProject(root, state, 'autosave', true).catch(function () {}); }, Number(CONFIG.autosaveDelay) || 1800);
    });
    root.addEventListener('change', function (event) {
      if (event.target.matches('[data-scwb-v310-project-select]')) loadProject(root, state, event.target.value).catch(function (error) { notify(root, error.message, 'error'); });
      if (event.target.matches('[data-scwb-v310-filter]')) renderProjects(root, state);
    });
    window.addEventListener('beforeunload', function () {
      if (root.getAttribute('data-scwb-v310-dirty') === 'true' && state.active) {
        try {
          var project = collect(root, state.active);
          project.updated_at = now();
          if (storage) storage.setItem(projectKey(project.project_id), JSON.stringify(project));
        } catch (error) {}
      }
    });
  }

  document.addEventListener('click', function (event) {
    var root = event.target.closest(ROOT_SELECTOR);
    if (!root) return;
    var state = root.__scwbV310;
    var tab = event.target.closest('[data-scwb-v310-tab]');
    if (tab) { event.preventDefault(); activateTab(root, tab.getAttribute('data-scwb-v310-tab')); return; }
    var load = event.target.closest('[data-scwb-v310-load]');
    if (load) { event.preventDefault(); loadProject(root, state, load.getAttribute('data-scwb-v310-load')).then(function () { activateTab(root, 'editor'); }); return; }
    var duplicate = event.target.closest('[data-scwb-v310-duplicate]');
    if (duplicate) {
      var original = readProject(duplicate.getAttribute('data-scwb-v310-duplicate'));
      if (original) {
        var copy = normalize(Object.assign({}, original, {project_id: slug(original.project_id + '-copy-' + Date.now().toString(36)), title: original.title + ' Copy', wordpress_id: 0, local_revision: 0, server_revision: 0, created_at: now(), updated_at: now()}));
        saveLocal(copy, {preserveRevision: true}).then(function () { renderProjects(root, state); updateStats(root); notify(root, 'Project duplicated.', 'success'); });
      }
      return;
    }
    var remove = event.target.closest('[data-scwb-v310-delete]');
    if (remove) {
      var id = remove.getAttribute('data-scwb-v310-delete');
      if (window.confirm('Delete the browser-local project "' + id + '"? Export it first if it is important.')) {
        removeProject(id); renderProjects(root, state); updateStats(root); notify(root, 'Browser project deleted.', 'warning');
      }
      return;
    }
    var restore = event.target.closest('[data-scwb-v310-restore-revision]');
    if (restore && state.active) {
      var revision = readRevisions(state.active.project_id).find(function (item) { return item.revision_hash === restore.getAttribute('data-scwb-v310-restore-revision'); });
      if (revision && revision.snapshot && window.confirm('Restore this local revision? A new safety revision will be created first.')) {
        createRevision(state.active, 'before-local-restore').then(function () { return saveLocal(revision.snapshot); }).then(function (saved) { state.active = saved; populate(root, saved); renderRevisions(root, saved); projectChanged(saved); notify(root, 'Revision restored.', 'success'); });
      }
      return;
    }
    var actionNode = event.target.closest('[data-scwb-v310-action]');
    if (!actionNode || !state) return;
    event.preventDefault();
    var action = actionNode.getAttribute('data-scwb-v310-action');
    if (action === 'new-project') {
      var title = window.prompt('Project title', 'Untitled Workbench project');
      if (title === null) return;
      var project = newProject(title);
      saveLocal(project, {preserveRevision: true}).then(function (saved) { return loadProject(root, state, saved.project_id); }).then(function () { renderProjects(root, state); updateStats(root); activateTab(root, 'editor'); notify(root, 'New project created.', 'success'); });
    } else if (action === 'save-project') {
      saveProject(root, state, 'manual-save', false).catch(function (error) { notify(root, error.message, 'error'); });
    } else if (action === 'snapshot') {
      var reason = value(root, 'revision_reason') || 'manual-snapshot';
      saveProject(root, state, reason, false).then(function () { renderRevisions(root, state.active, state.remoteRevisions[state.active.project_id] || []); notify(root, 'Revision snapshot created.', 'success'); }).catch(function (error) { notify(root, error.message, 'error'); });
    } else if (action === 'export-project' && state.active) {
      var revisions = readRevisions(state.active.project_id);
      var pack = {schema: PACKAGE_SCHEMA, version: VERSION, generated_at: now(), project: state.active, revisions: revisions};
      hashValue(pack).then(function (digest) { pack.package_hash = digest; download('workbench-' + state.active.project_id + '-v310.json', JSON.stringify(pack, null, 2)); notify(root, 'Project package exported.', 'success'); });
    } else if (action === 'import-project') {
      var input = root.querySelector('[data-scwb-v310-import]'); if (input) input.click();
    } else if (action === 'prune-revisions' && state.active) {
      var revisions = readRevisions(state.active.project_id).slice(0, Number(CONFIG.maxLocalRevisions) || 50); writeRevisions(state.active.project_id, revisions); renderRevisions(root, state.active); updateStats(root); notify(root, 'Old local revisions pruned.', 'success');
    } else if (action === 'open-recovery') {
      var primary = root.closest('[data-scwb-primary]');
      if (primary && window.SCWBPrimaryRouter) window.SCWBPrimaryRouter.activate(primary, 'recovery', {focus: true});
      else window.location.hash = '#workbench-studio-recovery';
    } else if (action === 'refresh-server') {
      refreshServer(root, state).then(function () { renderProjects(root, state); });
    } else if (action === 'sync-project') {
      syncProject(root, state).then(function (result) { notify(root, result.message, result.ok ? 'success' : 'warning'); }).catch(function (error) { notify(root, error.message, 'error'); });
    }
  });

  document.addEventListener('change', function (event) {
    if (!event.target.matches('[data-scwb-v310-import]')) return;
    var root = event.target.closest(ROOT_SELECTOR);
    var state = root && root.__scwbV310;
    var file = event.target.files && event.target.files[0];
    if (!root || !state || !file) return;
    file.text().then(function (text) {
      var raw = JSON.parse(text);
      var project = normalize(raw.project || raw);
      project.wordpress_id = 0;
      project.project_id = slug(project.project_id + '-import-' + Date.now().toString(36));
      project.storage_mode = CONFIG.authenticated ? 'hybrid' : 'browser';
      return saveLocal(project, {preserveRevision: true}).then(function (saved) {
        var revisions = Array.isArray(raw.revisions) ? raw.revisions : [];
        writeRevisions(saved.project_id, revisions);
        return loadProject(root, state, saved.project_id);
      });
    }).then(function () { renderProjects(root, state); renderRevisions(root, state.active); updateStats(root); notify(root, 'Project imported.', 'success'); }).catch(function (error) { notify(root, 'Import failed: ' + error.message, 'error'); });
    event.target.value = '';
  });

  function initAll(scope) { list(scope || document, ROOT_SELECTOR).forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { initAll(document); });
  else initAll(document);
  if ('MutationObserver' in window) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) { mutation.addedNodes.forEach(function (node) { if (node && node.nodeType === 1) { if (node.matches && node.matches(ROOT_SELECTOR)) init(node); if (node.querySelectorAll) initAll(node); } }); });
    }).observe(document.documentElement, {childList: true, subtree: true});
  }

  window.SCWBProjectWorkspace = {
    version: VERSION,
    schemas: {project: PROJECT_SCHEMA, revision: REVISION_SCHEMA, package: PACKAGE_SCHEMA},
    newProject: newProject,
    normalize: normalize,
    readProjects: readProjects,
    readProject: readProject,
    readRevisions: readRevisions,
    saveProject: function (project) { return saveLocal(project); },
    createRevision: createRevision,
    getActiveProject: function () { return readProject(storage ? storage.getItem(ACTIVE_KEY) : ''); },
    setActiveProject: function (id) { if (storage) storage.setItem(ACTIVE_KEY, slug(id)); },
    saveStudioRecord: function (studio, record) {
      var active = this.getActiveProject();
      if (!active) return Promise.reject(new Error('No active project.'));
      active.studio_records[slug(studio)] = {updated_at: now(), data: record};
      active.active_studio = slug(studio);
      return saveLocal(active).then(function (saved) { projectChanged(saved); return saved; });
    },
    hashValue: hashValue
  };
})();
