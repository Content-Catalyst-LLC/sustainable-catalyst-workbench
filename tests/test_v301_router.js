'use strict';
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');

const expected = ['unified','projects','library','research','embedded','electronics','robotics','instrumentation','simulation','runtime','visualization','experiments','documentation','recovery'];

class ClassList {
  constructor() { this.values = new Set(); }
  add(name) { this.values.add(name); }
  remove(name) { this.values.delete(name); }
  toggle(name, force) { if (force === undefined) force = !this.values.has(name); force ? this.values.add(name) : this.values.delete(name); return force; }
  contains(name) { return this.values.has(name); }
}

class BaseElement {
  constructor(attrs = {}) { this.attrs = Object.assign({}, attrs); this.classList = new ClassList(); this.hidden = false; this.disabled = false; this.nodeType = 1; this.events = []; }
  getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  dispatchEvent(event) { this.events.push(event.type); return true; }
  focus() { this.focused = true; }
}

class Tab extends BaseElement {
  constructor(key) { super({'data-scwb-primary-tab': key}); this.em = { textContent: 'Ready' }; }
  querySelector(selector) { return selector === 'em' ? this.em : null; }
}

class Mount extends BaseElement {
  constructor() { super({'data-scwb-module-mount': ''}); this.textContent = 'Studio interface'; }
  querySelector(selector) {
    if (selector.includes('offline')) return null;
    return { interactive: true };
  }
}

class Panel extends BaseElement {
  constructor(key) { super({'data-scwb-primary-panel': key}); this.mount = new Mount(); }
  querySelector(selector) {
    if (selector.includes('module-error') || selector.includes('data-scwb-error')) return null;
    if (selector === '[data-scwb-module-mount]') return this.mount;
    return null;
  }
  querySelectorAll() { return []; }
}

class Root extends BaseElement {
  constructor() {
    super({'data-scwb-initial':'unified','data-scwb-project':'default','data-scwb-remember':'false','aria-busy':'true'});
    this.tabs = expected.map((key) => new Tab(key));
    this.panels = expected.map((key) => new Panel(key));
    this.status = { textContent: '' };
    this.activation = { innerHTML: '', classList: new ClassList() };
  }
  querySelectorAll(selector) {
    if (selector === '[data-scwb-primary-tab]:not([disabled])') return this.tabs.filter((tab) => !tab.disabled);
    if (selector === '[data-scwb-primary-panel]') return this.panels;
    if (selector === '[data-scwb-primary]') return [this];
    return [];
  }
  querySelector(selector) {
    if (selector === '[data-scwb-primary-js-status]') return this.status;
    if (selector === '[data-scwb-activation]') return this.activation;
    return null;
  }
}

const root = new Root();
const listeners = {};
const windowListeners = {};
const document = {
  readyState: 'complete',
  body: { className: 'wp-block-page' },
  documentElement: {},
  querySelectorAll(selector) { return selector === '[data-scwb-primary]' ? [root] : []; },
  querySelector() { return null; },
  addEventListener(type, callback) { listeners[type] = callback; }
};

class Event { constructor(type) { this.type = type; } }
class CustomEvent extends Event { constructor(type, options = {}) { super(type); this.detail = options.detail; this.bubbles = options.bubbles; } }
class MutationObserver { constructor(callback) { this.callback = callback; } observe() {} }

const local = {};
const localStorage = { setItem(k,v){ local[k]=v; }, getItem(k){ return local[k] || null; } };
const windowObject = {
  location: { hash: '' },
  history: { replaceState(_a,_b,value){ windowObject.location.hash = value; } },
  addEventListener(type, callback){ windowListeners[type] = callback; },
  dispatchEvent(){ return true; },
  setTimeout(callback){ callback(); },
  Event,
  CustomEvent,
  MutationObserver,
  ResizeObserver: function(){},
};

const context = {
  window: windowObject,
  document,
  localStorage,
  MutationObserver,
  Event,
  CustomEvent,
  console,
  decodeURIComponent,
  encodeURIComponent,
};
windowObject.window = windowObject;

const source = fs.readFileSync(path.join(__dirname, '..', 'wordpress-plugin', 'sustainable-catalyst-workbench', 'assets', 'js', 'scwb-primary-repair.js'), 'utf8');
vm.runInNewContext(source, context, { filename: 'scwb-primary-repair.js' });

const router = windowObject.SCWBPrimaryRouter;
assert(router, 'Router was not exported');
assert.strictEqual(router.version, '3.2.0');
assert.deepStrictEqual(Array.from(router.expectedStudios), expected);
assert.strictEqual(root.getAttribute('data-scwb-active'), 'unified');
assert.strictEqual(root.getAttribute('aria-busy'), 'false');
assert(root.classList.contains('is-ready'));
assert.strictEqual(root.getAttribute('data-scwb-audit-count'), '14');

for (const key of expected) {
  assert.strictEqual(router.activate(root, key, { hash: false }), true, `Could not activate ${key}`);
  assert.strictEqual(root.getAttribute('data-scwb-active'), key);
  for (const panel of root.panels) {
    const active = panel.getAttribute('data-scwb-primary-panel') === key;
    assert.strictEqual(panel.hidden, !active, `Panel visibility mismatch for ${panel.getAttribute('data-scwb-primary-panel')}`);
    assert.strictEqual(panel.getAttribute('aria-hidden'), active ? 'false' : 'true');
    assert.strictEqual(panel.getAttribute('data-scwb-panel-state'), 'ready');
  }
}

assert(root.status.textContent.includes('keyboard'));
console.log(`Workbench v3.2.0 router regression passed for ${expected.length} studios.`);
