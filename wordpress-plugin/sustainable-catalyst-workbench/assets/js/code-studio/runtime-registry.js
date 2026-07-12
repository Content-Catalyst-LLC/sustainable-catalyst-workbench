(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  const fallbackRuntimes = [
    { id: 'javascript', label: 'JavaScript', target: 'browser-worker', status: 'available', version: 'Browser ES', release: '1.9.1' },
    { id: 'python', label: 'Python', target: 'pyodide-worker', status: 'available', version: 'Pyodide', release: '1.9.1' },
    { id: 'r', label: 'R', target: 'webr-worker', status: 'available', version: 'webR', release: '1.9.1' },
    { id: 'sql', label: 'SQL', target: 'duckdb-wasm', status: 'available', version: 'DuckDB-Wasm', release: '1.9.1' },
    { id: 'c', label: 'C', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'cpp', label: 'C++', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'go', label: 'Go', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'rust', label: 'Rust', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'java', label: 'Java', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'haskell', label: 'Haskell', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'fortran', label: 'Fortran', target: 'local-runner', status: 'roadmap', release: '2.2.0' },
    { id: 'julia', label: 'Julia', target: 'local-runner', status: 'roadmap', release: '2.2.0' }
  ];

  function manifest() {
    return window.SCWorkbench && window.SCWorkbench.codeStudioManifest ? window.SCWorkbench.codeStudioManifest : {};
  }

  function all() {
    const configured = manifest().runtimes;
    return Array.isArray(configured) && configured.length ? configured : fallbackRuntimes;
  }

  function browser() {
    return all().filter(function (runtime) {
      const browserTarget = String(runtime.target || '').indexOf('browser') >= 0 || ['pyodide-worker', 'webr-worker', 'duckdb-wasm'].indexOf(runtime.target) >= 0;
      return runtime.status === 'available' && browserTarget;
    });
  }

  function get(id) {
    return all().find(function (runtime) { return runtime.id === id; }) || null;
  }

  function formatTable() {
    const rows = all();
    const widths = { label: 17, target: 19, status: 12, version: 17 };
    function pad(value, width) {
      const text = String(value || '');
      return text.slice(0, width - 1) + ' '.repeat(Math.max(1, width - Math.min(text.length, width - 1)));
    }
    const lines = [pad('Runtime', widths.label) + pad('Target', widths.target) + pad('Status', widths.status) + pad('Version', widths.version) + 'Release'];
    lines.push('-'.repeat(79));
    rows.forEach(function (runtime) {
      lines.push(pad(runtime.label, widths.label) + pad(runtime.target, widths.target) + pad(runtime.status, widths.status) + pad(runtime.version || '', widths.version) + (runtime.release || ''));
    });
    return lines.join('\n');
  }

  function packageText(runtimeId) {
    const runtime = get(runtimeId);
    const packages = runtime && runtime.packages;
    if (!Array.isArray(packages) || !packages.length) return 'No package list is published for ' + runtimeId + '.';
    return runtime.label + ' approved browser packages:\n  ' + packages.join('\n  ');
  }

  root.RuntimeRegistry = { all: all, browser: browser, get: get, formatTable: formatTable, packageText: packageText, manifest: manifest };
})(window);
