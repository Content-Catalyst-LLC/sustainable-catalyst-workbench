(function (window) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function createAdapter(config, callbacks) {
    let worker = null;
    let loadPromise = null;
    let pending = null;
    let version = '';

    function createWorker() {
      worker = new Worker(config.workerUrl);
      worker.onmessage = function (event) {
        const message = event.data || {};
        if (message.type === 'stream') callbacks.stream(message.stream || 'stdout', message.text || '');
        if (message.type === 'ready') {
          version = message.version || '';
          if (pending && pending.kind === 'load') {
            const current = pending;
            pending = null;
            current.resolve({ id: 'python', version: version });
          }
        }
        if (message.type === 'error') {
          if (pending) {
            const current = pending;
            pending = null;
            current.reject(new Error(message.error || 'Python runtime failed.'));
          }
        }
        if (message.type === 'done' && pending && pending.kind === 'run') {
          const current = pending;
          pending = null;
          current.resolve(message);
        }
      };
      worker.onerror = function (event) {
        if (pending) {
          const current = pending;
          pending = null;
          current.reject(new Error(event.message || 'Python worker failed.'));
        }
      };
    }

    function load() {
      if (loadPromise) return loadPromise;
      loadPromise = new Promise(function (resolve, reject) {
        if (!worker) createWorker();
        pending = { kind: 'load', resolve: resolve, reject: reject };
        worker.postMessage({ type: 'init', config: config });
      }).catch(function (error) {
        loadPromise = null;
        throw error;
      });
      return loadPromise;
    }

    return {
      id: 'python',
      load: load,
      run: function (job) {
        return load().then(function () {
          if (pending) throw new Error('A Python job is already running.');
          return new Promise(function (resolve, reject) {
            pending = { kind: 'run', resolve: resolve, reject: reject };
            worker.postMessage({ type: 'run', code: job.code, path: job.path, files: job.files, config: config });
          });
        });
      },
      stop: function () {
        if (worker) worker.terminate();
        if (pending) {
          pending.resolve({ ok: false, runtime: 'python', stopped: true, error: 'Execution stopped by user.', output: [], tables: [], charts: [], artifacts: [] });
          pending = null;
        }
        worker = null;
        loadPromise = null;
        version = '';
      },
      reset: function () { this.stop(); },
      isReady: function () { return !!(worker && loadPromise); },
      version: function () { return version; }
    };
  }

  root.RuntimePython = { create: createAdapter };
})(window);
