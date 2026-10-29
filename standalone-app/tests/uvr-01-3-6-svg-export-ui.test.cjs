const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "app-shell.js"), "utf8");

test("Graph Studio exposes export only for a persisted graph", () => {
  assert.match(source, /id="export-graph-svg"/);
  assert.match(source, /id="export-graph-svg"[^>]*state\.activeGraphId\?"":"disabled"/);
});

test("SVG export is bound to the authenticated saved-graph handler", () => {
  assert.match(source, /function downloadActiveGraphSvg\(\)/);
  assert.match(source, /id="export-graph-svg"/);
  assert.match(source, /eg\.onclick=\(\)=>downloadActiveGraphSvg\(\)\.catch/);
  assert.match(source, /encodeURIComponent\(graphId\)\}\/export\.svg/);
  assert.match(source, /Authorization:`Bearer \$\{state\.token\}`/);
  assert.match(source, /if\(!response\.ok\)throw new Error/);
});

test("SVG export enforces response format and releases object URL", () => {
  assert.match(source, /content-type/);
  assert.match(source, /image\/svg\+xml/);
  assert.match(source, /if\(!blob\.size\)/);
  assert.match(source, /link\.download=`workbench-graph-/);
  assert.match(source, /URL\.revokeObjectURL\(url\)/);
});
