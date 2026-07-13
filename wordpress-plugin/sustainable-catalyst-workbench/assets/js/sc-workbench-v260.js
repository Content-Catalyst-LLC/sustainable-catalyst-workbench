(function () {
  'use strict';

  const CONFIG = window.SCWBV260 || { version: '2.6.0', runnerDefaultUrl: 'http://127.0.0.1:8787', storagePrefix: 'scwb-v260:' };
  const LANGUAGES = ['python', 'javascript', 'r', 'sql', 'go', 'c', 'cpp', 'rust', 'haskell', 'assembly'];

  function fields(root) {
    const data = {};
    root.querySelectorAll('[data-scwb-v260-field]').forEach((node) => { data[node.dataset.scwbV260Field] = node.value; });
    return data;
  }
  function storageKey(root) { return CONFIG.storagePrefix + (root.dataset.scwbV260Project || 'default') + ':' + root.dataset.scwbV260Panel; }
  function parseJSON(value, fallback) { try { return JSON.parse(value); } catch (error) { return fallback; } }
  function numbers(value) { return String(value || '').split(/[\s,;]+/).map(Number).filter(Number.isFinite); }
  function finite(value, fallback) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
  function round(value, digits) { if (!Number.isFinite(value)) return value; return Number(value.toFixed(digits == null ? 12 : digits)); }
  function mean(values) { return values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1); }
  function variance(values) { if (values.length < 2) return 0; const center = mean(values); return values.reduce((sum, value) => sum + (value - center) ** 2, 0) / (values.length - 1); }
  function kahan(values) { let sum = 0, correction = 0; values.forEach((value) => { const adjusted = value - correction; const next = sum + adjusted; correction = (next - sum) - adjusted; sum = next; }); return sum; }
  function pairwise(values) { if (values.length < 2) return values[0] || 0; const middle = Math.floor(values.length / 2); return pairwise(values.slice(0, middle)) + pairwise(values.slice(middle)); }
  function normalizeText(value) { return String(value == null ? '' : value).trim().replace(/\r\n/g, '\n').replace(/[ \t]+$/gm, ''); }
  function canonicalJSON(value) { if (Array.isArray(value)) return value.map(canonicalJSON); if (value && typeof value === 'object') return Object.keys(value).sort().reduce((out, key) => { out[key] = canonicalJSON(value[key]); return out; }, {}); return value; }
  function scalarDifference(actual, expected) {
    const a = Number(actual), e = Number(expected);
    if (!Number.isFinite(a) || !Number.isFinite(e)) return { comparable: false, absolute: null, relative: null };
    const absolute = Math.abs(a - e); return { comparable: true, absolute, relative: absolute / Math.max(Math.abs(e), 1e-30) };
  }
  function download(name, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2) + '\n'], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = name; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }
  function show(root, payload) {
    root._scwbV260Last = payload;
    const result = root.querySelector('[data-scwb-v260-results]');
    result.replaceChildren();
    const pre = document.createElement('pre'); pre.textContent = JSON.stringify(payload, null, 2); result.appendChild(pre);
  }
  function status(root, text) { const node = root.querySelector('[data-scwb-v260-status]'); if (node) node.textContent = text; }

  function expectedCalculation(calculation, input) {
    if (calculation === 'energy') return finite(input.power_kw, 0) * finite(input.hours, 0);
    if (calculation === 'dot_product') {
      const left = Array.isArray(input.left) ? input.left.map(Number) : [];
      const right = Array.isArray(input.right) ? input.right.map(Number) : [];
      return left.slice(0, Math.min(left.length, right.length)).reduce((sum, value, index) => sum + value * right[index], 0);
    }
    if (calculation === 'quadratic') {
      const a = finite(input.a, 1), b = finite(input.b, 0), c = finite(input.c, 0), discriminant = b * b - 4 * a * c;
      if (a === 0 || discriminant < 0) return [];
      return [(-b - Math.sqrt(discriminant)) / (2 * a), (-b + Math.sqrt(discriminant)) / (2 * a)].sort((x, y) => x - y);
    }
    const x = Array.isArray(input.x) ? input.x.map(Number) : [];
    const y = Array.isArray(input.y) ? input.y.map(Number) : [];
    const n = Math.min(x.length, y.length); if (n < 2) return { slope: null, intercept: null };
    const mx = mean(x.slice(0, n)), my = mean(y.slice(0, n));
    const sxx = x.slice(0, n).reduce((sum, value) => sum + (value - mx) ** 2, 0);
    const sxy = x.slice(0, n).reduce((sum, value, index) => sum + (value - mx) * (y[index] - my), 0);
    const slope = sxx ? sxy / sxx : 0; return { slope, intercept: my - slope * mx };
  }

  function compareValues(actual, expected, absTolerance, relTolerance) {
    if (Array.isArray(expected)) {
      if (!Array.isArray(actual) || actual.length !== expected.length) return { pass: false, reason: 'array-shape-mismatch' };
      const details = expected.map((value, index) => scalarDifference(actual[index], value));
      return { pass: details.every((item) => item.comparable && (item.absolute <= absTolerance || item.relative <= relTolerance)), details };
    }
    if (expected && typeof expected === 'object') {
      if (!actual || typeof actual !== 'object') return { pass: false, reason: 'object-shape-mismatch' };
      const details = {}; let pass = true;
      Object.keys(expected).forEach((key) => { details[key] = scalarDifference(actual[key], expected[key]); if (!details[key].comparable || (details[key].absolute > absTolerance && details[key].relative > relTolerance)) pass = false; });
      return { pass, details };
    }
    const detail = scalarDifference(actual, expected);
    return { pass: detail.comparable && (detail.absolute <= absTolerance || detail.relative <= relTolerance), detail };
  }

  function sourceTemplate(language, template, expression, projectName) {
    const safe = String(projectName || 'engineering-runtime-example').replace(/[^A-Za-z0-9_-]/g, '-');
    const expr = expression || 'power_kw * hours';
    const templates = {
      python: `"""${safe}: generated Workbench engineering calculation."""\n\ndef calculate(power_kw: float, hours: float) -> float:\n    return ${expr}\n\nif __name__ == "__main__":\n    result = calculate(2.5, 8.0)\n    print(f"{result:.12g}")\n`,
      javascript: `'use strict';\nfunction calculate(power_kw, hours) { return ${expr}; }\nconsole.log(calculate(2.5, 8.0).toPrecision(12));\n`,
      r: `calculate <- function(power_kw, hours) { ${expr} }\ncat(format(calculate(2.5, 8.0), digits=12), "\\n")\n`,
      sql: `WITH inputs(power_kw, hours) AS (VALUES (2.5, 8.0))\nSELECT printf('%.12g', ${expr}) AS result FROM inputs;\n`,
      go: `package main\nimport "fmt"\nfunc calculate(power_kw, hours float64) float64 { return ${expr} }\nfunc main(){ fmt.Printf("%.12g\\n", calculate(2.5,8.0)) }\n`,
      c: `#include <stdio.h>\ndouble calculate(double power_kw,double hours){ return ${expr}; }\nint main(void){ printf("%.12g\\n",calculate(2.5,8.0)); return 0; }\n`,
      cpp: `#include <iomanip>\n#include <iostream>\ndouble calculate(double power_kw,double hours){ return ${expr}; }\nint main(){ std::cout<<std::setprecision(12)<<calculate(2.5,8.0)<<'\\n'; }\n`,
      rust: `fn calculate(power_kw:f64,hours:f64)->f64{ ${expr} }\nfn main(){ println!("{:.12}",calculate(2.5,8.0)); }\n`,
      haskell: `calculate :: Double -> Double -> Double\ncalculate power_kw hours = ${expr}\nmain :: IO ()\nmain = print (calculate 2.5 8.0)\n`,
      assembly: `; ${safe} assembly profile\n; Select x86-64, ARM64, ARMv7, RISC-V, or AVR before implementation.\n; Define ABI, floating-point representation, calling convention, and test vectors.\n`,
    };
    const extensions = { python: 'py', javascript: 'js', r: 'R', sql: 'sql', go: 'go', c: 'c', cpp: 'cpp', rust: 'rs', haskell: 'hs', assembly: 'asm' };
    const files = {}; files['main.' + extensions[language]] = templates[language] || templates.python;
    files['README.md'] = `# ${safe}\n\nTemplate: ${template}\nLanguage: ${language}\nGenerated by Workbench v2.6.0. Validate units, dependencies, numeric precision, and runtime output.\n`;
    files['test-vectors.json'] = JSON.stringify({ schema: 'sc-workbench-runtime-test-vectors/1.0', cases: [{ inputs: { power_kw: 2.5, hours: 8 }, expected: 20 }] }, null, 2) + '\n';
    return files;
  }

  function analyze(root) {
    const panel = root.dataset.scwbV260Panel, data = fields(root), now = new Date().toISOString();
    if (panel === 'runtime') {
      show(root, { ok: true, schema: 'sc-workbench-runtime-plan/1.0', version: CONFIG.version, generatedAt: now, language: data.language, filename: data.filename, mode: data.execution_mode, limits: { timeoutSeconds: finite(data.timeout_seconds, 8), maxSourceBytes: 204800, maxOutputBytes: 262144 }, runner: { url: data.runner_url, pairedTokenPresent: Boolean(localStorage.getItem(CONFIG.storagePrefix + 'runner-token')) }, sourcePreview: data.source.slice(0, 1000), supportedLanguages: LANGUAGES, arbitraryShellEndpoint: false });
      return;
    }
    if (panel === 'equivalence') {
      const input = parseJSON(data.inputs, {}), outputs = parseJSON(data.outputs, {}), expected = expectedCalculation(data.calculation, input), absTolerance = Math.max(0, finite(data.absolute_tolerance, 1e-6)), relTolerance = Math.max(0, finite(data.relative_tolerance, 1e-6));
      const comparisons = {}; Object.keys(outputs).forEach((language) => { comparisons[language] = compareValues(outputs[language], expected, absTolerance, relTolerance); });
      const required = Object.keys(outputs); const pass = required.length > 0 && required.every((language) => comparisons[language].pass);
      show(root, { ok: pass, schema: 'sc-workbench-language-equivalence/1.0', version: CONFIG.version, generatedAt: now, calculation: data.calculation, inputs: input, expected, tolerances: { absolute: absTolerance, relative: relTolerance }, comparisons, findings: pass ? [{ severity: 'pass', code: 'all-results-equivalent' }] : [{ severity: 'warning', code: 'runtime-results-differ' }] });
      return;
    }
    if (panel === 'benchmark') {
      const values = numbers(data.values), naive = values.reduce((sum, value) => sum + value, 0), stable = kahan(values), pair = pairwise(values), spread = Math.max(naive, stable, pair) - Math.min(naive, stable, pair);
      show(root, { ok: values.length > 0, schema: 'sc-workbench-numerical-benchmark/1.0', version: CONFIG.version, generatedAt: now, benchmark: data.benchmark, sampleCount: values.length, repeats: Math.max(1, Math.floor(finite(data.repeats, 1000))), results: { naive: round(naive), kahan: round(stable), pairwise: round(pair), methodSpread: round(spread), sampleVariance: round(variance(values)) }, findings: spread === 0 ? [{ severity: 'pass', code: 'methods-agree' }] : [{ severity: 'warning', code: 'summation-order-sensitive', value: spread }] });
      return;
    }
    if (panel === 'templates') {
      const files = sourceTemplate(data.language, data.template, data.expression, data.project_name);
      show(root, { ok: true, schema: 'sc-workbench-multilanguage-project/1.0', version: CONFIG.version, generatedAt: now, project: data.project_name, language: data.language, template: data.template, files, validationChecklist: ['Confirm units and data types', 'Pin runtime and dependency versions', 'Run supplied test vector', 'Compare output against a second language', 'Review overflow and numerical stability'] });
      return;
    }
    if (panel === 'reproducibility') {
      const records = parseJSON(data.records, []), required = String(data.required_languages || '').split(',').map((value) => value.trim()).filter(Boolean), tolerance = Math.max(0, finite(data.tolerance, 1e-6));
      const present = new Set(records.map((record) => record.language)); const missing = required.filter((language) => !present.has(language)); let reference = records.length ? records[0].output : null;
      const comparisons = records.map((record) => {
        let pass = false, detail = null;
        if (data.comparison_mode === 'numeric') { detail = scalarDifference(record.output, reference); pass = detail.comparable && detail.absolute <= tolerance; }
        else if (data.comparison_mode === 'json') { const left = canonicalJSON(parseJSON(record.output, record.output)), right = canonicalJSON(parseJSON(reference, reference)); pass = JSON.stringify(left) === JSON.stringify(right); }
        else pass = normalizeText(record.output) === normalizeText(reference);
        return { language: record.language, runtime: record.runtime || '', durationMs: record.duration_ms, pass, detail };
      });
      const pass = records.length > 1 && missing.length === 0 && comparisons.every((item) => item.pass);
      show(root, { ok: pass, schema: 'sc-workbench-runtime-reproducibility/1.0', version: CONFIG.version, generatedAt: now, mode: data.comparison_mode, tolerance, requiredLanguages: required, missingLanguages: missing, reference, comparisons, runtimeVersionCoverage: records.filter((record) => record.runtime).length + '/' + records.length });
      return;
    }
    const findings = [], timeout = finite(data.timeout_seconds, 8), sourceBytes = finite(data.source_bytes, 0), outputBytes = finite(data.output_bytes, 0);
    if (data.consent !== 'yes') findings.push({ severity: 'error', code: 'explicit-consent-required' });
    if (timeout > 30) findings.push({ severity: 'warning', code: 'timeout-above-default-boundary' });
    if (sourceBytes > 204800) findings.push({ severity: 'error', code: 'source-limit-exceeded' });
    if (outputBytes > 262144) findings.push({ severity: 'error', code: 'output-limit-exceeded' });
    if (data.filesystem_mode === 'unrestricted') findings.push({ severity: 'error', code: 'unrestricted-filesystem-rejected' });
    if (data.network_access === 'required') findings.push({ severity: 'warning', code: 'network-not-provided-by-runner' });
    if (!findings.length) findings.push({ severity: 'pass', code: 'within-default-local-boundary' });
    show(root, { ok: !findings.some((item) => item.severity === 'error'), schema: 'sc-workbench-execution-audit/1.0', version: CONFIG.version, generatedAt: now, language: data.language, requested: { sourceBytes, timeoutSeconds: timeout, outputBytes, filesystemMode: data.filesystem_mode, networkAccess: data.network_access, consent: data.consent }, enforcedBoundary: { loopbackOnly: true, pairingRequired: true, originBoundToken: true, arbitraryShellEndpoint: false, maxSourceBytes: 204800, maxOutputBytes: 262144, temporaryWorkingDirectory: true }, findings });
  }

  async function connect(root) {
    const data = fields(root), base = (data.runner_url || CONFIG.runnerDefaultUrl).replace(/\/$/, ''), code = String(data.pairing_code || '').trim();
    status(root, 'Connecting…');
    try {
      let token = localStorage.getItem(CONFIG.storagePrefix + 'runner-token');
      if (code) {
        const response = await fetch(base + '/pair', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, origin: window.location.origin }) });
        const payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Pairing failed'); token = payload.token; localStorage.setItem(CONFIG.storagePrefix + 'runner-token', token);
      }
      if (!token) throw new Error('Enter the one-time pairing code shown by the local runner.');
      const response = await fetch(base + '/multi-language-tools', { headers: { Authorization: 'Bearer ' + token } });
      const payload = await response.json(); if (!response.ok) throw new Error(payload.error || 'Runtime discovery failed');
      status(root, 'Local runner paired'); show(root, payload);
    } catch (error) { status(root, 'Runner unavailable'); show(root, { ok: false, error: error.message, runnerUrl: base }); }
  }

  function initialize(root) {
    const saved = parseJSON(localStorage.getItem(storageKey(root)), null);
    if (saved && saved.fields) root.querySelectorAll('[data-scwb-v260-field]').forEach((node) => { if (Object.prototype.hasOwnProperty.call(saved.fields, node.dataset.scwbV260Field)) node.value = saved.fields[node.dataset.scwbV260Field]; });
    root.addEventListener('click', (event) => {
      const button = event.target.closest('[data-scwb-v260-action]'); if (!button) return;
      const action = button.dataset.scwbV260Action;
      if (action === 'analyze') analyze(root);
      else if (action === 'connect') connect(root);
      else if (action === 'save') { const record = { version: CONFIG.version, savedAt: new Date().toISOString(), fields: fields(root), result: root._scwbV260Last || null }; localStorage.setItem(storageKey(root), JSON.stringify(record)); status(root, 'Saved in this browser'); }
      else if (action === 'export') download('workbench-v260-' + root.dataset.scwbV260Panel + '.json', root._scwbV260Last || { version: CONFIG.version, fields: fields(root) });
    });
  }
  document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('[data-scwb-v260-panel]').forEach(initialize));
}());
