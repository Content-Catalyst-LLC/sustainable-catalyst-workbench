(function (window, document) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, function (character) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[character];
    });
  }

  function normalizeRows(table) {
    const data = table && table.data;
    if (Array.isArray(data)) {
      if (!data.length) return { columns: table.columns || [], rows: [] };
      if (Array.isArray(data[0])) {
        const columns = table.columns || data[0].map(function (_, index) { return 'Column ' + (index + 1); });
        return { columns: columns, rows: data.map(function (row) {
          const item = {};
          columns.forEach(function (column, index) { item[column] = row[index]; });
          return item;
        }) };
      }
      if (typeof data[0] === 'object') {
        const columns = table.columns || Array.from(data.reduce(function (set, row) {
          Object.keys(row || {}).forEach(function (key) { set.add(key); });
          return set;
        }, new Set()));
        return { columns: columns, rows: data };
      }
      return { columns: ['Value'], rows: data.map(function (value) { return { Value: value }; }) };
    }
    if (data && typeof data === 'object') {
      const keys = Object.keys(data);
      const lengths = keys.map(function (key) { return Array.isArray(data[key]) ? data[key].length : 1; });
      const count = Math.max.apply(null, lengths.concat([0]));
      const rows = [];
      for (let index = 0; index < count; index += 1) {
        const row = {};
        keys.forEach(function (key) { row[key] = Array.isArray(data[key]) ? data[key][index] : data[key]; });
        rows.push(row);
      }
      return { columns: keys, rows: rows };
    }
    return { columns: ['Value'], rows: data == null ? [] : [{ Value: data }] };
  }

  function tableCard(table) {
    const normalized = normalizeRows(table || {});
    const article = document.createElement('article');
    article.className = 'scwb-result-card scwb-result-table-card';
    const title = document.createElement('h4');
    title.textContent = table.name || 'Result table';
    article.appendChild(title);
    const wrap = document.createElement('div');
    wrap.className = 'scwb-result-table-wrap';
    const html = '<table><thead><tr>' + normalized.columns.map(function (column) { return '<th>' + escapeHtml(column) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      normalized.rows.slice(0, 500).map(function (row) {
        return '<tr>' + normalized.columns.map(function (column) {
          const value = row ? row[column] : '';
          const display = typeof value === 'object' && value !== null ? JSON.stringify(value) : value;
          return '<td>' + escapeHtml(display) + '</td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
    wrap.innerHTML = html || '<p>No rows returned.</p>';
    article.appendChild(wrap);
    if (normalized.rows.length > 500) {
      const note = document.createElement('p');
      note.className = 'scwb-result-note';
      note.textContent = 'Showing the first 500 of ' + normalized.rows.length + ' rows.';
      article.appendChild(note);
    }
    return article;
  }

  function dimensions(spec) {
    return { width: Math.max(420, Number(spec.width) || 760), height: Math.max(240, Number(spec.height) || 380) };
  }

  function svgChart(chart) {
    const spec = chart.spec || {};
    const kind = String(spec.type || spec.kind || 'line').toLowerCase();
    const dims = dimensions(spec);
    const pad = { left: 58, right: 24, top: 30, bottom: 48 };
    const width = dims.width;
    const height = dims.height;
    const x = Array.isArray(spec.x) ? spec.x : [];
    let series = Array.isArray(spec.series) ? spec.series : [];
    if (!series.length && Array.isArray(spec.y)) series = [{ name: spec.label || 'Series', values: spec.y }];
    const values = [];
    series.forEach(function (item) { (item.values || []).forEach(function (value) { if (Number.isFinite(Number(value))) values.push(Number(value)); }); });
    const yMin = spec.yMin != null ? Number(spec.yMin) : Math.min.apply(null, values.concat([0]));
    const yMaxRaw = spec.yMax != null ? Number(spec.yMax) : Math.max.apply(null, values.concat([1]));
    const yMax = yMaxRaw === yMin ? yMin + 1 : yMaxRaw;
    const count = Math.max(x.length, series.reduce(function (max, item) { return Math.max(max, (item.values || []).length); }, 0), 1);
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const sx = function (index) { return pad.left + (count <= 1 ? plotW / 2 : index * plotW / (count - 1)); };
    const sy = function (value) { return pad.top + plotH - ((Number(value) - yMin) / (yMax - yMin)) * plotH; };
    const parts = [
      '<svg viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="' + escapeHtml(chart.name || 'Chart') + '">',
      '<rect x="0" y="0" width="' + width + '" height="' + height + '" fill="#080808"/>',
      '<line x1="' + pad.left + '" y1="' + pad.top + '" x2="' + pad.left + '" y2="' + (height - pad.bottom) + '" stroke="#5b6d57"/>',
      '<line x1="' + pad.left + '" y1="' + (height - pad.bottom) + '" x2="' + (width - pad.right) + '" y2="' + (height - pad.bottom) + '" stroke="#5b6d57"/>'
    ];
    for (let tick = 0; tick <= 4; tick += 1) {
      const value = yMin + (yMax - yMin) * tick / 4;
      const yPos = sy(value);
      parts.push('<line x1="' + pad.left + '" y1="' + yPos + '" x2="' + (width - pad.right) + '" y2="' + yPos + '" stroke="#1c271b"/>');
      parts.push('<text x="' + (pad.left - 8) + '" y="' + (yPos + 4) + '" text-anchor="end" fill="#a9b7a5" font-size="11">' + escapeHtml(Number(value.toFixed(4))) + '</text>');
    }
    series.forEach(function (item, seriesIndex) {
      const vals = item.values || [];
      if (kind === 'bar') {
        const groupWidth = plotW / Math.max(count, 1);
        const barWidth = Math.max(4, groupWidth / Math.max(series.length + 1, 2));
        vals.forEach(function (value, index) {
          const base = sy(Math.max(0, yMin));
          const top = sy(Number(value));
          const left = pad.left + index * groupWidth + 4 + seriesIndex * barWidth;
          parts.push('<rect x="' + left + '" y="' + Math.min(base, top) + '" width="' + (barWidth - 2) + '" height="' + Math.abs(base - top) + '" fill="none" stroke="#39ff14" stroke-width="2" opacity="' + (1 - seriesIndex * 0.15) + '"/>');
        });
      } else {
        const points = vals.map(function (value, index) { return sx(index) + ',' + sy(value); }).join(' ');
        if (kind !== 'scatter') parts.push('<polyline points="' + points + '" fill="none" stroke="#39ff14" stroke-width="2.5" opacity="' + (1 - seriesIndex * 0.15) + '"/>');
        vals.forEach(function (value, index) { parts.push('<circle cx="' + sx(index) + '" cy="' + sy(value) + '" r="3.5" fill="#050505" stroke="#b6ff9c" stroke-width="2"/>'); });
      }
    });
    const labelStep = Math.max(1, Math.ceil(count / 8));
    for (let index = 0; index < count; index += labelStep) {
      const label = x[index] != null ? x[index] : index + 1;
      parts.push('<text x="' + sx(index) + '" y="' + (height - pad.bottom + 20) + '" text-anchor="middle" fill="#a9b7a5" font-size="11">' + escapeHtml(label) + '</text>');
    }
    parts.push('</svg>');
    const article = document.createElement('article');
    article.className = 'scwb-result-card scwb-result-chart-card';
    article.innerHTML = '<h4>' + escapeHtml(chart.name || spec.title || 'Chart') + '</h4><div class="scwb-result-svg">' + parts.join('') + '</div>';
    return article;
  }

  function imageCard(chart) {
    const article = document.createElement('article');
    article.className = 'scwb-result-card scwb-result-chart-card';
    const title = document.createElement('h4');
    title.textContent = chart.name || 'Chart';
    article.appendChild(title);
    if (chart.kind === 'bitmap' && chart.image) {
      const canvas = document.createElement('canvas');
      canvas.width = chart.image.width || 1008;
      canvas.height = chart.image.height || 1008;
      canvas.className = 'scwb-result-canvas';
      canvas.getContext('2d').drawImage(chart.image, 0, 0, canvas.width, canvas.height);
      article.appendChild(canvas);
    } else {
      const image = document.createElement('img');
      image.src = chart.dataUrl || '';
      image.alt = chart.name || 'Generated chart';
      image.loading = 'lazy';
      article.appendChild(image);
    }
    return article;
  }

  function createRenderer(panel) {
    function clear() {
      if (panel) panel.innerHTML = '<p class="scwb-code-empty">Run code that returns a table or chart to populate this workspace.</p>';
    }
    function render(result, append) {
      if (!panel) return;
      if (!append) panel.innerHTML = '';
      const tables = (result && result.tables) || [];
      const charts = (result && result.charts) || [];
      if (!tables.length && !charts.length) {
        if (!append) clear();
        return;
      }
      tables.forEach(function (table) { panel.appendChild(tableCard(table)); });
      charts.forEach(function (chart) {
        panel.appendChild(chart.kind === 'spec' ? svgChart(chart) : imageCard(chart));
      });
    }
    clear();
    return { clear: clear, render: render };
  }

  root.ChartRenderer = { create: createRenderer, normalizeRows: normalizeRows };
})(window, document);
