const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(
  path.join(__dirname, "..", "app-shell.js"), "utf8"
);

function functionBody(name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const start = source.search(
    new RegExp(`(?:async\\s+)?function\\s+${escaped}\\s*\\(`)
  );
  assert.ok(start >= 0, `Missing function: ${name}`);

  const open = source.indexOf("{", start);
  let depth = 0;

  for (let i = open; i < source.length; i++) {
    if (source[i] === "{") depth++;
    if (source[i] === "}") {
      depth--;
      if (depth === 0) return source.slice(open, i + 1);
    }
  }
  throw new Error(`Unclosed function: ${name}`);
}

test("graph creation uses persistent API", () => {
  const body = functionBody("createGraphStudy");
  assert.match(body, /graph-studio\/graphs/);
  assert.match(body, /method:"POST"/);
  assert.match(body, /state\.activeGraphId/);
});

test("graph updates use persistent API", () => {
  const body = functionBody("saveActiveGraph");
  assert.match(body, /method:"PATCH"/);
  assert.match(body, /state\.activeGraphId/);
});

test("saved graphs are loaded by project", () => {
  const body = functionBody("loadSavedGraphs");
  assert.match(body, /state\.projectId/);
  assert.match(body, /projects\/\$\{encodeURIComponent\(state\.projectId\)\}\/graphs/);
});

test("graph series inputs include scientific settings", () => {
  const body = functionBody("graphSeriesDraft");
  for (const field of [
    "expression", "variable", "visible",
    "roots", "critical", "derivative", "integral"
  ]) {
    assert.ok(
      body.includes(`[data-${field}]`),
      `Missing series field: ${field}`
    );
  }
});

test("graph creation preserves session association", () => {
  const body = functionBody("createGraphStudy");
  assert.match(body, /researchSessionId:state\.researchSessionId/);
  assert.match(body, /recordSessionActivity/);
});

test("saved graph rendering uses persistent graph ID", () => {
  const body = functionBody("renderSavedGraph");
  assert.match(body, /state\.activeGraphId/);
  assert.match(body, /\/render/);
  assert.match(body, /method:"POST"/);
});

test("graph switching reloads persisted objects", () => {
  const body = functionBody("activateGraphStudy");
  assert.match(body, /loadActiveGraph/);
  assert.match(body, /renderSavedGraph/);
});

test("graph annotations use persistent API", () => {
  const body = functionBody("annotateActiveGraph");
  assert.match(body, /\/annotations/);
  assert.match(body, /method:"POST"/);
});
