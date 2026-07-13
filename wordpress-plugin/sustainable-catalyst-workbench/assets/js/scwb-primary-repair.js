(function () {
  'use strict';

  var SELECTOR = '[data-scwb-primary]';
  var EXPECTED = ['unified','projects','library','handoffs','reviews','research','embedded','devices','electronics','robotics','instrumentation','simulation','intelligence','runtime','visualization','experiments','documentation','recovery'];

  function list(root, selector) {
    return Array.prototype.slice.call(root.querySelectorAll(selector));
  }
  function tabs(root) { return list(root, '[data-scwb-primary-tab]:not([disabled])'); }
  function panels(root) { return list(root, '[data-scwb-primary-panel]'); }
  function storageKey(root) { return 'scwb-v301:last-studio:' + (root.getAttribute('data-scwb-project') || 'default'); }
  function byKey(items, attribute, key) {
    return items.find(function (item) { return item.getAttribute(attribute) === key; }) || null;
  }

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
    var interactive = mount.querySelector('button,input,select,textarea,canvas,svg,form,[role="button"],[data-scwb-v200],[data-scwb-v210],[data-scwb-v220],[data-scwb-v230],[data-scwb-v240],[data-scwb-v250],[data-scwb-v260],[data-scwb-v270],[data-scwb-v280],[data-scwb-v290],[data-scwb-v300],[data-scwb-v330],[data-scwb-v340],[data-scwb-v350],[data-scwb-v360]');
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
    root.dispatchEvent(new CustomEvent('scwb:interface-audited', { bubbles: true, detail: { studios: report } }));
    return report;
  }

  function announceVisible(panel, key) {
    var detail = { studio: key, panel: panel, state: panelState(panel) };
    panel.dispatchEvent(new CustomEvent('scwb:studio-activated', { bubbles: true, detail: detail }));
    panel.dispatchEvent(new CustomEvent('scwb:panel-visible', { bubbles: true, detail: detail }));
    window.dispatchEvent(new Event('resize'));
    window.setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 80);
    window.setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 240);
    if (window.ResizeObserver) {
      panel.querySelectorAll('canvas,svg,[data-chart],[data-plot]').forEach(function (node) {
        node.dispatchEvent(new CustomEvent('scwb:visual-resize', { bubbles: true, detail: detail }));
      });
    }
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
    if (root.getAttribute('data-scwb-remember') === 'true') {
      try { localStorage.setItem(storageKey(root), key); } catch (error) {}
    }
    if (options.hash !== false && window.history && window.history.replaceState) {
      var value = '#workbench-studio-' + encodeURIComponent(key);
      if (window.location.hash !== value) window.history.replaceState(null, '', value);
    }
    if (options.focus) selected.focus();
    updateTabState(root, key, panelState(visiblePanel));
    announceVisible(visiblePanel, key);
    return true;
  }

  function hashStudio() {
    var match = (window.location.hash || '').match(/^#workbench-studio-([a-z0-9_-]+)$/i);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function preferred(root) {
    var initial = hashStudio() || root.getAttribute('data-scwb-initial') || '';
    if (!hashStudio() && root.getAttribute('data-scwb-remember') === 'true') {
      try {
        var saved = localStorage.getItem(storageKey(root));
        if (saved) initial = saved;
      } catch (error) {}
    }
    var available = tabs(root).map(function (tab) { return tab.getAttribute('data-scwb-primary-tab'); });
    return available.indexOf(initial) >= 0 ? initial : available[0];
  }

  function finishActivation(root) {
    root.classList.remove('is-loading');
    root.classList.add('is-ready');
    root.setAttribute('aria-busy', 'false');
    var activation = root.querySelector('[data-scwb-activation]');
    if (activation) {
      activation.innerHTML = '<span aria-hidden="true">✓</span><span>Workbench interface activated.</span>';
      activation.classList.add('is-complete');
    }
    var status = root.querySelector('[data-scwb-primary-js-status]');
    if (status) status.textContent = 'Active · keyboard, hash, cache-safe, and dynamic routing enabled';
  }

  function init(root) {
    if (!root || root.getAttribute('data-scwb-ready') === 'true') return;
    root.setAttribute('data-scwb-ready', 'true');
    audit(root);
    var key = preferred(root);
    if (key) activate(root, key, { hash: false });
    finishActivation(root);
  }

  function initAll(scope) {
    list(scope || document, SELECTOR).forEach(init);
  }

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
    var available = tabs(root);
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

  function start() { initAll(document); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

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


  document.addEventListener('scwb:project-changed', function (event) {
    var detail = event.detail || {};
    var projectId = detail.projectId || (detail.project && detail.project.project_id) || '';
    if (!projectId) return;
    document.querySelectorAll(SELECTOR).forEach(function (root) {
      root.setAttribute('data-scwb-project', projectId);
      root.dispatchEvent(new CustomEvent('scwb:active-project-updated', { bubbles: true, detail: detail }));
    });
  });

  window.SCWBPrimaryRouter = {
    activate: activate,
    audit: audit,
    init: init,
    expectedStudios: EXPECTED.slice(),
    version: '3.5.0'
  };
})();
