const assert = require('assert');
const fs = require('fs');
const path = require('path');

const php = fs.readFileSync(path.resolve(__dirname, '../../wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php'), 'utf8');
const js = fs.readFileSync(path.resolve(__dirname, '../../wordpress-plugin/sustainable-catalyst-workbench/assets/js/code-studio/code-studio.js'), 'utf8');
const css = fs.readFileSync(path.resolve(__dirname, '../../wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-code-studio.css'), 'utf8');

[
  'data-scwb-code-panel="code"',
  'data-scwb-run-output',
  'data-scwb-run-active',
  'data-scwb-file-select',
  'data-scwb-line-numbers',
  'Advanced Console'
].forEach((marker) => assert.ok(php.includes(marker), `missing PHP marker: ${marker}`));

assert.ok(js.includes('function runActiveFile()'), 'direct editor-to-runtime function missing');
assert.ok(js.includes("event.key === 'Enter'"), 'Ctrl/Cmd+Enter shortcut missing');
assert.ok(js.includes("activatePanel(terminalOnly ? 'terminal' : 'code')"), 'Code panel is not the default');
assert.ok(css.includes('.scwb-code-lab-grid'), 'editor/output grid CSS missing');
assert.ok(css.includes('.scwb-run-output'), 'direct output pane CSS missing');

console.log('Editor-first Code Studio contract tests passed.');
