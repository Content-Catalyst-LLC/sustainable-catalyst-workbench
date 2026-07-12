(function (window) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function createAdapter(config, callbacks) {
    let worker = null;
    let pending = null;
    let ready = false;

    function createWorker() {
      if (worker) worker.terminate();
      worker = new Worker(config.workerUrl);
      worker.onmessage = function (event) {
        const message = event.data || {};
        if (message.type === 'stream') callbacks.stream(message.stream || 'stdout', message.text || '');
        if (message.type === 'clear') callbacks.clear && callbacks.clear();
        if (message.type === 'done' && pending) {
          const current = pending;
          pending = null;
          current.resolve(message);
        }
      };
      worker.onerror = function (event) {
        if (pending) {
          const current = pending;
          pending = null;
          current.reject(new Error(event.message || 'JavaScript worker failed.'));
        }
      };
      ready = true;
    }

    return {
      id: 'javascript',
      load: function () {
        if (!worker) createWorker();
        return Promise.resolve({ id: 'javascript', version: 'ES2024-compatible browser runtime' });
      },
      run: function (job) {
        if (!worker) createWorker();
        if (pending) return Promise.reject(new Error('A JavaScript job is already running.'));
        return new Promise(function (resolve, reject) {
          pending = { resolve: resolve, reject: reject };
          worker.postMessage({ type: 'run', code: job.code, path: job.path, files: job.files });
        });
      },
      stop: function () {
        if (worker) worker.terminate();
        if (pending) {
          pending.resolve({ ok: false, runtime: 'javascript', stopped: true, error: 'Execution stopped by user.', output: [], tables: [], charts: [], artifacts: [] });
          pending = null;
        }
        worker = null;
        ready = false;
      },
      reset: function () { this.stop(); },
      isReady: function () { return ready; }
    };
  }

  root.RuntimeJavaScript = { create: createAdapter };
})(window);
