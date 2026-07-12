/* Sustainable Catalyst Workbench v1.9.1 — isolated JavaScript browser worker */
(function () {
  'use strict';

  function serialize(value, depth) {
    const level = depth || 0;
    if (level > 4) return '[Maximum depth]';
    if (value === undefined) return 'undefined';
    if (value === null) return null;
    if (typeof value === 'bigint') return String(value) + 'n';
    if (typeof value === 'function') return '[Function ' + (value.name || 'anonymous') + ']';
    if (value instanceof Error) return value.stack || value.message;
    if (Array.isArray(value)) return value.map(function (item) { return serialize(item, level + 1); });
    if (typeof value === 'object') {
      const out = {};
      Object.keys(value).slice(0, 200).forEach(function (key) { out[key] = serialize(value[key], level + 1); });
      return out;
    }
    return value;
  }

  function text(value) {
    if (typeof value === 'string') return value;
    try { return JSON.stringify(serialize(value), null, 2); }
    catch (error) { return String(value); }
  }

  function blockedNetwork() {
    throw new Error('Network access is disabled in the Workbench JavaScript runtime.');
  }

  self.fetch = blockedNetwork;
  self.WebSocket = blockedNetwork;
  self.EventSource = blockedNetwork;
  self.XMLHttpRequest = blockedNetwork;
  self.importScripts = blockedNetwork;

  self.onmessage = async function (event) {
    const message = event.data || {};
    if (message.type !== 'run') return;
    const files = Object.assign({}, message.files || {});
    const artifacts = [];
    const tables = [];
    const charts = [];
    const output = [];
    const started = Date.now();

    function emit(stream, values) {
      const line = values.map(text).join(' ');
      output.push({ stream: stream, text: line });
      self.postMessage({ type: 'stream', stream: stream, text: line });
    }

    const consoleProxy = {
      log: function () { emit('stdout', Array.prototype.slice.call(arguments)); },
      info: function () { emit('stdout', Array.prototype.slice.call(arguments)); },
      warn: function () { emit('stderr', Array.prototype.slice.call(arguments)); },
      error: function () { emit('stderr', Array.prototype.slice.call(arguments)); },
      table: function (data) { tables.push({ name: 'console.table', data: serialize(data) }); emit('stdout', [data]); },
      clear: function () { self.postMessage({ type: 'clear' }); }
    };

    const workbench = Object.freeze({
      readFile: function (path) {
        const normalized = String(path || '').startsWith('/') ? String(path) : '/' + String(path || '');
        if (!Object.prototype.hasOwnProperty.call(files, normalized)) throw new Error('Project file not found: ' + normalized);
        return files[normalized];
      },
      writeFile: function (path, content, mimeType) {
        const normalized = String(path || '').startsWith('/') ? String(path) : '/output/' + String(path || 'artifact.txt');
        artifacts.push({ path: normalized, content: String(content == null ? '' : content), mimeType: mimeType || 'text/plain', encoding: 'text' });
        return normalized;
      },
      table: function (name, data) {
        tables.push({ name: String(name || 'Result table'), data: serialize(data) });
      },
      chart: function (name, spec) {
        charts.push({ name: String(name || 'Chart'), kind: 'spec', spec: serialize(spec) });
      },
      artifact: function (name, content, mimeType) {
        const path = '/output/' + String(name || 'artifact.txt').replace(/^\/+/, '');
        artifacts.push({ path: path, content: String(content == null ? '' : content), mimeType: mimeType || 'text/plain', encoding: 'text' });
        return path;
      }
    });

    try {
      const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
      const source = '"use strict";\n' + String(message.code || '') + '\n//# sourceURL=' + String(message.path || 'workbench.js').replace(/\s/g, '_');
      const run = new AsyncFunction('console', 'workbench', 'fetch', 'WebSocket', 'EventSource', 'XMLHttpRequest', 'importScripts', source);
      const result = await run(consoleProxy, workbench, blockedNetwork, blockedNetwork, blockedNetwork, blockedNetwork, blockedNetwork);
      if (result !== undefined) emit('result', [result]);
      self.postMessage({
        type: 'done',
        ok: true,
        runtime: 'javascript',
        output: output,
        result: serialize(result),
        tables: tables,
        charts: charts,
        artifacts: artifacts,
        durationMs: Date.now() - started
      });
    } catch (error) {
      self.postMessage({
        type: 'done',
        ok: false,
        runtime: 'javascript',
        error: error && (error.stack || error.message) ? (error.stack || error.message) : String(error),
        output: output,
        tables: tables,
        charts: charts,
        artifacts: artifacts,
        durationMs: Date.now() - started
      });
    }
  };
})();
