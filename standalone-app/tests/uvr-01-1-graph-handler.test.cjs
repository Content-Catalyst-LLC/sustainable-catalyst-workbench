// UVR-01.1 structural regression guard for Graph Studio event wiring.
// Run: node --test standalone-app/tests/uvr-01-1-graph-handler.test.cjs
// This is a source-level test, not an API/browser integration test.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "app-shell.js"), "utf8");

test("Graph Studio series controls are defined in the dynamic template", () => {
  assert.match(source, /data-graph-series/);
  assert.match(source, /data-expression/);
  assert.match(source, /data-variable/);
  assert.match(source, /id="graph-series-list"/);
});

test("new graph Render uses the Graph Studio creation path, not obsolete inputs", () => {
  assert.match(source, /else createGraphStudy\(\)\.catch\(e=>toast\(String\(e\),true\)\);/);
  assert.doesNotMatch(source, /else renderGraph\(\);/);
  assert.match(source, /async function createGraphStudy\(\)/);
  assert.match(source, /const series=graphSeriesDraft\(\)/);
});

test("existing saved graph Render retains the saved render endpoint", () => {
  assert.match(source, /if\(state\.activeGraphId\)renderSavedGraph\(\)/);
  assert.match(source, /async function renderSavedGraph\(\)/);
  assert.match(source, /graph-studio\/graphs\/\$\{encodeURIComponent\(state\.activeGraphId\)\}\/render/);
});

test("save control remains separately wired", () => {
  assert.match(source, /id="save-graph-study"/);
  assert.match(source, /if\(sg\)sg\.onclick=\(\)=>saveActiveGraph\(\)/);
});
