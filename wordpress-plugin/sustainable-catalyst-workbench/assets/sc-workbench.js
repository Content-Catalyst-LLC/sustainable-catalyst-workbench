(function () {
  'use strict';

  function request(path, options) {
    var opts = options || {};
    opts.headers = Object.assign({
      'Content-Type': 'application/json',
      'X-WP-Nonce': SCWorkbench.nonce
    }, opts.headers || {});
    return fetch(SCWorkbench.restUrl + path, opts).then(function (response) {
      return response.json();
    });
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch];
    });
  }

  function renderTools(grid, data) {
    var tools = data.tools || data.fallback_tools || [];
    if (!tools.length) {
      grid.innerHTML = '<p class="scwb-muted">No tools are registered yet.</p>';
      return;
    }
    grid.innerHTML = tools.map(function (tool) {
      return '<article class="scwb-card">' +
        '<h3>' + escapeHtml(tool.title) + '</h3>' +
        '<p>' + escapeHtml(tool.description || tool.domain || '') + '</p>' +
        '<span class="scwb-badge">' + escapeHtml(tool.type || 'tool') + '</span>' +
        '</article>';
    }).join('');
  }

  function defaultInputForTool(toolId) {
    if (toolId === 'linear-system-solver') {
      return JSON.stringify({ matrix: [[2, 1], [1, 3]], vector: [1, 2] }, null, 2);
    }
    if (toolId === 'decision-matrix') {
      return JSON.stringify({
        criteria: [{ name: 'Impact', weight: 0.5 }, { name: 'Feasibility', weight: 0.3 }, { name: 'Risk', weight: 0.2, direction: 'lower_is_better' }],
        options: [{ name: 'Option A', scores: { Impact: 8, Feasibility: 7, Risk: 4 } }, { name: 'Option B', scores: { Impact: 6, Feasibility: 9, Risk: 2 } }]
      }, null, 2);
    }
    if (toolId === 'ai-governance-audit') {
      return JSON.stringify({ transparency: 3, human_oversight: 4, data_quality: 3, contestability: 2, harm_risk: 4 }, null, 2);
    }
    return JSON.stringify({ note: 'Enter tool inputs here.' }, null, 2);
  }

  function renderToolPanel(panel) {
    var toolId = panel.getAttribute('data-tool');
    var body = panel.querySelector('[data-scwb-body]');
    if (!toolId) {
      request('/tools').then(function (data) {
        body.innerHTML = '<div class="scwb-card-grid" data-grid></div>';
        renderTools(body.querySelector('[data-grid]'), data);
      });
      return;
    }

    body.innerHTML = '' +
      '<form class="scwb-tool-form" data-scwb-tool-form>' +
      '<p class="scwb-muted">Enter JSON inputs for this starter tool. Later versions can replace this with custom UI fields.</p>' +
      '<textarea rows="9" name="inputs">' + escapeHtml(defaultInputForTool(toolId)) + '</textarea>' +
      '<button class="scwb-button" type="submit">Run Tool</button>' +
      '</form>' +
      '<div class="scwb-result" data-scwb-tool-result style="display:none"></div>';

    var form = body.querySelector('[data-scwb-tool-form]');
    var result = body.querySelector('[data-scwb-tool-result]');
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      result.style.display = '';
      result.innerHTML = '<p class="scwb-loading">Running tool…</p>';
      var parsed;
      try {
        parsed = JSON.parse(form.elements.inputs.value);
      } catch (err) {
        result.innerHTML = '<div class="scwb-warning">Invalid JSON input.</div>';
        return;
      }
      request('/run', {
        method: 'POST',
        body: JSON.stringify({ tool_id: toolId, inputs: parsed })
      }).then(function (data) {
        result.innerHTML = '<pre>' + escapeHtml(JSON.stringify(data, null, 2)) + '</pre>';
      }).catch(function () {
        result.innerHTML = '<div class="scwb-warning">Could not reach the Workbench backend.</div>';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-scwb-tools]').forEach(function (panel) {
      var grid = panel.querySelector('[data-scwb-tools-grid]');
      request('/tools').then(function (data) { renderTools(grid, data); });
    });

    document.querySelectorAll('[data-scwb-panel]').forEach(renderToolPanel);

    document.querySelectorAll('[data-scwb-ai]').forEach(function (panel) {
      var form = panel.querySelector('[data-scwb-ai-form]');
      var result = panel.querySelector('[data-scwb-ai-result]');
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        var question = form.elements.question.value.trim();
        if (!question) return;
        result.innerHTML = '<p class="scwb-loading">Checking Sustainable Catalyst scope…</p>';
        request('/ask', {
          method: 'POST',
          body: JSON.stringify({
            question: question,
            mode: panel.getAttribute('data-mode') || 'library-guide',
            topic: panel.getAttribute('data-topic') || ''
          })
        }).then(function (data) {
          result.innerHTML = '<pre>' + escapeHtml(JSON.stringify(data, null, 2)) + '</pre>';
        }).catch(function () {
          result.innerHTML = '<div class="scwb-warning">Could not reach the Workbench backend.</div>';
        });
      });
    });
  });
}());
