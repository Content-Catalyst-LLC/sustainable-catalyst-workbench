/* Sustainable Catalyst Workbench v1.9.1 — Pyodide worker */
(function () {
  'use strict';

  let pyodide = null;
  let config = null;
  let helperSource = '';
  const textEncoder = new TextEncoder();

  function postStream(stream, text) {
    self.postMessage({ type: 'stream', stream: stream, text: String(text == null ? '' : text) });
  }

  function mkdirTree(path) {
    const parts = String(path || '/').split('/').filter(Boolean);
    let current = '';
    parts.forEach(function (part) {
      current += '/' + part;
      try { pyodide.FS.mkdir(current); } catch (error) {}
    });
  }

  function clearDirectory(path) {
    try {
      const entries = pyodide.FS.readdir(path).filter(function (name) { return name !== '.' && name !== '..'; });
      entries.forEach(function (name) {
        const target = path.replace(/\/$/, '') + '/' + name;
        const stat = pyodide.FS.stat(target);
        if (pyodide.FS.isDir(stat.mode)) {
          clearDirectory(target);
          pyodide.FS.rmdir(target);
        } else {
          pyodide.FS.unlink(target);
        }
      });
    } catch (error) {}
  }

  function syncFiles(files) {
    mkdirTree('/workbench');
    clearDirectory('/workbench');
    mkdirTree('/workbench/output');
    Object.keys(files || {}).forEach(function (path) {
      const normalized = '/workbench' + (String(path).startsWith('/') ? String(path) : '/' + String(path));
      const parent = normalized.slice(0, normalized.lastIndexOf('/')) || '/workbench';
      mkdirTree(parent);
      pyodide.FS.writeFile(normalized, String(files[path] == null ? '' : files[path]), { encoding: 'utf8' });
    });
  }

  function topLevelImports(code) {
    const found = [];
    String(code || '').split('\n').forEach(function (line) {
      let match = line.match(/^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)/);
      if (!match) match = line.match(/^\s*from\s+([A-Za-z_][A-Za-z0-9_]*)/);
      if (match && found.indexOf(match[1]) < 0) found.push(match[1]);
    });
    return found;
  }

  async function loadApprovedPackages(code) {
    const mapping = Object.assign({
      numpy: 'numpy',
      pandas: 'pandas',
      scipy: 'scipy',
      sympy: 'sympy',
      matplotlib: 'matplotlib',
      sklearn: 'scikit-learn',
      statsmodels: 'statsmodels'
    }, config.packageMap || {});
    const approved = config.approvedPackages || Object.keys(mapping);
    const packages = [];
    topLevelImports(code).forEach(function (module) {
      if (approved.indexOf(module) >= 0 && mapping[module] && packages.indexOf(mapping[module]) < 0) packages.push(mapping[module]);
    });
    if (packages.length) {
      postStream('system', 'Loading approved Python packages: ' + packages.join(', '));
      await pyodide.loadPackage(packages, { messageCallback: function (message) { postStream('system', message); } });
    }
    return packages;
  }

  function bytesToDataUrl(bytes, mimeType) {
    let binary = '';
    const chunk = 0x8000;
    for (let index = 0; index < bytes.length; index += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(index, Math.min(index + chunk, bytes.length)));
    }
    return 'data:' + mimeType + ';base64,' + btoa(binary);
  }

  function collectOutput(path, out) {
    let entries = [];
    try { entries = pyodide.FS.readdir(path).filter(function (name) { return name !== '.' && name !== '..'; }); }
    catch (error) { return; }
    entries.forEach(function (name) {
      const full = path.replace(/\/$/, '') + '/' + name;
      const stat = pyodide.FS.stat(full);
      if (pyodide.FS.isDir(stat.mode)) {
        collectOutput(full, out);
        return;
      }
      const projectPath = full.replace(/^\/workbench/, '') || '/output/' + name;
      const lower = name.toLowerCase();
      if (lower.endsWith('.table.json') || lower.endsWith('.chart.json')) {
        try {
          const parsed = JSON.parse(pyodide.FS.readFile(full, { encoding: 'utf8' }));
          if (lower.endsWith('.table.json')) out.tables.push(parsed);
          else out.charts.push({ name: parsed.name || name, kind: 'spec', spec: parsed.spec || parsed });
        } catch (error) {
          out.artifacts.push({ path: projectPath, content: pyodide.FS.readFile(full, { encoding: 'utf8' }), mimeType: 'application/json', encoding: 'text' });
        }
      } else if (lower.endsWith('.png')) {
        const bytes = pyodide.FS.readFile(full);
        out.charts.push({ name: name, kind: 'image', dataUrl: bytesToDataUrl(bytes, 'image/png') });
      } else if (lower.endsWith('.svg')) {
        const svg = pyodide.FS.readFile(full, { encoding: 'utf8' });
        out.charts.push({ name: name, kind: 'image', dataUrl: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg) });
      } else {
        out.artifacts.push({ path: projectPath, content: pyodide.FS.readFile(full, { encoding: 'utf8' }), mimeType: 'text/plain', encoding: 'text' });
      }
    });
  }

  async function initialize(nextConfig) {
    if (pyodide) return;
    config = nextConfig || {};
    importScripts(config.loaderUrl);
    pyodide = await loadPyodide({ indexURL: config.indexUrl });
    pyodide.setStdout({ batched: function (text) { postStream('stdout', text); } });
    pyodide.setStderr({ batched: function (text) { postStream('stderr', text); } });
    mkdirTree('/workbench/output');
    helperSource = [
      'import json, pathlib',
      'def _safe_name(name):',
      '    return "".join(c if c.isalnum() or c in "-_." else "-" for c in str(name)).strip("-") or "result"',
      'def table(name, data):',
      '    if hasattr(data, "to_dict"):',
      '        try: data = data.to_dict(orient="records")',
      '        except TypeError: data = data.to_dict()',
      '    path = pathlib.Path("/workbench/output") / (_safe_name(name) + ".table.json")',
      '    path.write_text(json.dumps({"name": str(name), "data": data}, default=str), encoding="utf-8")',
      '    return str(path)',
      'def chart(name, spec):',
      '    path = pathlib.Path("/workbench/output") / (_safe_name(name) + ".chart.json")',
      '    path.write_text(json.dumps({"name": str(name), "spec": spec}, default=str), encoding="utf-8")',
      '    return str(path)',
      'def artifact(name, content):',
      '    path = pathlib.Path("/workbench/output") / _safe_name(name)',
      '    path.write_text(str(content), encoding="utf-8")',
      '    return str(path)'
    ].join('\n');
    pyodide.FS.writeFile('/workbench/workbench.py', helperSource, { encoding: 'utf8' });
  }

  self.onmessage = async function (event) {
    const message = event.data || {};
    if (message.type === 'init') {
      try {
        await initialize(message.config || {});
        self.postMessage({ type: 'ready', runtime: 'python', version: pyodide.runPython('import sys; sys.version.split()[0]') });
      } catch (error) {
        self.postMessage({ type: 'error', runtime: 'python', error: error && (error.stack || error.message) ? (error.stack || error.message) : String(error) });
      }
      return;
    }
    if (message.type !== 'run') return;
    const started = Date.now();
    const result = { type: 'done', ok: false, runtime: 'python', output: [], tables: [], charts: [], artifacts: [], durationMs: 0 };
    try {
      await initialize(message.config || {});
      syncFiles(message.files || {});
      pyodide.FS.writeFile('/workbench/workbench.py', helperSource, { encoding: 'utf8' });
      await loadApprovedPackages(message.code || '');
      await pyodide.runPythonAsync([
        'import os, sys',
        'os.chdir("/workbench")',
        'if "/workbench" not in sys.path: sys.path.insert(0, "/workbench")',
        'sys.argv = [' + JSON.stringify(String(message.path || '/src/analysis.py')) + ']'
      ].join('\n'));
      const value = await pyodide.runPythonAsync(String(message.code || ''));
      try {
        await pyodide.runPythonAsync([
          'try:',
          '    import matplotlib.pyplot as _scwb_plt',
          '    for _scwb_i, _scwb_num in enumerate(_scwb_plt.get_fignums(), start=1):',
          '        _scwb_plt.figure(_scwb_num).savefig(f"/workbench/output/plot-{_scwb_i}.png", dpi=140, bbox_inches="tight")',
          'except Exception:',
          '    pass'
        ].join('\n'));
      } catch (error) {}
      if (value !== undefined && value !== null) {
        let converted = value;
        if (value && typeof value.toJs === 'function') {
          try { converted = value.toJs({ dict_converter: Object.fromEntries }); } catch (error) { converted = String(value); }
          try { value.destroy(); } catch (error) {}
        }
        result.result = converted;
        postStream('result', typeof converted === 'string' ? converted : JSON.stringify(converted, null, 2));
      }
      collectOutput('/workbench/output', result);
      result.ok = true;
    } catch (error) {
      result.error = error && (error.stack || error.message) ? (error.stack || error.message) : String(error);
    }
    result.durationMs = Date.now() - started;
    self.postMessage(result);
  };
})();
