const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const storage = new Map();
const document = {
  readyState: 'complete',
  documentElement: {},
  body: { appendChild() {} },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement() { return { click() {}, remove() {} }; }
};
const localStorage = {
  setItem(key, value) { storage.set(key, value); },
  getItem(key) { return storage.has(key) ? storage.get(key) : null; },
  removeItem(key) { storage.delete(key); }
};
const URLObject = { createObjectURL() { return 'blob:test'; }, revokeObjectURL() {} };
const windowObject = {
  SCWBV400Config: { authenticated: false, restUrl: '/wp-json/scwb/v1' },
  setTimeout,
  clearTimeout,
  URL: URLObject,
  addEventListener() {}
};
const context = {
  window: windowObject,
  document,
  localStorage,
  Blob: class Blob {},
  URL: URLObject,
  navigator: {},
  console,
  Promise,
  Date,
  JSON,
  Set,
  Map,
  Array,
  String,
  Number,
  Object,
  Math,
  Error,
  CustomEvent: function (type, options) { this.type = type; this.detail = options && options.detail; },
  MutationObserver: undefined
};
Object.assign(windowObject, { window: windowObject, document, localStorage });
const source = fs.readFileSync(path.join(__dirname, '..', 'wordpress-plugin', 'sustainable-catalyst-workbench', 'assets', 'js', 'sc-workbench-v400.js'), 'utf8');
for (const marker of [
  'sc-workbench-connected-environment-',
  "version: VERSION",
  'automaticPublicationAuthorized: false',
  'automaticDeviceControlAuthorized: false',
  'remoteShellAllowed: false'
]) assert(source.includes(marker), `Missing marker: ${marker}`);
vm.runInNewContext(source, context, { filename: 'sc-workbench-v400.js' });
const api = windowObject.SCWBConnectedWorkbench;
assert(api, 'API not exported');
assert.strictEqual(api.version, '4.0.0');
assert.strictEqual(Array.from(api.platforms).length, 6);
assert.strictEqual(Array.from(api.capabilities).length, 10);
assert.strictEqual(api.automaticPublicationAuthorized, false);
assert.strictEqual(api.remoteShellAllowed, false);
console.log('Workbench v4.0.0 browser connected environment regression passed.');
