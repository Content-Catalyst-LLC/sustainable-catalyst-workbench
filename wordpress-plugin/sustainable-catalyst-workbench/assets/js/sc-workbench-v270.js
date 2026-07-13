(function () {
  'use strict';
  const CONFIG = window.SCWBV270 || { version: '2.7.0', runnerDefaultUrl: 'http://127.0.0.1:8787', storagePrefix: 'scwb-v270:' };
  const NS = 'http://www.w3.org/2000/svg';

  function esc(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char])); }
  function finite(value, fallback) { const number = Number(value); return Number.isFinite(number) ? number : fallback; }
  function round(value, digits) { const factor = Math.pow(10, digits == null ? 6 : digits); return Math.round(value * factor) / factor; }
  function clamp(value, lower, upper) { return Math.min(upper, Math.max(lower, value)); }
  function parseJSON(value, fallback) { try { return JSON.parse(value); } catch (error) { return fallback; } }
  function numbers(value) { return String(value || '').split(/[\s,;]+/).map(Number).filter(Number.isFinite); }
  function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0; }
  function median(values) { if (!values.length) return 0; const sorted = values.slice().sort((a, b) => a - b); const middle = Math.floor(sorted.length / 2); return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2; }
  function standardDeviation(values) { if (values.length < 2) return 0; const average = mean(values); return Math.sqrt(values.reduce((sum, value) => sum + Math.pow(value - average, 2), 0) / values.length); }
  function quantile(values, probability) { if (!values.length) return 0; const sorted = values.slice().sort((a, b) => a - b), position = (sorted.length - 1) * probability, lower = Math.floor(position), upper = Math.ceil(position); return lower === upper ? sorted[lower] : sorted[lower] * (upper - position) + sorted[upper] * (position - lower); }
  function storageKey(root) { return CONFIG.storagePrefix + root.dataset.scwbV270Project + ':' + root.dataset.scwbV270Panel; }
  function fields(root) { const data = {}; root.querySelectorAll('[data-scwb-v270-field]').forEach((node) => { data[node.dataset.scwbV270Field] = node.value; }); return data; }
  function status(root, text) { const node = root.querySelector('[data-scwb-v270-status]'); if (node) node.textContent = text; }
  function results(root, record) { root._scwbV270Last = record; const node = root.querySelector('[data-scwb-v270-results]'); if (node) node.innerHTML = '<pre>' + esc(JSON.stringify(record, null, 2)) + '</pre>'; }
  function chartNode(root) { return root.querySelector('[data-scwb-v270-chart]'); }

  function parseCSV(text) {
    const rows = String(text || '').trim().split(/\r?\n/).filter((line) => line.trim()).map((line) => line.split(',').map((cell) => cell.trim()));
    if (!rows.length) return { headers: [], rows: [] };
    const firstNumeric = rows[0].every((cell) => Number.isFinite(Number(cell)));
    const headers = firstNumeric ? rows[0].map((value, index) => 'column_' + (index + 1)) : rows.shift().map((value, index) => value || 'column_' + (index + 1));
    return { headers, rows: rows.map((cells) => { const record = {}; headers.forEach((header, index) => { const numeric = Number(cells[index]); record[header] = Number.isFinite(numeric) ? numeric : (cells[index] || ''); }); return record; }) };
  }

  function extent(values) {
    const finiteValues = values.filter(Number.isFinite);
    if (!finiteValues.length) return [0, 1];
    let lower = Math.min.apply(null, finiteValues), upper = Math.max.apply(null, finiteValues);
    if (lower === upper) { const pad = Math.abs(lower || 1) * 0.1; lower -= pad; upper += pad; }
    return [lower, upper];
  }

  function chartScales(xValues, yValues, width, height, margins) {
    const xExtent = extent(xValues), yExtent = extent(yValues), xPad = (xExtent[1] - xExtent[0]) * 0.04, yPad = (yExtent[1] - yExtent[0]) * 0.08;
    const xMin = xExtent[0] - xPad, xMax = xExtent[1] + xPad, yMin = yExtent[0] - yPad, yMax = yExtent[1] + yPad;
    return {
      x: (value) => margins.left + ((value - xMin) / (xMax - xMin || 1)) * (width - margins.left - margins.right),
      y: (value) => height - margins.bottom - ((value - yMin) / (yMax - yMin || 1)) * (height - margins.top - margins.bottom),
      xMin, xMax, yMin, yMax,
    };
  }

  function gridMarkup(scales, width, height, margins, xLabel, yLabel, title) {
    let lines = '', labels = '';
    for (let index = 0; index <= 5; index += 1) {
      const px = margins.left + index * (width - margins.left - margins.right) / 5;
      const py = margins.top + index * (height - margins.top - margins.bottom) / 5;
      const xv = scales.xMin + index * (scales.xMax - scales.xMin) / 5;
      const yv = scales.yMax - index * (scales.yMax - scales.yMin) / 5;
      lines += '<line x1="' + px + '" y1="' + margins.top + '" x2="' + px + '" y2="' + (height - margins.bottom) + '" stroke="#dbe3e7" stroke-width="1"/>';
      lines += '<line x1="' + margins.left + '" y1="' + py + '" x2="' + (width - margins.right) + '" y2="' + py + '" stroke="#dbe3e7" stroke-width="1"/>';
      labels += '<text x="' + px + '" y="' + (height - margins.bottom + 22) + '" text-anchor="middle" font-size="11" fill="#52616a">' + esc(round(xv, 3)) + '</text>';
      labels += '<text x="' + (margins.left - 10) + '" y="' + (py + 4) + '" text-anchor="end" font-size="11" fill="#52616a">' + esc(round(yv, 3)) + '</text>';
    }
    return '<rect width="100%" height="100%" fill="#ffffff"/>' +
      '<text x="' + margins.left + '" y="24" font-size="17" font-weight="800" fill="#13212a">' + esc(title) + '</text>' + lines + labels +
      '<line x1="' + margins.left + '" y1="' + (height - margins.bottom) + '" x2="' + (width - margins.right) + '" y2="' + (height - margins.bottom) + '" stroke="#566771" stroke-width="1.5"/>' +
      '<line x1="' + margins.left + '" y1="' + margins.top + '" x2="' + margins.left + '" y2="' + (height - margins.bottom) + '" stroke="#566771" stroke-width="1.5"/>' +
      '<text x="' + ((margins.left + width - margins.right) / 2) + '" y="' + (height - 8) + '" text-anchor="middle" font-size="12" font-weight="700" fill="#33434c">' + esc(xLabel) + '</text>' +
      '<text transform="translate(16 ' + ((margins.top + height - margins.bottom) / 2) + ') rotate(-90)" text-anchor="middle" font-size="12" font-weight="700" fill="#33434c">' + esc(yLabel) + '</text>';
  }

  function wrapSVG(title, xLabel, yLabel, xValues, yValues, mark, description) {
    const width = 820, height = 440, margins = { top: 48, right: 24, bottom: 58, left: 74 }, scales = chartScales(xValues, yValues, width, height, margins);
    const body = typeof mark === 'function' ? mark(scales, width, height, margins) : mark;
    return '<svg xmlns="' + NS + '" viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-labelledby="scwb-v270-svg-title scwb-v270-svg-desc">' +
      '<title id="scwb-v270-svg-title">' + esc(title) + '</title><desc id="scwb-v270-svg-desc">' + esc(description || '') + '</desc>' +
      gridMarkup(scales, width, height, margins, xLabel, yLabel, title) + body + '</svg>';
  }

  function summary(values) {
    return { count: values.length, minimum: round(Math.min.apply(null, values)), maximum: round(Math.max.apply(null, values)), mean: round(mean(values)), median: round(median(values)), standardDeviation: round(standardDeviation(values)), q05: round(quantile(values, 0.05)), q95: round(quantile(values, 0.95)), first: round(values[0]), last: round(values[values.length - 1]), netChange: round(values[values.length - 1] - values[0]) };
  }

  function accessibleDescription(title, type, values, units) {
    if (!values.length) return title + ' contains no valid numeric observations.';
    const stats = summary(values), unit = units ? ' ' + units : '', direction = stats.last > stats.first ? 'increases' : stats.last < stats.first ? 'decreases' : 'ends unchanged';
    return title + ' is a ' + type + ' visualization with ' + stats.count + ' observations. The values range from ' + stats.minimum + unit + ' to ' + stats.maximum + unit + '. The series ' + direction + ' overall from ' + stats.first + unit + ' to ' + stats.last + unit + '. The mean is ' + stats.mean + unit + ' and the median is ' + stats.median + unit + '.';
  }

  function histogram(values, binCount) {
    const bounds = extent(values), lower = bounds[0], upper = bounds[1], count = clamp(Math.floor(binCount), 2, 100), width = (upper - lower) / count || 1;
    const bins = Array.from({ length: count }, (_, index) => ({ x: lower + (index + 0.5) * width, lower: lower + index * width, upper: lower + (index + 1) * width, y: 0 }));
    values.forEach((value) => { const index = Math.min(count - 1, Math.max(0, Math.floor((value - lower) / width))); bins[index].y += 1; });
    return bins;
  }

  function spectrum(values) {
    const source = values.slice(0, 512), length = source.length, output = [];
    if (length < 2) return output;
    const average = mean(source);
    for (let k = 0; k <= Math.floor(length / 2); k += 1) {
      let real = 0, imaginary = 0;
      for (let n = 0; n < length; n += 1) {
        const sample = source[n] - average, angle = -2 * Math.PI * k * n / length;
        real += sample * Math.cos(angle); imaginary += sample * Math.sin(angle);
      }
      output.push({ x: k / length, y: Math.sqrt(real * real + imaginary * imaginary) * 2 / length });
    }
    return output;
  }

  function renderXY(root, spec) {
    const xValues = spec.points.map((point) => point.x), yValues = spec.points.map((point) => point.y), plottedY = ['bar', 'histogram', 'spectrum'].includes(spec.type) ? yValues.concat([0]) : yValues, description = accessibleDescription(spec.title, spec.type, yValues, spec.units);
    const svg = wrapSVG(spec.title, spec.xLabel, spec.yLabel, xValues, plottedY, (scales, width, height, margins) => {
      if (spec.type === 'bar' || spec.type === 'histogram' || spec.type === 'spectrum') {
        const available = width - margins.left - margins.right, barWidth = Math.max(2, available / Math.max(1, spec.points.length) * 0.72);
        return spec.points.map((point) => { const baseline = scales.y(0), valueY = scales.y(point.y), top = Math.min(baseline, valueY), heightValue = Math.abs(valueY - baseline); return '<rect x="' + (scales.x(point.x) - barWidth / 2) + '" y="' + top + '" width="' + barWidth + '" height="' + heightValue + '" fill="#8b1e2d" opacity=".82"><title>' + esc(point.x + ': ' + point.y) + '</title></rect>'; }).join('');
      }
      if (spec.type === 'scatter' || spec.type === 'spatial') return spec.points.map((point) => '<circle cx="' + scales.x(point.x) + '" cy="' + scales.y(point.y) + '" r="4" fill="#8b1e2d" opacity=".84"><title>' + esc(point.x + ', ' + point.y) + '</title></circle>').join('');
      const path = spec.points.map((point, index) => (index ? 'L' : 'M') + scales.x(point.x) + ',' + scales.y(point.y)).join(' ');
      return '<path d="' + path + '" fill="none" stroke="#8b1e2d" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>' + spec.points.map((point) => '<circle cx="' + scales.x(point.x) + '" cy="' + scales.y(point.y) + '" r="2.8" fill="#ffffff" stroke="#8b1e2d" stroke-width="1.5"><title>' + esc(point.x + ', ' + point.y) + '</title></circle>').join('');
    }, description);
    const node = chartNode(root); node.innerHTML = svg + '<div class="scwb-v270__a11y"><strong>Accessible description:</strong> ' + esc(description) + '</div>'; root._scwbV270SVG = svg;
    return description;
  }

  function analyzeVisualization(root, data) {
    const parsed = parseCSV(data.data), rows = parsed.rows, first = parsed.headers[0], second = parsed.headers[1] || parsed.headers[0];
    let points = rows.map((row, index) => ({ x: finite(row[first], index), y: finite(row[second], NaN) })).filter((point) => Number.isFinite(point.y)), type = data.chart_type;
    if (!points.length) throw new Error('No numeric visualization records were found.');
    if (type === 'histogram') points = histogram(points.map((point) => point.y), finite(data.bins, 12));
    if (type === 'spectrum') points = spectrum(points.map((point) => point.y));
    const description = renderXY(root, { title: data.title, type, xLabel: type === 'spectrum' ? 'Normalized frequency' : data.x_label, yLabel: type === 'histogram' ? 'Count' : type === 'spectrum' ? 'Amplitude' : data.y_label, units: data.units, points });
    const values = points.map((point) => point.y), record = { ok: true, schema: 'sc-workbench-scientific-visualization/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), chartType: type, sourceColumns: parsed.headers, pointCount: points.length, statistics: summary(values), accessibleDescription: description, exportFormats: ['svg', 'png', 'json', 'csv'], data: points.slice(0, 5000), dataTruncated: points.length > 5000 };
    results(root, record); status(root, 'Figure rendered');
  }

  function metricStatus(metric) {
    const value = finite(metric.value, 0);
    if ((Number.isFinite(Number(metric.critical_low)) && value < Number(metric.critical_low)) || (Number.isFinite(Number(metric.critical_high)) && value > Number(metric.critical_high))) return 'critical';
    if ((Number.isFinite(Number(metric.warning_low)) && value < Number(metric.warning_low)) || (Number.isFinite(Number(metric.warning_high)) && value > Number(metric.warning_high))) return 'warning';
    return 'normal';
  }

  function renderDashboard(root, data) {
    const metrics = parseJSON(data.metrics, []); if (!Array.isArray(metrics) || !metrics.length) throw new Error('Metrics JSON must contain at least one metric.');
    root.dataset.density = data.density;
    const evaluated = metrics.map((metric) => Object.assign({}, metric, { status: metricStatus(metric) }));
    const trend = numbers(data.trend), cards = evaluated.map((metric) => '<article class="scwb-v270__metric" data-status="' + esc(metric.status) + '"><span class="scwb-v270__metric-label">' + esc(metric.label || metric.key) + '</span><strong class="scwb-v270__metric-value">' + esc(round(finite(metric.value, 0))) + ' ' + esc(metric.units || '') + '</strong><span class="scwb-v270__metric-status">' + esc(metric.status) + (Number.isFinite(Number(metric.target)) ? ' · target ' + esc(metric.target) : '') + '</span></article>').join('');
    const trendPoints = trend.map((value, index) => ({ x: index, y: value }));
    const description = data.title + ' contains ' + evaluated.length + ' metrics: ' + evaluated.filter((metric) => metric.status === 'critical').length + ' critical, ' + evaluated.filter((metric) => metric.status === 'warning').length + ' warning, and ' + evaluated.filter((metric) => metric.status === 'normal').length + ' normal.';
    const node = chartNode(root); node.innerHTML = '<h3>' + esc(data.title) + '</h3><div class="scwb-v270__dashboard-grid">' + cards + '</div><div data-scwb-v270-dashboard-trend></div><div class="scwb-v270__a11y"><strong>Accessible description:</strong> ' + esc(description) + '</div>';
    if (trendPoints.length > 1) { const svg = wrapSVG('Recent metric trend', 'Observation', 'Value', trendPoints.map((point) => point.x), trend, (scales) => '<path d="' + trendPoints.map((point, index) => (index ? 'L' : 'M') + scales.x(point.x) + ',' + scales.y(point.y)).join(' ') + '" fill="none" stroke="#8b1e2d" stroke-width="3"/>', accessibleDescription('Recent metric trend', 'line', trend, '')); node.querySelector('[data-scwb-v270-dashboard-trend]').innerHTML = svg; root._scwbV270SVG = svg; }
    const counts = { normal: evaluated.filter((metric) => metric.status === 'normal').length, warning: evaluated.filter((metric) => metric.status === 'warning').length, critical: evaluated.filter((metric) => metric.status === 'critical').length };
    results(root, { ok: counts.critical === 0, schema: 'sc-workbench-engineering-dashboard/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), title: data.title, overallStatus: counts.critical ? 'critical' : counts.warning ? 'warning' : 'normal', statusCounts: counts, metrics: evaluated, accessibleDescription: description }); status(root, 'Dashboard built');
  }

  function interactivePoints(data) {
    const a = finite(data.parameter_a, 1), b = finite(data.parameter_b, 2), c = finite(data.parameter_c, 0), lower = finite(data.x_min, 0), upper = finite(data.x_max, 10), samples = clamp(Math.floor(finite(data.samples, 101)), 10, 1000), points = [];
    for (let index = 0; index < samples; index += 1) {
      const x = lower + (upper - lower) * index / (samples - 1), y = data.model === 'sine' ? a * Math.sin(b * x + c) : data.model === 'linear' ? a * x + b : data.model === 'quadratic' ? a * x * x + b * x + c : a * (1 - Math.exp(-x / Math.max(0.000001, Math.abs(b)))) + c;
      points.push({ x, y });
    }
    return points;
  }

  function renderInteractive(root, data) {
    const points = interactivePoints(data), description = renderXY(root, { title: data.title, type: 'line', xLabel: 'Independent variable', yLabel: 'Model output', units: '', points });
    results(root, { ok: true, schema: 'sc-workbench-interactive-chart/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), model: data.model, parameters: { a: finite(data.parameter_a, 1), b: finite(data.parameter_b, 2), c: finite(data.parameter_c, 0) }, domain: [finite(data.x_min, 0), finite(data.x_max, 10)], samples: points.length, statistics: summary(points.map((point) => point.y)), accessibleDescription: description, points: points.slice(0, 1000) }); status(root, 'Interactive chart updated');
  }

  function renderValidation(root, data) {
    const parsed = parseCSV(data.data), headers = parsed.headers, xKey = headers[0], observedKey = headers[1], predictedKey = headers[2], uncertaintyKey = headers[3];
    const points = parsed.rows.map((row, index) => ({ x: finite(row[xKey], index), observed: finite(row[observedKey], NaN), predicted: finite(row[predictedKey], NaN), uncertainty: Math.max(0, finite(row[uncertaintyKey], 0)) })).filter((point) => Number.isFinite(point.observed) && Number.isFinite(point.predicted));
    if (points.length < 2) throw new Error('At least two observed and predicted records are required.');
    const sigma = Math.max(0.01, finite(data.sigma_multiplier, 1.96)), xValues = points.map((point) => point.x), allY = points.flatMap((point) => [point.observed, point.predicted - sigma * point.uncertainty, point.predicted + sigma * point.uncertainty]);
    const residuals = points.map((point) => point.observed - point.predicted), rmse = Math.sqrt(mean(residuals.map((value) => value * value))), mae = mean(residuals.map(Math.abs)), bias = mean(residuals), covered = points.filter((point) => point.observed >= point.predicted - sigma * point.uncertainty && point.observed <= point.predicted + sigma * point.uncertainty).length;
    const description = data.title + ' compares ' + points.length + ' observed and predicted records. RMSE is ' + round(rmse) + ', mean absolute error is ' + round(mae) + ', bias is ' + round(bias) + ', and ' + covered + ' observations fall inside the configured uncertainty band.';
    const svg = wrapSVG(data.title, 'Independent variable', 'Response', xValues, allY, (scales) => {
      const upper = points.map((point, index) => (index ? 'L' : 'M') + scales.x(point.x) + ',' + scales.y(point.predicted + sigma * point.uncertainty)).join(' '), lower = points.slice().reverse().map((point) => 'L' + scales.x(point.x) + ',' + scales.y(point.predicted - sigma * point.uncertainty)).join(' '), predicted = points.map((point, index) => (index ? 'L' : 'M') + scales.x(point.x) + ',' + scales.y(point.predicted)).join(' '), observed = points.map((point, index) => (index ? 'L' : 'M') + scales.x(point.x) + ',' + scales.y(point.observed)).join(' ');
      return '<path d="' + upper + ' ' + lower + ' Z" fill="#8b1e2d" opacity=".14"/><path d="' + predicted + '" fill="none" stroke="#8b1e2d" stroke-width="2.5"/><path d="' + observed + '" fill="none" stroke="#1e667d" stroke-width="2.5" stroke-dasharray="6 4"/>' + points.map((point) => '<circle cx="' + scales.x(point.x) + '" cy="' + scales.y(point.observed) + '" r="3" fill="#1e667d"/>').join('');
    }, description);
    chartNode(root).innerHTML = svg + '<div class="scwb-v270__a11y"><strong>Accessible description:</strong> ' + esc(description) + '</div>'; root._scwbV270SVG = svg;
    results(root, { ok: rmse <= Math.max(0, finite(data.rmse_limit, Infinity)), schema: 'sc-workbench-validation-overlay/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), sigmaMultiplier: sigma, acceptance: { rmseLimit: finite(data.rmse_limit, null), pass: rmse <= finite(data.rmse_limit, Infinity) }, metrics: { rmse: round(rmse), mae: round(mae), bias: round(bias), coverageFraction: round(covered / points.length), coverageCount: covered, sampleCount: points.length }, accessibleDescription: description, points }); status(root, 'Validation overlay rendered');
  }

  function renderState(root, data) {
    const nodes = parseJSON(data.nodes, []), edges = parseJSON(data.edges, []); if (!Array.isArray(nodes) || !nodes.length) throw new Error('Nodes JSON must contain at least one node.');
    const known = new Set(nodes.map((node) => String(node.id))), unknownEdges = edges.filter((edge) => !known.has(String(edge.source)) || !known.has(String(edge.target))), width = 820, height = 440, radius = Math.min(155, 44 * nodes.length), centerX = width / 2, centerY = height / 2 + 15;
    const positioned = nodes.map((node, index) => Object.assign({}, node, { x: centerX + radius * Math.cos(2 * Math.PI * index / nodes.length - Math.PI / 2), y: centerY + radius * Math.sin(2 * Math.PI * index / nodes.length - Math.PI / 2) })), map = new Map(positioned.map((node) => [String(node.id), node]));
    const colors = { normal: '#137447', warning: '#9a6200', critical: '#a32929', offline: '#5f6870', unknown: '#667884' };
    let marks = edges.map((edge) => { const source = map.get(String(edge.source)), target = map.get(String(edge.target)); if (!source || !target) return ''; return '<line x1="' + source.x + '" y1="' + source.y + '" x2="' + target.x + '" y2="' + target.y + '" stroke="#82929a" stroke-width="2" marker-end="url(#arrow)"/><text x="' + ((source.x + target.x) / 2) + '" y="' + ((source.y + target.y) / 2 - 5) + '" text-anchor="middle" font-size="10" fill="#52616a">' + esc(edge.relation || '') + '</text>'; }).join('');
    marks += positioned.map((node) => '<g><circle cx="' + node.x + '" cy="' + node.y + '" r="34" fill="#fff" stroke="' + (colors[node.state] || colors.unknown) + '" stroke-width="5"/><text x="' + node.x + '" y="' + (node.y - 3) + '" text-anchor="middle" font-size="11" font-weight="800" fill="#13212a">' + esc(node.label || node.id) + '</text><text x="' + node.x + '" y="' + (node.y + 13) + '" text-anchor="middle" font-size="10" fill="#52616a">' + esc(node.state || 'unknown') + '</text></g>').join('');
    const counts = {}; nodes.forEach((node) => { const state = node.state || 'unknown'; counts[state] = (counts[state] || 0) + 1; });
    const description = data.title + ' contains ' + nodes.length + ' nodes and ' + edges.length + ' directed connections. State counts are ' + Object.keys(counts).map((key) => key + ': ' + counts[key]).join(', ') + '.';
    const svg = '<svg xmlns="' + NS + '" viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-labelledby="scwb-v270-state-title scwb-v270-state-desc"><title id="scwb-v270-state-title">' + esc(data.title) + '</title><desc id="scwb-v270-state-desc">' + esc(description) + '</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#82929a"/></marker></defs><rect width="100%" height="100%" fill="#fff"/><text x="30" y="28" font-size="17" font-weight="800" fill="#13212a">' + esc(data.title) + '</text>' + marks + '</svg>';
    chartNode(root).innerHTML = svg + '<div class="scwb-v270__a11y"><strong>Accessible description:</strong> ' + esc(description) + '</div>'; root._scwbV270SVG = svg;
    results(root, { ok: unknownEdges.length === 0, schema: 'sc-workbench-system-state-view/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), nodeCount: nodes.length, edgeCount: edges.length, statusCounts: counts, unknownEdges, nodes, edges, accessibleDescription: description }); status(root, 'System-state view rendered');
  }

  function renderExport(root, data) {
    const values = numbers(data.values); if (!values.length) throw new Error('Enter at least one numeric value.');
    const points = values.map((value, index) => ({ x: index + 1, y: value })), type = data.chart_type === 'state' ? 'line' : data.chart_type;
    const description = renderXY(root, { title: data.title, type, xLabel: data.x_label, yLabel: data.y_label, units: data.units, points: type === 'histogram' ? histogram(values, 10) : type === 'spectrum' ? spectrum(values) : points });
    const tableRows = points.slice(0, 100).map((point) => '<tr><td>' + point.x + '</td><td>' + esc(round(point.y)) + '</td></tr>').join('');
    chartNode(root).insertAdjacentHTML('beforeend', '<table class="scwb-v270__table"><thead><tr><th>Observation</th><th>Value ' + esc(data.units || '') + '</th></tr></thead><tbody>' + tableRows + '</tbody></table>');
    results(root, { ok: true, schema: 'sc-workbench-accessible-visual-export/1.0', version: CONFIG.version, generatedAt: new Date().toISOString(), title: data.title, chartType: data.chart_type, accessibleDescription: description, dataTable: points, exports: { svg: true, png: true, json: true, csv: true }, accessibilityChecklist: ['Visible figure title', 'Programmatic SVG title and description', 'Text description', 'Data table', 'Axis labels', 'No color-only status in dashboard cards'] }); status(root, 'Accessible export record generated');
  }

  function analyze(root) {
    const data = fields(root), panel = root.dataset.scwbV270Panel;
    try {
      if (panel === 'visualization') analyzeVisualization(root, data);
      else if (panel === 'dashboard') renderDashboard(root, data);
      else if (panel === 'interactive') renderInteractive(root, data);
      else if (panel === 'validation') renderValidation(root, data);
      else if (panel === 'state') renderState(root, data);
      else renderExport(root, data);
    } catch (error) { status(root, 'Input needs review'); results(root, { ok: false, version: CONFIG.version, error: error.message }); }
  }

  function download(filename, content, type) { const blob = content instanceof Blob ? content : new Blob([content], { type: type || 'application/octet-stream' }), url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
  function exportSVG(root) { if (!root._scwbV270SVG) { analyze(root); } if (root._scwbV270SVG) download('workbench-v270-' + root.dataset.scwbV270Panel + '.svg', root._scwbV270SVG, 'image/svg+xml'); }
  function exportPNG(root) {
    if (!root._scwbV270SVG) analyze(root); if (!root._scwbV270SVG) return;
    const svgBlob = new Blob([root._scwbV270SVG], { type: 'image/svg+xml;charset=utf-8' }), url = URL.createObjectURL(svgBlob), image = new Image();
    image.onload = function () { const canvas = document.createElement('canvas'); canvas.width = 1640; canvas.height = 880; const context = canvas.getContext('2d'); context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height); context.drawImage(image, 0, 0, canvas.width, canvas.height); URL.revokeObjectURL(url); canvas.toBlob((blob) => { if (blob) download('workbench-v270-' + root.dataset.scwbV270Panel + '.png', blob, 'image/png'); }); };
    image.onerror = function () { URL.revokeObjectURL(url); results(root, { ok: false, error: 'PNG export could not render this SVG in the current browser.' }); };
    image.src = url;
  }


  function csvCell(value) {
    const text = value != null && typeof value === 'object' ? JSON.stringify(value) : String(value == null ? '' : value);
    return /[",\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
  }
  function exportCSV(root) {
    const record = root._scwbV270Last || {}, rows = Array.isArray(record.data) ? record.data : Array.isArray(record.points) ? record.points : Array.isArray(record.dataTable) ? record.dataTable : Array.isArray(record.metrics) ? record.metrics : [];
    if (!rows.length) { results(root, { ok: false, error: 'No tabular result is available for CSV export. Render the visualization first.' }); return; }
    const headers = Array.from(rows.reduce((set, row) => { Object.keys(row || {}).forEach((key) => set.add(key)); return set; }, new Set()));
    const csv = [headers.map(csvCell).join(',')].concat(rows.map((row) => headers.map((header) => csvCell(row[header])).join(','))).join('\n') + '\n';
    download('workbench-v270-' + root.dataset.scwbV270Panel + '.csv', csv, 'text/csv');
  }

  async function connect(root) {
    const data = fields(root), base = (data.runner_url || CONFIG.runnerDefaultUrl).replace(/\/$/, ''), code = String(data.pairing_code || '').trim(); status(root, 'Connecting…');
    try {
      let token = localStorage.getItem(CONFIG.storagePrefix + 'runner-token');
      if (code) { const response = await fetch(base + '/pair', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, origin: window.location.origin }) }), payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Pairing failed'); token = payload.token; localStorage.setItem(CONFIG.storagePrefix + 'runner-token', token); }
      if (!token) throw new Error('Enter the one-time pairing code shown by the local runner.');
      const response = await fetch(base + '/visualization-tools', { headers: { Authorization: 'Bearer ' + token } }), payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Visualization-tool discovery failed'); status(root, 'Local runner paired'); results(root, payload);
    } catch (error) { status(root, 'Runner unavailable'); results(root, { ok: false, error: error.message, runnerUrl: base }); }
  }

  function initialize(root) {
    const saved = parseJSON(localStorage.getItem(storageKey(root)), null);
    if (saved && saved.fields) root.querySelectorAll('[data-scwb-v270-field]').forEach((node) => { if (Object.prototype.hasOwnProperty.call(saved.fields, node.dataset.scwbV270Field)) node.value = saved.fields[node.dataset.scwbV270Field]; });
    root.querySelectorAll('input[type=range][data-scwb-v270-field]').forEach((node) => { const badge = document.createElement('output'); badge.textContent = node.value; badge.style.fontFamily = 'ui-monospace, monospace'; badge.style.fontSize = '.78rem'; badge.style.color = '#5a6972'; node.insertAdjacentElement('afterend', badge); node.addEventListener('input', () => { badge.textContent = node.value; if (root.dataset.scwbV270Panel === 'interactive') analyze(root); }); });
    root.addEventListener('click', (event) => {
      const button = event.target.closest('[data-scwb-v270-action]'); if (!button) return; const action = button.dataset.scwbV270Action;
      if (action === 'analyze') analyze(root);
      else if (action === 'connect') connect(root);
      else if (action === 'save') { localStorage.setItem(storageKey(root), JSON.stringify({ version: CONFIG.version, savedAt: new Date().toISOString(), fields: fields(root), result: root._scwbV270Last || null })); status(root, 'Saved in this browser'); }
      else if (action === 'export-json') download('workbench-v270-' + root.dataset.scwbV270Panel + '.json', JSON.stringify(root._scwbV270Last || { version: CONFIG.version, fields: fields(root) }, null, 2) + '\n', 'application/json');
      else if (action === 'export-csv') exportCSV(root);
      else if (action === 'export-svg') exportSVG(root);
      else if (action === 'export-png') exportPNG(root);
    });
  }

  document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('[data-scwb-v270-panel]').forEach(initialize));
}());
