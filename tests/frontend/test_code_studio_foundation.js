const assert = require('assert');

global.window = {
  SCWBCodeStudio: {},
  localStorage: {
    _data: new Map(),
    getItem(key) { return this._data.has(key) ? this._data.get(key) : null; },
    setItem(key, value) { this._data.set(key, String(value)); },
  },
};

require('../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/filesystem.js');
require('../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/session.js');
require('../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/runtime-registry.js');
require('../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/runtime-manager.js');
require('../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/terminal.js');

(async () => {
  const fsApi = window.SCWBCodeStudio.FileSystem;
  assert.strictEqual(fsApi.normalizePath('/src/../data/example.csv'), '/data/example.csv');
  assert.strictEqual(fsApi.resolvePath('/src', '../README.md'), '/README.md');
  assert.strictEqual(fsApi.dirname('/src/main.js'), '/src');
  assert.strictEqual(fsApi.basename('/src/main.js'), 'main.js');

  const projectFs = fsApi.create('node-test');
  await projectFs.init();
  assert.strictEqual(projectFs.getStorageMode(), 'localstorage');
  assert.ok(projectFs.read('/README.md').includes('Workbench v1.9.1'));
  await projectFs.mkdir('/models');
  await projectFs.write('/models/test.py', 'print(42)\n', 'python');
  assert.strictEqual(projectFs.read('/models/test.py'), 'print(42)\n');
  assert.ok(projectFs.list('/models').some((item) => item.name === 'test.py'));
  await projectFs.remove('/models', true);
  assert.strictEqual(projectFs.exists('/models/test.py'), false);
  assert.ok(JSON.parse(projectFs.exportProject()).files['/src/main.js']);

  const parse = window.SCWBCodeStudio.Terminal.parseCommand;
  assert.deepStrictEqual(parse('echo "hello world" > notes.txt'), ['echo', 'hello world', '>', 'notes.txt']);
  assert.deepStrictEqual(parse("edit 'src/main.js'"), ['edit', 'src/main.js']);

  const session = window.SCWBCodeStudio.Session.create('test');
  session.addHistory('pwd');
  session.addHistory('pwd');
  session.addHistory('ls');
  assert.deepStrictEqual(session.get('history'), ['pwd', 'ls']);

  const runtimes = window.SCWBCodeStudio.RuntimeRegistry.all();
  assert.ok(runtimes.some((runtime) => runtime.id === 'python'));
  assert.ok(runtimes.some((runtime) => runtime.id === 'go'));
  assert.deepStrictEqual(window.SCWBCodeStudio.RuntimeRegistry.browser().map((runtime) => runtime.id), ['javascript', 'python', 'r', 'sql']);
  assert.strictEqual(window.SCWBCodeStudio.RuntimeManager.detectRuntime('/src/analysis.py'), 'python');
  assert.strictEqual(window.SCWBCodeStudio.RuntimeManager.detectRuntime('/src/query.sql'), 'sql');
  assert.throws(() => window.SCWBCodeStudio.RuntimeManager.validate('javascript', 'fetch("https://example.com")', { maxSourceBytes: 1000 }), /network/i);
  assert.throws(() => window.SCWBCodeStudio.RuntimeManager.validate('python', 'import requests', { maxSourceBytes: 1000 }), /network/i);
  assert.ok(projectFs.read('/src/analysis.py').includes('workbench'));
  assert.strictEqual(session.get('activePanel'), 'code');
  assert.ok(projectFs.read('/src/analysis.R').includes('plot'));
  assert.ok(projectFs.read('/src/query.sql').includes('read_csv_auto'));

  console.log('Code Studio foundation frontend tests passed.');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
