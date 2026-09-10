(function () {
  'use strict';

  var VERSION = '6.0.1';
  var SELECTOR = '[data-scwb-primary]';
  var EXPECTED = [
    'computational-project','blackboard','music-mathematics','creative-mathematics','prototype-bench',
    'graph-mathematics','geometry','numerical','signals','electronics','digital-logic','mathematics',
    'platform','connected','unified','projects','teams','guided','data','evaluation','extensions','library',
    'handoffs','reviews','research','embedded','devices','fpga-electronics','robotics','instrumentation',
    'simulation','intelligence','laboratories','offline','hardening','runtime','visualization','experiments',
    'documentation','recovery'
  ];

  function list(root, selector) { return Array.prototype.slice.call(root.querySelectorAll(selector)); }
  function tabs(root) { return list(root, '[data-scwb-primary-tab]:not([disabled])'); }
  function panels(root) { return list(root, '[data-scwb-primary-panel]'); }
  function rows(root) { return list(root, '[data-scwb-tab-row]'); }
  function storageKey(root) { return 'scwb-v601:last-studio:' + (root.getAttribute('data-scwb-project') || 'default'); }
  function favoritesKey(root) { return 'scwb-v601:favorites:' + (root.getAttribute('data-scwb-project') || 'default'); }
  function recentsKey(root) { return 'scwb-v601:recents:' + (root.getAttribute('data-scwb-project') || 'default'); }
  function byKey(items, attribute, key) { return items.find(function (item) { return item.getAttribute(attribute) === key; }) || null; }
  function readList(key) { try { var v = JSON.parse(localStorage.getItem(key) || '[]'); return Array.isArray(v) ? v : []; } catch (error) { return []; } }
  function writeList(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (error) {} }

  function detectBuilder() {
    var body = document.body;
    if (!body) return 'unknown';
    var names = body.className || '';
    if (/elementor/i.test(names) || document.querySelector('.elementor')) return 'elementor';
    if (/block-editor|wp-block/i.test(names) || document.querySelector('.wp-block-shortcode')) return 'gutenberg';
    if (/classic-editor/i.test(names)) return 'classic';
    return 'unknown';
  }

  function panelState(panel) {
    if (!panel) return 'unavailable';
    if (panel.querySelector('.scwb-primary__module-error,[data-scwb-error]')) return 'error';
    var mount = panel.querySelector('[data-scwb-module-mount]');
    if (!mount) return 'empty';
    var text = (mount.textContent || '').trim();
    var interactive = mount.querySelector('button,input,select,textarea,canvas,svg,form,[role="button"],[data-scwb-v600],[data-scwb-v590],[data-scwb-v580],[data-scwb-v570],[data-scwb-v560],[data-scwb-v550],[data-scwb-v540],[data-scwb-v530],[data-scwb-v520],[data-scwb-v510],[data-scwb-v500],[data-scwb-v400],[data-scwb-v300]');
    if (!text && !interactive) return 'empty';
    if (mount.querySelector('[data-backend-status="offline"],.is-offline,[data-runner-status="offline"]')) return 'offline';
    return 'ready';
  }

  function updateTabState(root, key, state) {
    var tab = byKey(tabs(root), 'data-scwb-primary-tab', key);
    if (!tab) return;
    tab.setAttribute('data-scwb-tab-state', state);
    var label = tab.querySelector('em');
    if (label) label.textContent = state === 'ready' ? 'Ready' : state.charAt(0).toUpperCase() + state.slice(1);
  }

  function audit(root) {
    var report = [];
    panels(root).forEach(function (panel) {
      var key = panel.getAttribute('data-scwb-primary-panel');
      var state = panelState(panel);
      panel.setAttribute('data-scwb-panel-state', state);
      updateTabState(root, key, state);
      report.push({ studio: key, state: state, rendered: state !== 'empty' && state !== 'unavailable' });
    });
    root.setAttribute('data-scwb-page-builder', detectBuilder());
    root.setAttribute('data-scwb-audit-count', String(report.length));
    root.dispatchEvent(new CustomEvent('scwb:interface-audited', { bubbles: true, detail: { studios: report, version: VERSION } }));
    return report;
  }

  function redrawVisuals(panel, key) {
    var detail = { studio: key, panel: panel, state: panelState(panel), releaseVersion: VERSION };
    panel.dispatchEvent(new CustomEvent('scwb:studio-activated', { bubbles: true, detail: detail }));
    panel.dispatchEvent(new CustomEvent('scwb:panel-visible', { bubbles: true, detail: detail }));
    window.dispatchEvent(new Event('resize'));
    [60, 180, 420].forEach(function (delay) {
      window.setTimeout(function () {
        panel.querySelectorAll('canvas,svg,[data-chart],[data-plot]').forEach(function (node) {
          node.dispatchEvent(new CustomEvent('scwb:visual-resize', { bubbles: true, detail: detail }));
        });
        window.dispatchEvent(new Event('resize'));
      }, delay);
    });
  }

  function recordRecent(root, key) {
    var recent = readList(recentsKey(root)).filter(function (x) { return x !== key; });
    recent.unshift(key);
    writeList(recentsKey(root), recent.slice(0, 8));
  }

  function updateActiveReadout(root, tab) {
    var readout = root.querySelector('[data-scwb-active-label]');
    if (readout && tab) readout.textContent = tab.getAttribute('data-scwb-studio-label') || tab.textContent.trim();
  }

  function activate(root, key, options) {
    options = options || {};
    var selected = null;
    tabs(root).forEach(function (tab) {
      var active = tab.getAttribute('data-scwb-primary-tab') === key;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.setAttribute('tabindex', active ? '0' : '-1');
      if (active) selected = tab;
    });

    var visiblePanel = null;
    panels(root).forEach(function (panel) {
      var active = panel.getAttribute('data-scwb-primary-panel') === key;
      panel.classList.toggle('is-active', active);
      panel.hidden = !active;
      panel.setAttribute('aria-hidden', active ? 'false' : 'true');
      if (active) visiblePanel = panel;
    });

    if (!selected || !visiblePanel) return false;
    root.setAttribute('data-scwb-active', key);
    updateActiveReadout(root, selected);
    recordRecent(root, key);
    if (root.getAttribute('data-scwb-remember') === 'true') {
      try { localStorage.setItem(storageKey(root), key); } catch (error) {}
    }
    if (options.hash !== false && window.history && window.history.replaceState) {
      var value = '#workbench-studio-' + encodeURIComponent(key);
      if (window.location.hash !== value) window.history.replaceState(null, '', value);
    }
    if (options.focus) selected.focus();
    updateTabState(root, key, panelState(visiblePanel));
    redrawVisuals(visiblePanel, key);
    return true;
  }

  function hashStudio() {
    var match = (window.location.hash || '').match(/^#workbench-studio-([a-z0-9_-]+)$/i);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function preferred(root) {
    var initial = hashStudio() || root.getAttribute('data-scwb-initial') || '';
    if (!hashStudio() && root.getAttribute('data-scwb-remember') === 'true') {
      try { var saved = localStorage.getItem(storageKey(root)); if (saved) initial = saved; } catch (error) {}
    }
    var available = tabs(root).map(function (tab) { return tab.getAttribute('data-scwb-primary-tab'); });
    return available.indexOf(initial) >= 0 ? initial : available[0];
  }

  function syncFavorites(root) {
    var favorites = readList(favoritesKey(root));
    list(root, '[data-scwb-favorite]').forEach(function (button) {
      var active = favorites.indexOf(button.getAttribute('data-scwb-favorite')) >= 0;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.textContent = active ? '★' : '☆';
    });
  }

  function toggleFavorite(root, key) {
    var favorites = readList(favoritesKey(root));
    var index = favorites.indexOf(key);
    if (index >= 0) favorites.splice(index, 1); else favorites.unshift(key);
    writeList(favoritesKey(root), favorites.slice(0, 20));
    syncFavorites(root);
    applyFilter(root);
  }

  function currentFilter(root) {
    var button = root.querySelector('[data-scwb-studio-filter].is-active');
    return button ? button.getAttribute('data-scwb-studio-filter') : 'all';
  }

  function applyFilter(root) {
    var filter = currentFilter(root);
    var search = (root.querySelector('[data-scwb-studio-search]') || {}).value || '';
    search = String(search).trim().toLowerCase();
    var favorites = readList(favoritesKey(root));
    var recents = readList(recentsKey(root));
    rows(root).forEach(function (row) {
      var key = row.getAttribute('data-scwb-studio-key');
      var group = row.getAttribute('data-scwb-studio-group');
      var tab = row.querySelector('[data-scwb-primary-tab]');
      var haystack = ((tab && tab.textContent) || '').toLowerCase();
      var groupPass = filter === 'all' || group === filter || (filter === 'favorites' && favorites.indexOf(key) >= 0) || (filter === 'recent' && recents.indexOf(key) >= 0);
      var searchPass = !search || haystack.indexOf(search) >= 0;
      row.hidden = !(groupPass && searchPass);
    });
  }

  function finishActivation(root) {
    root.classList.remove('is-loading');
    root.classList.add('is-ready');
    root.setAttribute('aria-busy', 'false');
    var activation = root.querySelector('[data-scwb-activation]');
    if (activation) {
      activation.innerHTML = '<span aria-hidden="true">✓</span><span>Workbench v6.0.1 interface activated.</span>';
      activation.classList.add('is-complete');
    }
    var status = root.querySelector('[data-scwb-primary-js-status]');
    if (status) status.textContent = 'Active · grouped navigation, search, favorites, recents, hash routing, and resize-safe studio activation';
  }

  function bindControls(root) {
    var search = root.querySelector('[data-scwb-studio-search]');
    if (search) search.addEventListener('input', function () { applyFilter(root); });
    list(root, '[data-scwb-studio-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        list(root, '[data-scwb-studio-filter]').forEach(function (b) { b.classList.toggle('is-active', b === button); });
        applyFilter(root);
      });
    });
    list(root, '[data-scwb-favorite]').forEach(function (button) {
      button.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        toggleFavorite(root, button.getAttribute('data-scwb-favorite'));
      });
    });
  }

  function init(root) {
    if (!root || root.getAttribute('data-scwb-ready') === 'true') return;
    root.setAttribute('data-scwb-ready', 'true');
    audit(root);
    bindControls(root);
    syncFavorites(root);
    applyFilter(root);
    var key = preferred(root);
    if (key) activate(root, key, { hash: false });
    finishActivation(root);
  }

  function initAll(scope) { list(scope || document, SELECTOR).forEach(init); }

  document.addEventListener('click', function (event) {
    var tab = event.target.closest('[data-scwb-primary-tab]');
    if (!tab || tab.disabled) return;
    var root = tab.closest(SELECTOR);
    if (!root) return;
    event.preventDefault();
    activate(root, tab.getAttribute('data-scwb-primary-tab'), { focus: true });
  });

  document.addEventListener('keydown', function (event) {
    var current = event.target.closest('[data-scwb-primary-tab]');
    if (!current || current.disabled) return;
    var root = current.closest(SELECTOR);
    if (!root) return;
    var available = tabs(root).filter(function (tab) { return !tab.closest('[data-scwb-tab-row]').hidden; });
    var index = available.indexOf(current);
    if (index < 0 || !available.length) return;
    var next = index;
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = (index + 1) % available.length;
    else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = (index - 1 + available.length) % available.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = available.length - 1;
    else return;
    event.preventDefault();
    activate(root, available[next].getAttribute('data-scwb-primary-tab'), { focus: true });
  });

  window.addEventListener('hashchange', function () {
    var key = hashStudio();
    if (!key) return;
    document.querySelectorAll(SELECTOR).forEach(function (root) { activate(root, key, { hash: false }); });
  });

  document.addEventListener('scwb:project-changed', function (event) {
    var detail = event.detail || {};
    var projectId = detail.projectId || (detail.project && detail.project.project_id) || '';
    if (!projectId) return;
    document.querySelectorAll(SELECTOR).forEach(function (root) {
      root.setAttribute('data-scwb-project', projectId);
      root.dispatchEvent(new CustomEvent('scwb:active-project-updated', { bubbles: true, detail: detail }));
    });
  });

  function start() { initAll(document); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();

  if ('MutationObserver' in window) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (!node || node.nodeType !== 1) return;
          if (node.matches && node.matches(SELECTOR)) init(node);
          if (node.querySelectorAll) initAll(node);
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  window.SCWBPrimaryRouter = {
    activate: activate,
    audit: audit,
    filter: applyFilter,
    init: init,
    expectedStudios: EXPECTED.slice(),
    version: VERSION
  };
})();
