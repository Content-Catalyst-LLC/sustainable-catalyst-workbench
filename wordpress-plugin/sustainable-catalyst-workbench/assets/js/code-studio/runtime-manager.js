(function (window) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  const extensions = {
    javascript: ['.js', '.mjs', '.cjs'],
    python: ['.py'],
    r: ['.r'],
    sql: ['.sql']
  };

  const forbidden = {
    javascript: [
      { re: /\b(fetch|XMLHttpRequest|WebSocket|EventSource|BroadcastChannel|indexedDB|caches)\b/i, message: 'Browser network and cross-context APIs are disabled.' },
      { re: /\b(importScripts|globalThis|self|window|document|localStorage|sessionStorage)\b/i, message: 'Direct access to the browser global environment is disabled.' },
      { re: /\b(eval|Function)\s*\(/, message: 'Dynamic code construction is disabled.' },
      { re: /\bimport\s*\(/, message: 'Dynamic module imports are disabled.' }
    ],
    python: [
      { re: /\b(subprocess|socket|requests|urllib|http\.client|ftplib|telnetlib)\b/i, message: 'Network and process modules are disabled in browser Python.' },
      { re: /\b(os\.system|os\.popen|micropip\.install|pyfetch|open_url)\b/i, message: 'Process execution and arbitrary package or network access are disabled.' },
      { re: /(^|\n)\s*(from\s+js\s+import|import\s+js\b)/i, message: 'Direct JavaScript bridge access is disabled.' },
      { re: /\b(eval|exec|compile|__import__)\s*\(/, message: 'Dynamic Python code construction is disabled.' }
    ],
    r: [
      { re: /\b(system2?|pipe|socketConnection|url|download\.file|browseURL)\s*\(/i, message: 'System and network functions are disabled in browser R.' },
      { re: /\b(install\.packages|download\.packages)\s*\(/i, message: 'Arbitrary package installation is disabled. Use the approved browser package set.' },
      { re: /\b(library|require)\s*\(\s*(curl|httr|httr2|websocket|processx|callr)/i, message: 'Network and process packages are disabled.' }
    ],
    sql: [
      { re: /\b(ATTACH|DETACH|INSTALL|LOAD|EXPORT|IMPORT|CALL|CREATE\s+SECRET)\b/i, message: 'Extensions, attached databases, and external import/export are disabled.' },
      { re: /\bCOPY\b[\s\S]*\bTO\b/i, message: 'COPY TO is disabled. Export results through Workbench instead.' },
      { re: /https?:\/\//i, message: 'Remote URLs are disabled in browser SQL.' },
      { re: /\b(PRAGMA|SET)\b/i, message: 'Runtime configuration statements are disabled.' }
    ]
  };

  function detectRuntime(path) {
    const lower = String(path || '').toLowerCase();
    for (const runtime of Object.keys(extensions)) {
      if (extensions[runtime].some(function (extension) { return lower.endsWith(extension); })) return runtime;
    }
    return '';
  }

  function validate(runtime, code, limits) {
    const source = String(code || '');
    const maxSource = Number(limits.maxSourceBytes || 262144);
    if (new Blob([source]).size > maxSource) throw new Error('Source exceeds the browser runtime limit of ' + maxSource + ' bytes.');
    (forbidden[runtime] || []).forEach(function (rule) {
      if (rule.re.test(source)) throw new Error('Runtime safety check: ' + rule.message);
    });
  }

  function projectFiles(fileSystem) {
    const project = fileSystem.getProject();
    const files = {};
    Object.keys(project.files || {}).forEach(function (path) {
      const node = project.files[path];
      if (node && node.type === 'file') files[path] = String(node.content == null ? '' : node.content);
    });
    return files;
  }

  function createManager(options) {
    const fileSystem = options.fileSystem;
    const manifest = options.manifest || {};
    const callbacks = options.callbacks || {};
    const runtimeConfig = manifest.runtime_config || {};
    const limits = manifest.limits || {};
    const adapters = {};
    let activeJob = null;
    let selectedRuntime = options.selectedRuntime || 'javascript';

    function emitStatus(runtime, status, detail) {
      callbacks.status && callbacks.status({ runtime: runtime, status: status, detail: detail || '' });
    }

    function adapter(runtime) {
      if (adapters[runtime]) return adapters[runtime];
      const commonCallbacks = {
        stream: function (stream, text) { callbacks.stream && callbacks.stream(stream, text); },
        clear: function () { callbacks.clear && callbacks.clear(); }
      };
      if (runtime === 'javascript') adapters[runtime] = root.RuntimeJavaScript.create(runtimeConfig.javascript || {}, commonCallbacks);
      else if (runtime === 'python') adapters[runtime] = root.RuntimePython.create(runtimeConfig.python || {}, commonCallbacks);
      else if (runtime === 'r') adapters[runtime] = root.RuntimeR.create(runtimeConfig.r || {}, commonCallbacks);
      else if (runtime === 'sql') adapters[runtime] = root.RuntimeSQL.create(runtimeConfig.sql || {}, commonCallbacks);
      else throw new Error('Browser runtime is not available: ' + runtime);
      return adapters[runtime];
    }

    function load(runtime) {
      const id = runtime || selectedRuntime;
      selectedRuntime = id;
      emitStatus(id, 'loading', 'Downloading runtime assets');
      return adapter(id).load().then(function (info) {
        emitStatus(id, 'ready', info.version || 'Ready');
        return info;
      }).catch(function (error) {
        emitStatus(id, 'error', error.message || String(error));
        throw error;
      });
    }

    function persistArtifacts(result) {
      const writes = [];
      (result.artifacts || []).forEach(function (artifact) {
        if (artifact.encoding !== 'text') return;
        const path = fileSystem.normalizePath(artifact.path || '/output/artifact.txt');
        writes.push(fileSystem.write(path, artifact.content == null ? '' : artifact.content));
      });
      return Promise.all(writes);
    }

    function run(path, runtimeOverride) {
      const normalized = fileSystem.normalizePath(path);
      const runtime = runtimeOverride || detectRuntime(normalized) || selectedRuntime;
      if (!runtime || ['javascript', 'python', 'r', 'sql'].indexOf(runtime) < 0) throw new Error('Choose JavaScript, Python, R, or SQL for this browser file.');
      if (activeJob) throw new Error('A browser execution job is already active. Use stop first.');
      const code = fileSystem.read(normalized);
      validate(runtime, code, limits);
      selectedRuntime = runtime;
      const started = Date.now();
      const timeoutMs = Math.max(1000, Number(limits.executionTimeoutMs || 15000));
      emitStatus(runtime, 'running', normalized);
      activeJob = { runtime: runtime, path: normalized, started: started };
      const execution = adapter(runtime).run({ path: normalized, code: code, files: projectFiles(fileSystem) });
      const timeout = new Promise(function (resolve) {
        activeJob.timeoutId = window.setTimeout(function () {
          adapter(runtime).stop();
          resolve({ ok: false, runtime: runtime, stopped: true, timedOut: true, error: 'Execution exceeded ' + timeoutMs + ' ms and was stopped.', output: [], tables: [], charts: [], artifacts: [], durationMs: Date.now() - started });
        }, timeoutMs);
      });
      return Promise.race([execution, timeout]).then(function (result) {
        if (activeJob && activeJob.timeoutId) window.clearTimeout(activeJob.timeoutId);
        activeJob = null;
        return persistArtifacts(result).then(function () {
          emitStatus(runtime, result.ok ? 'ready' : (result.stopped ? 'stopped' : 'error'), result.ok ? ('Completed in ' + (result.durationMs || Date.now() - started) + ' ms') : (result.error || 'Execution failed'));
          callbacks.result && callbacks.result(result, normalized);
          return result;
        });
      }).catch(function (error) {
        if (activeJob && activeJob.timeoutId) window.clearTimeout(activeJob.timeoutId);
        activeJob = null;
        emitStatus(runtime, 'error', error.message || String(error));
        throw error;
      });
    }

    function stop() {
      if (!activeJob) return false;
      const job = activeJob;
      if (job.timeoutId) window.clearTimeout(job.timeoutId);
      adapter(job.runtime).stop();
      activeJob = null;
      emitStatus(job.runtime, 'stopped', job.path);
      callbacks.stopped && callbacks.stopped(job);
      return true;
    }

    return {
      load: load,
      run: run,
      stop: stop,
      reset: function (runtime) {
        const id = runtime || selectedRuntime;
        if (adapters[id]) adapters[id].reset();
        emitStatus(id, 'idle', 'Runtime reset');
      },
      detectRuntime: detectRuntime,
      validate: validate,
      isRunning: function () { return !!activeJob; },
      getActiveJob: function () { return activeJob ? Object.assign({}, activeJob) : null; },
      getSelectedRuntime: function () { return selectedRuntime; },
      setSelectedRuntime: function (runtime) { selectedRuntime = runtime; },
      available: function () { return ['javascript', 'python', 'r', 'sql']; }
    };
  }

  root.RuntimeManager = { create: createManager, detectRuntime: detectRuntime, validate: validate };
})(window);
