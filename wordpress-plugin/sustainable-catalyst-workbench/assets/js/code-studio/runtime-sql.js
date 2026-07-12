(function (window) {
  'use strict';
  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function safeValue(value) {
    if (typeof value === 'bigint') return String(value);
    if (value instanceof Date) return value.toISOString();
    if (value && typeof value === 'object') {
      try { return JSON.parse(JSON.stringify(value, function (key, item) { return typeof item === 'bigint' ? String(item) : item; })); }
      catch (error) { return String(value); }
    }
    return value;
  }

  function createAdapter(config, callbacks) {
    let duckdb = null;
    let db = null;
    let worker = null;
    let connection = null;
    let loadPromise = null;
    let running = false;

    function load() {
      if (loadPromise) return loadPromise;
      loadPromise = import(config.moduleUrl).then(async function (module) {
        duckdb = module;
        const bundles = duckdb.getJsDelivrBundles();
        const bundle = await duckdb.selectBundle(bundles);
        const workerUrl = URL.createObjectURL(new Blob(['importScripts("' + bundle.mainWorker + '");'], { type: 'text/javascript' }));
        worker = new Worker(workerUrl);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
        URL.revokeObjectURL(workerUrl);
        connection = await db.connect();
        return { id: 'sql', version: config.version || 'DuckDB-Wasm' };
      }).catch(function (error) {
        loadPromise = null;
        throw error;
      });
      return loadPromise;
    }

    async function syncFiles(files) {
      for (const path of Object.keys(files || {})) {
        const lower = path.toLowerCase();
        if (!(lower.endsWith('.csv') || lower.endsWith('.json') || lower.endsWith('.ndjson') || lower.endsWith('.txt'))) continue;
        const name = String(path).replace(/^\/+/, '');
        try { if (db.dropFile) await db.dropFile(name); } catch (error) {}
        await db.registerFileText(name, String(files[path] == null ? '' : files[path]));
      }
    }

    return {
      id: 'sql',
      load: load,
      run: function (job) {
        return load().then(async function () {
          if (running) throw new Error('A SQL job is already running.');
          running = true;
          const started = Date.now();
          const result = { ok: false, runtime: 'sql', output: [], tables: [], charts: [], artifacts: [], durationMs: 0 };
          try {
            await syncFiles(job.files || {});
            const table = await connection.query(String(job.code || ''));
            const columns = table.schema.fields.map(function (field) { return field.name; });
            const rows = table.toArray().map(function (row) {
              const item = {};
              columns.forEach(function (column) { item[column] = safeValue(row[column]); });
              return item;
            });
            result.tables.push({ name: job.path || 'SQL result', columns: columns, data: rows });
            const summary = rows.length + ' row' + (rows.length === 1 ? '' : 's') + ' returned.';
            result.output.push({ stream: 'stdout', text: summary });
            callbacks.stream('stdout', summary);
            result.ok = true;
          } catch (error) {
            result.error = error && (error.stack || error.message) ? (error.stack || error.message) : String(error);
          } finally {
            running = false;
          }
          result.durationMs = Date.now() - started;
          return result;
        });
      },
      stop: function () {
        if (!running) return;
        this.reset();
      },
      reset: function () {
        try { if (connection) connection.close(); } catch (error) {}
        try { if (db && db.terminate) db.terminate(); } catch (error) {}
        try { if (worker) worker.terminate(); } catch (error) {}
        duckdb = null;
        db = null;
        worker = null;
        connection = null;
        loadPromise = null;
        running = false;
      },
      isReady: function () { return !!db; }
    };
  }

  root.RuntimeSQL = { create: createAdapter };
})(window);
