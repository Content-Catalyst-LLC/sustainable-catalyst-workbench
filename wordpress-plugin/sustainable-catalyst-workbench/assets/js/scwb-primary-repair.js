(function () {
  'use strict';

  function activate(root, key) {
    root.querySelectorAll('[data-scwb-primary-tab]').forEach(function (tab) {
      var active = tab.getAttribute('data-scwb-primary-tab') === key;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });

    root.querySelectorAll('[data-scwb-primary-panel]').forEach(function (panel) {
      var active = panel.getAttribute('data-scwb-primary-panel') === key;
      panel.classList.toggle('is-active', active);
      panel.hidden = !active;
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scwb-primary]').forEach(function (root) {
      root.querySelectorAll('[data-scwb-primary-tab]').forEach(function (tab) {
        tab.addEventListener('click', function () {
          activate(root, tab.getAttribute('data-scwb-primary-tab'));
        });
      });
    });
  });
})();
