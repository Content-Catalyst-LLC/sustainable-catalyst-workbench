(function (window) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};
  const encoder = new TextEncoder();

  function normalizePath(path) {
    return '/workbench' + (String(path || '').startsWith('/') ? String(path) : '/' + String(path || ''));
  }

  function createAdapter(config, callbacks) {
    let webR = null;
    let loadPromise = null;
    let running = false;

    async function ensureDirectory(path) {
      const parts = String(path || '/').split('/').filter(Boolean);
      let current = '';
      for (const part of parts) {
        current += '/' + part;
        try { await webR.FS.mkdir(current); } catch (error) {}
      }
    }

    async function syncFiles(files) {
      await ensureDirectory('/workbench/output');
      for (const path of Object.keys(files || {})) {
        const target = normalizePath(path);
        await ensureDirectory(target.slice(0, target.lastIndexOf('/')) || '/workbench');
        await webR.FS.writeFile(target, encoder.encode(String(files[path] == null ? '' : files[path])));
      }
    }

    function load() {
      if (loadPromise) return loadPromise;
      loadPromise = import(config.moduleUrl).then(async function (module) {
        const options = { interactive: false };
        if (!window.crossOriginIsolated && module.ChannelType && module.ChannelType.PostMessage) {
          options.channelType = module.ChannelType.PostMessage;
        }
        webR = new module.WebR(options);
        await webR.init();
        return { id: 'r', version: webR.versionR || webR.version || config.version || '' };
      }).catch(function (error) {
        loadPromise = null;
        webR = null;
        throw error;
      });
      return loadPromise;
    }

    return {
      id: 'r',
      load: load,
      run: function (job) {
        return load().then(async function () {
          if (running) throw new Error('An R job is already running.');
          running = true;
          const started = Date.now();
          const result = { ok: false, runtime: 'r', output: [], tables: [], charts: [], artifacts: [], durationMs: 0 };
          let shelter = null;
          try {
            await syncFiles(job.files || {});
            shelter = await new webR.Shelter();
            const wrapped = 'setwd("/workbench")\n' + String(job.code || '');
            const capture = await shelter.captureR(wrapped);
            (capture.output || []).forEach(function (entry) {
              const stream = entry.type === 'stderr' ? 'stderr' : 'stdout';
              const line = String(entry.data == null ? '' : entry.data);
              result.output.push({ stream: stream, text: line });
              callbacks.stream(stream, line);
            });
            (capture.images || []).forEach(function (image, index) {
              result.charts.push({ name: 'R plot ' + (index + 1), kind: 'bitmap', image: image });
            });
            result.ok = true;
          } catch (error) {
            result.error = error && (error.stack || error.message) ? (error.stack || error.message) : String(error);
          } finally {
            if (shelter) {
              try { shelter.purge(); } catch (error) {}
            }
            running = false;
          }
          result.durationMs = Date.now() - started;
          return result;
        });
      },
      stop: function () {
        if (!webR || !running) return;
        if (window.crossOriginIsolated && typeof webR.interrupt === 'function') {
          try { webR.interrupt(); return; } catch (error) {}
        }
        // PostMessage mode cannot interrupt R. Closing the runtime is the safe fallback.
        try { if (typeof webR.close === 'function') webR.close(); } catch (error) {}
        webR = null;
        loadPromise = null;
        running = false;
      },
      reset: function () {
        if (webR && typeof webR.close === 'function') webR.close();
        webR = null;
        loadPromise = null;
        running = false;
      },
      isReady: function () { return !!webR; }
    };
  }

  root.RuntimeR = { create: createAdapter };
})(window);
