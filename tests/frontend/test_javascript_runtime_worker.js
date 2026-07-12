const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

(async () => {
  const workerPath = path.resolve(__dirname, '../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/workers/javascript-worker.js');
  const source = fs.readFileSync(workerPath, 'utf8');
  const messages = [];
  const self = {
    postMessage(message) { messages.push(message); },
  };
  const context = vm.createContext({
    self,
    Error,
    Object,
    Array,
    JSON,
    String,
    Number,
    Boolean,
    Date,
    Math,
    Promise,
    RegExp,
    setTimeout,
    clearTimeout,
  });
  vm.runInContext(source, context, { filename: 'javascript-worker.js' });
  assert.strictEqual(typeof self.onmessage, 'function');

  await self.onmessage({
    data: {
      type: 'run',
      path: '/src/smoke.js',
      files: { '/data/value.txt': '42' },
      code: [
        'console.log("worker", workbench.readFile("/data/value.txt"));',
        'workbench.table("Table", [{ x: 1 }]);',
        'workbench.chart("Chart", { type: "line", x: [1], y: [2] });',
        'workbench.artifact("smoke.txt", "ok");',
        'return 7;'
      ].join('\n'),
    },
  });

  const done = messages.find((message) => message.type === 'done');
  assert.ok(done, 'worker should emit a done message');
  assert.strictEqual(done.ok, true);
  assert.strictEqual(done.result, 7);
  assert.strictEqual(done.tables.length, 1);
  assert.strictEqual(done.charts.length, 1);
  assert.strictEqual(done.artifacts.length, 1);
  assert.ok(messages.some((message) => message.type === 'stream' && /worker 42/.test(message.text)));

  console.log('JavaScript runtime worker tests passed.');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
