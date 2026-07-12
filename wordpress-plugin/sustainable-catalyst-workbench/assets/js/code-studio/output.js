(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function createOutput(panel) {
    const entries = [];

    function render() {
      if (!panel) return;
      if (!entries.length) {
        panel.innerHTML = '<p class="scwb-code-empty">No execution or project events yet.</p>';
        return;
      }
      panel.innerHTML = entries.slice().reverse().map(function (entry) {
        return '<article class="scwb-code-event scwb-code-event-' + entry.level + '">' +
          '<time>' + entry.time + '</time>' +
          '<strong>' + escapeHtml(entry.title) + '</strong>' +
          '<pre>' + escapeHtml(entry.detail) + '</pre>' +
          '</article>';
      }).join('');
    }

    function escapeHtml(value) {
      return String(value == null ? '' : value).replace(/[&<>"']/g, function (character) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character];
      });
    }

    return {
      add: function (title, detail, level) {
        entries.push({
          title: title || 'Workbench event',
          detail: detail || '',
          level: level || 'info',
          time: new Date().toLocaleTimeString()
        });
        if (entries.length > 100) entries.shift();
        render();
      },
      clear: function () { entries.length = 0; render(); },
      render: render,
      entries: function () { return entries.slice(); }
    };
  }

  root.Output = { create: createOutput };
})(window);
