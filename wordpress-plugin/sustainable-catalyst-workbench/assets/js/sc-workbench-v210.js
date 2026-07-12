(() => {
  'use strict';

  const cfg = window.SCWBV210 || {};
  const q = (root, selector) => root.querySelector(selector);
  const qa = (root, selector) => Array.from(root.querySelectorAll(selector));
  const field = (root, name) => q(root, `[data-scwb-v210-field="${name}"]`);
  const value = (root, name, fallback = '') => {
    const el = field(root, name);
    if (!el) return fallback;
    if (el.type === 'checkbox') return Boolean(el.checked);
    return el.value === '' ? fallback : el.value;
  };
  const action = (root, name, callback) => {
    const el = q(root, `[data-scwb-v210-action="${name}"]`);
    if (el) el.addEventListener('click', callback);
  };
  const project = root => root.dataset.scwbV210Project || 'default';
  const key = (root, suffix) => `${cfg.storagePrefix || 'scwb-v210:'}${project(root)}:${suffix}`;
  const save = (root, suffix, data) => localStorage.setItem(key(root, suffix), JSON.stringify(data));
  const load = (root, suffix, fallback) => {
    try {
      const raw = localStorage.getItem(key(root, suffix));
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  };
  const setStatus = (root, text) => {
    const el = q(root, '[data-scwb-v210-status]');
    if (el) el.textContent = text;
  };
  const safeName = text => String(text || 'project').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'project';
  const esc = text => String(text ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const round = (number, digits = 4) => Number.isFinite(number) ? Number(number.toFixed(digits)) : null;
  const mean = values => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
  const download = (filename, content, type = 'application/json;charset=utf-8') => {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const metricCards = metrics => Object.entries(metrics).map(([label, result]) => `<div class="scwb-v210__metric"><span>${esc(label)}</span><strong>${esc(result)}</strong></div>`).join('');

  function parseCSV(text) {
    const rows = [];
    let row = [];
    let cell = '';
    let quoted = false;
    const input = String(text || '').replace(/\r\n?/g, '\n');
    for (let index = 0; index < input.length; index += 1) {
      const char = input[index];
      if (quoted) {
        if (char === '"' && input[index + 1] === '"') {
          cell += '"';
          index += 1;
        } else if (char === '"') {
          quoted = false;
        } else {
          cell += char;
        }
      } else if (char === '"') {
        quoted = true;
      } else if (char === ',') {
        row.push(cell.trim());
        cell = '';
      } else if (char === '\n') {
        row.push(cell.trim());
        if (row.some(item => item !== '')) rows.push(row);
        row = [];
        cell = '';
      } else {
        cell += char;
      }
    }
    row.push(cell.trim());
    if (row.some(item => item !== '')) rows.push(row);
    if (rows.length < 2) throw new Error('CSV requires a header and at least one data row.');
    const headers = rows[0];
    if (new Set(headers).size !== headers.length) throw new Error('CSV headers must be unique.');
    return rows.slice(1).map((cells, rowIndex) => {
      if (cells.length !== headers.length) throw new Error(`Row ${rowIndex + 2} has ${cells.length} columns; expected ${headers.length}.`);
      return Object.fromEntries(headers.map((header, index) => [header, cells[index]]));
    });
  }

  function linearFit(x, y) {
    if (x.length !== y.length || x.length < 2) throw new Error('At least two paired values are required.');
    const mx = mean(x);
    const my = mean(y);
    const denominator = x.reduce((sum, current) => sum + ((current - mx) ** 2), 0);
    if (denominator === 0) throw new Error('Independent values must not all be identical.');
    const slope = x.reduce((sum, current, index) => sum + ((current - mx) * (y[index] - my)), 0) / denominator;
    const intercept = my - (slope * mx);
    const predicted = x.map(current => (slope * current) + intercept);
    const residuals = y.map((current, index) => current - predicted[index]);
    const sse = residuals.reduce((sum, current) => sum + (current ** 2), 0);
    const sst = y.reduce((sum, current) => sum + ((current - my) ** 2), 0);
    const rmse = Math.sqrt(sse / y.length);
    const r2 = sst === 0 ? 1 : 1 - (sse / sst);
    return {slope, intercept, predicted, residuals, rmse, r2};
  }

  async function runnerRequest(root, path, options = {}) {
    const base = String(value(root, 'runner-url', cfg.runnerDefaultUrl || 'http://127.0.0.1:8787')).replace(/\/$/, '');
    const tokenKey = `${cfg.v200StoragePrefix || 'scwb-v200:'}${project(root)}:runner-token`;
    const token = sessionStorage.getItem(tokenKey);
    const headers = {'Content-Type': 'application/json', ...(options.headers || {})};
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(base + path, {...options, headers});
    const data = await response.json().catch(() => ({ok: false, error: `HTTP ${response.status}`}));
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  function initDevice(root) {
    const output = q(root, '[data-scwb-v210-device-output]');
    if (!output) return;
    const show = data => { output.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2); };
    action(root, 'device-health', async () => {
      try {
        const data = await runnerRequest(root, '/health');
        show(data);
        setStatus(root, `Runner ${data.version || 'online'}`);
      } catch (error) {
        show(`Runner unavailable: ${error.message}`);
        setStatus(root, 'Runner offline');
      }
    });
    action(root, 'device-discover', async () => {
      try {
        const data = await runnerRequest(root, '/devices');
        show(data);
        save(root, 'device-discovery', data);
        setStatus(root, 'Device discovery complete');
      } catch (error) {
        show(`Device discovery failed: ${error.message}\nPair with the v2.0.0 Local Go Runner panel first.`);
        setStatus(root, 'Discovery failed');
      }
    });
    action(root, 'device-task-run', async () => {
      try {
        const data = await runnerRequest(root, '/device-task', {
          method: 'POST',
          body: JSON.stringify({task: value(root, 'device-task'), consent: value(root, 'device-consent', false)})
        });
        show(data);
        setStatus(root, 'Structured task complete');
      } catch (error) {
        show(`Device task failed: ${error.message}`);
        setStatus(root, 'Task failed');
      }
    });
  }

  function piProject(root) {
    const name = safeName(value(root, 'pi-project', 'environment-monitor'));
    const board = value(root, 'pi-board');
    const os = value(root, 'pi-os');
    const deviceInterface = value(root, 'pi-interface');
    const sensor = value(root, 'pi-sensor');
    const interval = Math.max(0.1, Number(value(root, 'pi-interval', 10)) || 10);
    const objective = value(root, 'pi-objective');
    const generatedAt = new Date().toISOString();
    const code = `#!/usr/bin/env python3\n"""${name}: generated Raspberry Pi acquisition scaffold.\nValidate hardware, permissions, drivers, electrical limits, and calibration before deployment.\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport signal\nimport time\nfrom datetime import datetime, timezone\n\nPROJECT = ${JSON.stringify(name)}\nBOARD_PROFILE = ${JSON.stringify(board)}\nINTERFACE = ${JSON.stringify(deviceInterface)}\nPERIPHERAL = ${JSON.stringify(sensor)}\nSAMPLE_INTERVAL_SECONDS = ${interval}\nRUNNING = True\n\ndef stop_service(_signum: int, _frame: object) -> None:\n    global RUNNING\n    RUNNING = False\n\ndef read_sensor() -> dict[str, object]:\n    # Replace this simulation with a reviewed driver for ${sensor}.\n    # Keep raw values, calibration version, uncertainty, and quality flags.\n    return {\n        "timestamp": datetime.now(timezone.utc).isoformat(),\n        "project": PROJECT,\n        "board": BOARD_PROFILE,\n        "interface": INTERFACE,\n        "peripheral": PERIPHERAL,\n        "raw_value": None,\n        "calibrated_value": None,\n        "unit": None,\n        "quality": "simulation",\n    }\n\ndef main() -> None:\n    signal.signal(signal.SIGINT, stop_service)\n    signal.signal(signal.SIGTERM, stop_service)\n    while RUNNING:\n        print(json.dumps(read_sensor(), sort_keys=True), flush=True)\n        time.sleep(SAMPLE_INTERVAL_SECONDS)\n\nif __name__ == "__main__":\n    main()\n`;
    const manifest = {
      schema: 'sc-workbench-raspberry-pi-project/1.0',
      workbenchVersion: cfg.version || '2.1.0',
      generatedAt,
      project: {id: name, objective},
      target: {board, operatingProfile: os, interface: deviceInterface, peripheral: sensor, sampleIntervalSeconds: interval},
      files: ['src/main.py', 'project.json', 'README.md', 'systemd/workbench-device.service'],
      validation: [
        'Confirm voltage, current, grounding, pull-up, and logic-level requirements.',
        'Confirm Linux device permissions and interface enablement.',
        'Record sensor calibration, uncertainty, location, and environmental conditions.',
        'Run hardware-absent simulation before connecting physical devices.',
        'Review service restart, logging, storage, network, privacy, and failure behavior.'
      ],
      deployment: {serviceUser: 'workbench', networkRequired: deviceInterface === 'network', nativeExecutionRequired: false}
    };
    return {name, code, manifest};
  }

  function initPi(root) {
    const codeOut = q(root, '[data-scwb-v210-pi-code]');
    const manifestOut = q(root, '[data-scwb-v210-pi-manifest]');
    if (!codeOut || !manifestOut) return;
    let current = load(root, 'pi-project', null);
    const render = item => {
      if (!item) return;
      codeOut.textContent = item.code;
      manifestOut.textContent = JSON.stringify(item.manifest, null, 2);
    };
    render(current);
    action(root, 'pi-generate', () => {
      current = piProject(root);
      save(root, 'pi-project', current);
      render(current);
      setStatus(root, 'Project generated');
    });
    action(root, 'pi-download', () => {
      current = current || piProject(root);
      const bundle = {
        schema: 'sc-workbench-project-bundle/1.0',
        kind: 'raspberry-pi',
        project: current.manifest,
        files: {'src/main.py': current.code, 'project.json': JSON.stringify(current.manifest, null, 2)}
      };
      download(`${current.name}-raspberry-pi-project.json`, JSON.stringify(bundle, null, 2));
      setStatus(root, 'Project bundle downloaded');
    });
    action(root, 'pi-python', () => {
      current = current || piProject(root);
      download(`${current.name}.py`, current.code, 'text/x-python;charset=utf-8');
      setStatus(root, 'Python service downloaded');
    });
  }

  function prepareDataset(root) {
    const rows = parseCSV(value(root, 'tinyml-csv'));
    const target = String(value(root, 'tinyml-target')).trim();
    const task = value(root, 'tinyml-task', 'classification');
    const quantization = value(root, 'tinyml-quantization', 'int8');
    if (!target || !(target in rows[0])) throw new Error(`Target column "${target}" was not found.`);
    const features = Object.keys(rows[0]).filter(header => header !== target);
    if (!features.length) throw new Error('At least one feature column is required.');
    const numeric = rows.map((row, rowIndex) => features.map(feature => {
      const number = Number(row[feature]);
      if (!Number.isFinite(number)) throw new Error(`Feature ${feature} in row ${rowIndex + 2} is not numeric.`);
      return number;
    }));
    if (task === 'regression') {
      rows.forEach((row, rowIndex) => {
        if (!Number.isFinite(Number(row[target]))) throw new Error(`Regression target in row ${rowIndex + 2} is not numeric.`);
      });
    }
    const splitAt = Math.max(1, Math.min(rows.length - 1, Math.floor(rows.length * 0.8)));
    return {rows, target, task, quantization, features, numeric, splitAt};
  }

  function classificationBaseline(data) {
    const trainRows = data.rows.slice(0, data.splitAt);
    const trainX = data.numeric.slice(0, data.splitAt);
    const testRows = data.rows.slice(data.splitAt);
    const testX = data.numeric.slice(data.splitAt);
    const labels = [...new Set(trainRows.map(row => row[data.target]))];
    if (labels.length < 2) throw new Error('Classification training data needs at least two classes before the test split.');
    const centroids = Object.fromEntries(labels.map(label => {
      const matches = trainX.filter((_, index) => trainRows[index][data.target] === label);
      return [label, data.features.map((_, featureIndex) => mean(matches.map(row => row[featureIndex])))];
    }));
    const predict = vector => labels.reduce((best, label) => {
      const distance = vector.reduce((sum, current, index) => sum + ((current - centroids[label][index]) ** 2), 0);
      return !best || distance < best.distance ? {label, distance} : best;
    }, null).label;
    const predictions = testX.map(predict);
    const actual = testRows.map(row => row[data.target]);
    const correct = predictions.filter((prediction, index) => prediction === actual[index]).length;
    return {algorithm: 'nearest-centroid', centroids, predictions, actual, accuracy: actual.length ? correct / actual.length : 0};
  }

  function regressionBaseline(data) {
    const feature = data.features[0];
    const trainX = data.rows.slice(0, data.splitAt).map(row => Number(row[feature]));
    const trainY = data.rows.slice(0, data.splitAt).map(row => Number(row[data.target]));
    const testX = data.rows.slice(data.splitAt).map(row => Number(row[feature]));
    const testY = data.rows.slice(data.splitAt).map(row => Number(row[data.target]));
    const fit = linearFit(trainX, trainY);
    const predictions = testX.map(x => (fit.slope * x) + fit.intercept);
    const residuals = testY.map((y, index) => y - predictions[index]);
    const rmse = Math.sqrt(mean(residuals.map(item => item ** 2)));
    const baselineMean = mean(testY);
    const sse = residuals.reduce((sum, item) => sum + (item ** 2), 0);
    const sst = testY.reduce((sum, item) => sum + ((item - baselineMean) ** 2), 0);
    return {algorithm: 'univariate-linear-regression', feature, slope: fit.slope, intercept: fit.intercept, predictions, actual: testY, rmse, r2: sst === 0 ? 1 : 1 - (sse / sst)};
  }

  function quantizationPreview(data) {
    const flat = data.numeric.flat();
    const maximum = Math.max(...flat.map(item => Math.abs(item)), 0);
    if (data.quantization === 'int8') {
      const scale = maximum === 0 ? 1 : maximum / 127;
      return {type: 'int8-symmetric-preview', scale, zeroPoint: 0, observedAbsoluteMaximum: maximum};
    }
    if (data.quantization === 'float16') return {type: 'float16-preview', note: 'Validate target-runtime operator and memory support.'};
    return {type: 'none'};
  }

  function analyzeTinyML(root) {
    const data = prepareDataset(root);
    const baseline = data.task === 'classification' ? classificationBaseline(data) : regressionBaseline(data);
    const columns = data.features.map((feature, index) => {
      const values = data.numeric.map(row => row[index]);
      const average = mean(values);
      const variance = mean(values.map(item => (item - average) ** 2));
      return {name: feature, min: Math.min(...values), max: Math.max(...values), mean: average, standardDeviation: Math.sqrt(variance)};
    });
    return {
      schema: 'sc-workbench-tinyml-model-card/1.0',
      workbenchVersion: cfg.version || '2.1.0',
      generatedAt: new Date().toISOString(),
      task: data.task,
      target: data.target,
      features: data.features,
      records: data.rows.length,
      trainRecords: data.splitAt,
      testRecords: data.rows.length - data.splitAt,
      splitMethod: 'deterministic-first-80-percent',
      columns,
      baseline,
      quantization: quantizationPreview(data),
      limitations: [
        'This browser baseline is for pipeline validation, not production model selection.',
        'The deterministic split is not randomized, stratified, grouped, or time-aware.',
        'Validate leakage, class balance, drift, calibration, uncertainty, fairness, latency, flash, RAM, and energy use.',
        'Reproduce training with a reviewed Python or embedded ML toolchain before deployment.'
      ]
    };
  }

  function tinyMLScaffold(card) {
    if (card.task === 'classification') {
      const labels = Object.keys(card.baseline.centroids || {});
      const arrays = labels.map((label, index) => `static const float centroid_${index}[FEATURE_COUNT] = {${card.baseline.centroids[label].map(item => round(item, 6)).join(', ')}};`).join('\n');
      return `/* Sustainable Catalyst Workbench v2.1.0 TinyML deployment scaffold\n * Baseline: nearest centroid. Validate against the reviewed training pipeline.\n */\n#include <math.h>\n#include <stddef.h>\n#define FEATURE_COUNT ${card.features.length}\n#define CLASS_COUNT ${labels.length}\n${arrays}\nstatic const char *labels[CLASS_COUNT] = {${labels.map(label => JSON.stringify(label)).join(', ')}};\n\nint predict_class(const float features[FEATURE_COUNT]) {\n  float best_distance = INFINITY;\n  int best_class = -1;\n  const float *centroids[CLASS_COUNT] = {${labels.map((_, index) => `centroid_${index}`).join(', ')}};\n  for (int c = 0; c < CLASS_COUNT; ++c) {\n    float distance = 0.0f;\n    for (int i = 0; i < FEATURE_COUNT; ++i) {\n      const float delta = features[i] - centroids[c][i];\n      distance += delta * delta;\n    }\n    if (distance < best_distance) { best_distance = distance; best_class = c; }\n  }\n  return best_class;\n}\n`;
    }
    return `/* Sustainable Catalyst Workbench v2.1.0 regression deployment scaffold */\nfloat predict_${safeName(card.target).replace(/-/g, '_')}(float ${safeName(card.baseline.feature).replace(/-/g, '_')}) {\n  return (${round(card.baseline.slope, 8)}f * ${safeName(card.baseline.feature).replace(/-/g, '_')}) + ${round(card.baseline.intercept, 8)}f;\n}\n`;
  }

  function initTinyML(root) {
    const output = q(root, '[data-scwb-v210-tinyml-output]');
    const metrics = q(root, '[data-scwb-v210-tinyml-metrics]');
    if (!output || !metrics) return;
    let card = load(root, 'tinyml-card', null);
    const render = item => {
      if (!item) return;
      const score = item.task === 'classification' ? `${round(item.baseline.accuracy * 100, 2)}%` : String(round(item.baseline.rmse, 5));
      metrics.innerHTML = metricCards({Records: item.records, Features: item.features.length, 'Test records': item.testRecords, [item.task === 'classification' ? 'Accuracy' : 'RMSE']: score});
      output.textContent = JSON.stringify(item, null, 2);
    };
    render(card);
    action(root, 'tinyml-analyze', () => {
      try {
        card = analyzeTinyML(root);
        save(root, 'tinyml-card', card);
        render(card);
        setStatus(root, 'Baseline validated');
      } catch (error) {
        output.textContent = `TinyML analysis failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Analysis failed');
      }
    });
    action(root, 'tinyml-model-card', () => {
      try {
        card = card || analyzeTinyML(root);
        download('tinyml-model-card.json', JSON.stringify(card, null, 2));
        setStatus(root, 'Model card downloaded');
      } catch (error) { output.textContent = error.message; }
    });
    action(root, 'tinyml-scaffold', () => {
      try {
        card = card || analyzeTinyML(root);
        download('tinyml-deployment-scaffold.h', tinyMLScaffold(card), 'text/x-c;charset=utf-8');
        setStatus(root, 'Deployment scaffold downloaded');
      } catch (error) { output.textContent = error.message; }
    });
    action(root, 'tinyml-bundle', () => {
      try {
        card = card || analyzeTinyML(root);
        const bundle = {
          schema: 'sc-workbench-project-bundle/1.0',
          kind: 'tinyml',
          modelCard: card,
          files: {'model-card.json': JSON.stringify(card, null, 2), 'deployment/model.h': tinyMLScaffold(card), 'data/source.csv': value(root, 'tinyml-csv')}
        };
        download('tinyml-project-bundle.json', JSON.stringify(bundle, null, 2));
        setStatus(root, 'TinyML bundle downloaded');
      } catch (error) { output.textContent = error.message; }
    });
  }

  function calibrationRecord(root) {
    const lines = String(value(root, 'cal-pairs')).split(/\n+/).map(line => line.trim()).filter(Boolean);
    const pairs = lines.map((line, index) => {
      const parts = line.split(',').map(item => Number(item.trim()));
      if (parts.length !== 2 || parts.some(item => !Number.isFinite(item))) throw new Error(`Calibration line ${index + 1} must be reference,measured.`);
      return {reference: parts[0], measured: parts[1]};
    });
    if (pairs.length < 3) throw new Error('Use at least three calibration points.');
    const fit = linearFit(pairs.map(item => item.measured), pairs.map(item => item.reference));
    return {
      schema: 'sc-workbench-sensor-calibration/1.0',
      workbenchVersion: cfg.version || '2.1.0',
      generatedAt: new Date().toISOString(),
      instrument: value(root, 'cal-name'),
      unit: value(root, 'cal-unit'),
      calibrationDate: value(root, 'cal-date') || new Date().toISOString().slice(0, 10),
      equation: {form: 'reference = slope * measured + intercept', slope: fit.slope, intercept: fit.intercept},
      performance: {rmse: fit.rmse, r2: fit.r2, points: pairs.length},
      points: pairs.map((item, index) => ({...item, predictedReference: fit.predicted[index], residual: fit.residuals[index]})),
      limitations: ['Linear calibration only.', 'Record reference-instrument traceability, uncertainty, temperature, humidity, stabilization time, hysteresis, repeatability, and valid operating range.']
    };
  }

  function initCalibration(root) {
    const output = q(root, '[data-scwb-v210-cal-output]');
    const metrics = q(root, '[data-scwb-v210-cal-metrics]');
    if (!output || !metrics) return;
    let record = load(root, 'calibration-record', null);
    const render = item => {
      if (!item) return;
      metrics.innerHTML = metricCards({Points: item.performance.points, Slope: round(item.equation.slope, 6), Intercept: round(item.equation.intercept, 6), 'R² / RMSE': `${round(item.performance.r2, 5)} / ${round(item.performance.rmse, 5)}`});
      output.textContent = JSON.stringify(item, null, 2);
    };
    render(record);
    action(root, 'cal-fit', () => {
      try {
        record = calibrationRecord(root);
        save(root, 'calibration-record', record);
        render(record);
        setStatus(root, 'Calibration fitted');
      } catch (error) {
        output.textContent = `Calibration failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Calibration failed');
      }
    });
    action(root, 'cal-download', () => {
      try {
        record = record || calibrationRecord(root);
        download(`${safeName(record.instrument)}-calibration.json`, JSON.stringify(record, null, 2));
        setStatus(root, 'Calibration record downloaded');
      } catch (error) { output.textContent = error.message; }
    });
  }

  function initLogs(root) {
    const body = q(root, '[data-scwb-v210-log-body]');
    if (!body) return;
    let rows = load(root, 'device-log', []);
    const render = () => {
      body.innerHTML = rows.map((item, index) => `<tr><td>${esc(item.timestamp)}</td><td>${esc(item.device)}</td><td>${esc(item.metric)}</td><td>${esc(item.value)} ${esc(item.unit)}</td><td>${esc(item.note)}</td><td><button type="button" class="scwb-v210__text-button" data-scwb-v210-log-remove="${index}">Remove</button></td></tr>`).join('');
      qa(body, '[data-scwb-v210-log-remove]').forEach(button => button.addEventListener('click', () => {
        rows.splice(Number(button.dataset.scwbV210LogRemove), 1);
        save(root, 'device-log', rows);
        render();
      }));
    };
    render();
    action(root, 'log-add', () => {
      rows.unshift({timestamp: new Date().toISOString(), device: value(root, 'log-device'), metric: value(root, 'log-metric'), value: value(root, 'log-value'), unit: value(root, 'log-unit'), note: value(root, 'log-note')});
      save(root, 'device-log', rows);
      render();
      setStatus(root, 'Observation saved');
    });
    action(root, 'log-export', () => {
      const csv = ['timestamp,device,metric,value,unit,note', ...rows.map(item => [item.timestamp, item.device, item.metric, item.value, item.unit, item.note].map(current => `"${String(current ?? '').replace(/"/g, '""')}"`).join(','))].join('\n');
      download(`${safeName(project(root))}-device-log.csv`, csv, 'text/csv;charset=utf-8');
      setStatus(root, 'Log exported');
    });
    action(root, 'log-clear', () => {
      if (!window.confirm('Clear the browser-local device observation log for this project?')) return;
      rows = [];
      save(root, 'device-log', rows);
      render();
      setStatus(root, 'Log cleared');
    });
  }

  const boards = [
    {family:'raspberry-pi', name:'Raspberry Pi 5', profile:'Linux SBC', capabilities:['GPIO','I²C','SPI','UART','camera','PCIe'], note:'High-performance local gateway, analysis, and edge inference.'},
    {family:'raspberry-pi', name:'Raspberry Pi Zero 2 W', profile:'Compact Linux SBC', capabilities:['GPIO','I²C','SPI','UART','Wi-Fi'], note:'Low-footprint sensing, logging, and gateway projects.'},
    {family:'arduino', name:'Arduino Nicla Vision', profile:'TinyML vision/sensing', capabilities:['camera','IMU','microphone','ToF'], note:'Compact multimodal embedded inference and sensor projects.'},
    {family:'arduino', name:'Arduino Nicla Voice', profile:'TinyML audio/motion', capabilities:['microphone','IMU','Bluetooth'], note:'Always-on audio, gesture, and low-power inference workflows.'},
    {family:'arduino', name:'Arduino Portenta H7', profile:'Dual-core industrial MCU', capabilities:['TinyML','Ethernet','Wi-Fi','camera','Arduino'], note:'Higher-complexity embedded control, sensing, and inference.'},
    {family:'arduino', name:'Arduino MKR family', profile:'Connected MCU', capabilities:['Arduino','I²C','SPI','UART','network options'], note:'Modular field sensing and connected prototype foundation.'},
    {family:'esp32', name:'ESP32 Arduino-compatible', profile:'Wireless MCU', capabilities:['Wi-Fi','Bluetooth','ADC','I²C','SPI'], note:'Low-cost connected sensing and embedded control.'},
    {family:'seeed', name:'Seeed XIAO / Wio family', profile:'Compact sensing MCU', capabilities:['Arduino toolchain','TinyML','wireless options'], note:'Small-footprint sensors, wearables, and field nodes.'},
    {family:'adafruit', name:'Adafruit LiteRT Micro boards', profile:'Learning and TinyML MCU', capabilities:['CircuitPython','Arduino','sensors','TinyML'], note:'Accessible embedded inference and instrument prototypes.'},
    {family:'st', name:'ST STM32 development boards', profile:'Industrial MCU', capabilities:['STM32Cube','TinyML','DSP','control'], note:'Performance-oriented sensing, control, and embedded ML.'},
    {family:'fpga', name:'Lattice iCE40-class boards', profile:'Open FPGA workflow', capabilities:['Verilog','Yosys','nextpnr','timing'], note:'Digital logic, interfaces, and deterministic hardware experiments.'}
  ];

  function initBoards(root) {
    const grid = q(root, '[data-scwb-v210-board-grid]');
    const selector = field(root, 'board-family');
    if (!grid || !selector) return;
    const render = () => {
      const family = selector.value;
      const visible = family === 'all' ? boards : boards.filter(board => board.family === family);
      grid.innerHTML = visible.map(board => `<article class="scwb-v210__board-card"><p class="scwb-v210__eyebrow">${esc(board.profile)}</p><h3>${esc(board.name)}</h3><p>${esc(board.note)}</p><ul class="scwb-v210__board-meta">${board.capabilities.map(item => `<li>${esc(item)}</li>`).join('')}</ul></article>`).join('');
      setStatus(root, `${visible.length} board profiles`);
    };
    selector.addEventListener('change', render);
    render();
  }

  function init(root) {
    const panel = root.dataset.scwbV210Panel;
    ({'device': initDevice, 'raspberry-pi': initPi, 'tinyml': initTinyML, 'calibration': initCalibration, 'logs': initLogs, 'boards': initBoards}[panel] || (() => {}))(root);
  }

  const boot = () => qa(document, '[data-scwb-v210-panel]').forEach(init);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
