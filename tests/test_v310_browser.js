const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

class MemoryStorage {
  constructor() { this.data = new Map(); }
  setItem(k,v) { this.data.set(String(k), String(v)); }
  getItem(k) { return this.data.has(String(k)) ? this.data.get(String(k)) : null; }
  removeItem(k) { this.data.delete(String(k)); }
  key(i) { return Array.from(this.data.keys())[i] || null; }
  get length() { return this.data.size; }
}
const localStorage = new MemoryStorage();
const document = {
  readyState: 'complete',
  documentElement: {},
  body: { appendChild() {} },
  querySelectorAll() { return []; },
  addEventListener() {},
  dispatchEvent() {},
  createElement() { return {click(){}, remove(){}}; }
};
const windowObject = {
  SCWBV310Config: {authenticated:false,currentUser:0,autosaveDelay:1800,maxLocalRevisions:50,restUrl:'/wp-json/scwb/v1',nonce:''},
  setTimeout,
  clearTimeout,
  addEventListener() {},
  dispatchEvent() {},
  confirm() { return true; },
  prompt() { return 'Test project'; },
  location: {hash:''},
  URL: {createObjectURL(){return 'blob:test';}, revokeObjectURL(){}},
};
class CustomEvent { constructor(type, options={}) { this.type=type; this.detail=options.detail; this.bubbles=options.bubbles; } }
const context = {window:windowObject,document,localStorage,CustomEvent,Blob:class Blob{},URL:windowObject.URL,console,Promise,Date,JSON,Set,Map,Array,String,Number,Object,Math,Error,TextEncoder:undefined,fetch(){return Promise.reject(new Error('not used'));}};
windowObject.window = windowObject;
windowObject.document = document;
windowObject.localStorage = localStorage;
windowObject.CustomEvent = CustomEvent;

const source = fs.readFileSync(path.join(__dirname, '..', 'wordpress-plugin', 'sustainable-catalyst-workbench', 'assets', 'js', 'sc-workbench-v310.js'), 'utf8');
for (const marker of ['sc-workbench-persistent-project/1.0','sc-workbench-project-revision/1.0','sc-workbench-project-workspace-package/1.0','autosaveDelay','saveStudioRecord','scwb:project-changed','browser-local','WordPress']) assert(source.includes(marker), `Missing marker: ${marker}`);
vm.runInNewContext(source, context, {filename:'sc-workbench-v310.js'});
const api = windowObject.SCWBProjectWorkspace;
assert(api, 'Persistent workspace API was not exported');
assert.strictEqual(api.version, '3.1.0');
const project = api.newProject('Climate Sensor');
assert.strictEqual(project.title, 'Climate Sensor');
assert.strictEqual(project.schema, 'sc-workbench-persistent-project/1.0');

(async () => {
  const saved = await api.saveProject(project);
  assert(saved.content_hash, 'Saved project should have a content hash');
  assert.strictEqual(api.readProjects().length, 1);
  api.setActiveProject(saved.project_id);
  assert.strictEqual(api.getActiveProject().project_id, saved.project_id);
  const revision = await api.createRevision(saved, 'test-snapshot');
  assert.strictEqual(revision.schema, 'sc-workbench-project-revision/1.0');
  assert.strictEqual(api.readRevisions(saved.project_id).length, 1);
  const updated = await api.saveStudioRecord('simulation', {model:'first-order'});
  assert.strictEqual(updated.studio_records.simulation.data.model, 'first-order');
  console.log('Workbench v3.1.0 browser persistence regression passed.');
})().catch((error) => { console.error(error); process.exit(1); });
