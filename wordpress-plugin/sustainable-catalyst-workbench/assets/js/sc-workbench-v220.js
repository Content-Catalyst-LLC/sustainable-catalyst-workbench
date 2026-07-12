(() => {
  'use strict';

  const cfg = window.SCWBV220 || {};
  const q = (root, selector) => root.querySelector(selector);
  const field = (root, name) => q(root, `[data-scwb-v220-field="${name}"]`);
  const value = (root, name, fallback = '') => {
    const element = field(root, name);
    if (!element) return fallback;
    if (element.type === 'checkbox') return Boolean(element.checked);
    return element.value === '' ? fallback : element.value;
  };
  const action = (root, name, callback) => {
    const element = q(root, `[data-scwb-v220-action="${name}"]`);
    if (element) element.addEventListener('click', callback);
  };
  const project = root => root.dataset.scwbV220Project || 'default';
  const storageKey = (root, suffix) => `${cfg.storagePrefix || 'scwb-v220:'}${project(root)}:${suffix}`;
  const save = (root, suffix, data) => localStorage.setItem(storageKey(root, suffix), JSON.stringify(data));
  const load = (root, suffix, fallback) => {
    try {
      const raw = localStorage.getItem(storageKey(root, suffix));
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  };
  const setStatus = (root, text) => {
    const element = q(root, '[data-scwb-v220-status]');
    if (element) element.textContent = text;
  };
  const safeName = text => String(text || 'project').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'project';
  const esc = text => String(text ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const round = (number, digits = 4) => Number.isFinite(number) ? Number(number.toFixed(digits)) : null;
  const download = (filename, content, type = 'application/json;charset=utf-8') => {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const metricCards = metrics => Object.entries(metrics).map(([label, result]) => `<div class="scwb-v220__metric"><span>${esc(label)}</span><strong>${esc(result)}</strong></div>`).join('');

  function parseCSV(text) {
    const rows = [];
    let row = [];
    let cell = '';
    let quoted = false;
    const input = String(text || '').replace(/\r\n?/g, '\n');
    for (let index = 0; index < input.length; index += 1) {
      const character = input[index];
      if (quoted) {
        if (character === '"' && input[index + 1] === '"') {
          cell += '"';
          index += 1;
        } else if (character === '"') {
          quoted = false;
        } else {
          cell += character;
        }
      } else if (character === '"') {
        quoted = true;
      } else if (character === ',') {
        row.push(cell.trim());
        cell = '';
      } else if (character === '\n') {
        row.push(cell.trim());
        if (row.some(item => item !== '')) rows.push(row);
        row = [];
        cell = '';
      } else {
        cell += character;
      }
    }
    row.push(cell.trim());
    if (row.some(item => item !== '')) rows.push(row);
    if (rows.length < 2) throw new Error('CSV requires a header and at least one data row.');
    const headers = rows[0].map(header => header.trim());
    if (headers.some(header => !header)) throw new Error('CSV headers cannot be blank.');
    if (new Set(headers).size !== headers.length) throw new Error('CSV headers must be unique.');
    return rows.slice(1).map((cells, rowIndex) => {
      if (cells.length !== headers.length) throw new Error(`Row ${rowIndex + 2} has ${cells.length} columns; expected ${headers.length}.`);
      return Object.fromEntries(headers.map((header, index) => [header, cells[index]]));
    });
  }

  function toCSV(records, headers) {
    const quote = item => {
      const text = String(item ?? '');
      return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };
    return [headers.join(','), ...records.map(record => headers.map(header => quote(record[header])).join(','))].join('\n') + '\n';
  }

  async function runnerRequest(root, path, options = {}) {
    const base = String(cfg.runnerDefaultUrl || 'http://127.0.0.1:8787').replace(/\/$/, '');
    const tokenKey = `${cfg.v210StoragePrefix || 'scwb-v210:'}${project(root)}:runner-token`;
    const legacyTokenKey = `scwb-v200:${project(root)}:runner-token`;
    const token = sessionStorage.getItem(tokenKey) || sessionStorage.getItem(legacyTokenKey);
    const headers = {'Content-Type': 'application/json', ...(options.headers || {})};
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(base + path, {...options, headers});
    const data = await response.json().catch(() => ({ok: false, error: `HTTP ${response.status}`}));
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  function parseConstraintLines(text) {
    return String(text || '').split(/\n+/).map(line => line.trim()).filter(Boolean).map((line, index) => {
      const parts = line.split(',').map(item => item.trim());
      if (parts.length < 2) throw new Error(`Constraint line ${index + 1} needs at least signal and pin.`);
      return {signal: parts[0], pin: parts[1], ioStandard: parts[2] || '', clockMHz: parts[3] === '' || parts[3] === undefined ? null : Number(parts[3])};
    });
  }

  function boardConstraintText(board, constraints) {
    if (board === 'icebreaker') {
      return constraints.map(item => `set_io ${item.signal} ${item.pin}${item.ioStandard ? ` # ${item.ioStandard}` : ''}`).join('\n') + '\n';
    }
    if (board === 'ulx3s') {
      return constraints.map(item => `LOCATE COMP "${item.signal}" SITE "${item.pin}";${item.ioStandard ? `\nIOBUF PORT "${item.signal}" IO_TYPE=${item.ioStandard};` : ''}`).join('\n') + '\n';
    }
    return constraints.map(item => `set_property PACKAGE_PIN ${item.pin} [get_ports {${item.signal}}]${item.ioStandard ? `\nset_property IOSTANDARD ${item.ioStandard} [get_ports {${item.signal}}]` : ''}`).join('\n') + '\n';
  }

  function fpgaProject(root) {
    const name = safeName(value(root, 'fpga-project', 'fpga-project'));
    const language = value(root, 'fpga-language', 'verilog');
    const board = value(root, 'fpga-board', 'generic');
    const clockMHz = Number(value(root, 'fpga-clock', 12));
    const source = String(value(root, 'fpga-source')).trim();
    const constraints = parseConstraintLines(value(root, 'fpga-constraints'));
    if (!source) throw new Error('Top-level HDL is required.');
    if (!Number.isFinite(clockMHz) || clockMHz <= 0 || clockMHz > 2000) throw new Error('Clock frequency must be greater than 0 and no more than 2000 MHz.');
    const signals = constraints.map(item => item.signal);
    const pins = constraints.map(item => item.pin);
    const findings = [];
    if (new Set(signals).size !== signals.length) findings.push({severity: 'error', code: 'duplicate-signal', message: 'A signal appears more than once in the constraint set.'});
    if (new Set(pins).size !== pins.length) findings.push({severity: 'error', code: 'duplicate-pin', message: 'A physical pin is assigned more than once.'});
    if (!constraints.some(item => item.signal.toLowerCase().includes('clk'))) findings.push({severity: 'warning', code: 'clock-unidentified', message: 'No clock-like signal was identified in the constraints.'});
    const extension = language === 'vhdl' ? 'vhd' : language === 'systemverilog' ? 'sv' : 'v';
    const constraintExtension = board === 'icebreaker' ? 'pcf' : board === 'ulx3s' ? 'lpf' : 'xdc';
    const manifest = {
      schema: 'sc-workbench-fpga-project/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      project: {id: name, language, board, clockMHz, clockPeriodNs: round(1000 / clockMHz, 6)},
      constraints,
      findings,
      implementationFlow: board === 'icebreaker' ? ['yosys', 'nextpnr-ice40', 'icepack', 'openFPGALoader'] : ['simulate', 'synthesize', 'place-and-route', 'timing-review', 'program'],
      validationGates: ['lint', 'testbench', 'clock-domain review', 'constraints review', 'timing closure', 'resource review', 'hardware bring-up']
    };
    return {
      name,
      source,
      constraintsText: boardConstraintText(board, constraints),
      manifest,
      files: {
        [`rtl/top.${extension}`]: source + '\n',
        [`constraints/${name}.${constraintExtension}`]: boardConstraintText(board, constraints),
        'project.json': JSON.stringify(manifest, null, 2),
        'validation/implementation-review.md': '# Implementation review\n\nRecord tool versions, warnings, utilization, timing, clocks, CDC review, and hardware results.\n'
      }
    };
  }

  function firstNumber(text, expressions) {
    for (const expression of expressions) {
      const match = text.match(expression);
      if (match) return Number(String(match[1]).replace(/,/g, ''));
    }
    return null;
  }

  function analyzeFpgaReport(root) {
    const text = String(value(root, 'fpga-report')).trim();
    if (!text) throw new Error('Paste an implementation report first.');
    const targetClock = Number(value(root, 'fpga-clock', 0));
    const lines = text.split(/\n+/);
    const errors = lines.filter(line => /\berror\b/i.test(line) && !/0\s+errors?/i.test(line));
    const warnings = lines.filter(line => /\bwarning\b/i.test(line) && !/0\s+warnings?/i.test(line));
    const luts = firstNumber(text, [/(?:LUTs?|logic cells?|LCs?)\s*[:=]\s*([\d,]+)/i, /SB_LUT4\s+([\d,]+)/i]);
    const registers = firstNumber(text, [/(?:registers?|flip[- ]?flops?|DFFs?)\s*[:=]\s*([\d,]+)/i, /SB_DFF\w*\s+([\d,]+)/i]);
    const bram = firstNumber(text, [/(?:block RAM|BRAMs?|RAM blocks?)\s*[:=]\s*([\d,]+)/i, /SB_RAM40_4K\s+([\d,]+)/i]);
    const dsp = firstNumber(text, [/(?:DSPs?|multipliers?)\s*[:=]\s*([\d,]+)/i, /SB_MAC16\s+([\d,]+)/i]);
    const slackNs = firstNumber(text, [/(?:worst\s+)?slack\s*[:=]?\s*(-?[\d.]+)\s*ns/i]);
    const fmaxMHz = firstNumber(text, [/(?:max(?:imum)?\s+frequency|fmax)[^\d]*([\d.]+)\s*MHz/i, /([\d.]+)\s*MHz\s*\(PASS at/i]);
    const timingPass = slackNs !== null ? slackNs >= 0 : fmaxMHz !== null && targetClock > 0 ? fmaxMHz >= targetClock : null;
    return {
      schema: 'sc-workbench-fpga-implementation-review/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      toolReportFingerprint: simpleHash(text),
      targetClockMHz: targetClock || null,
      resources: {luts, registers, blockRam: bram, dsp},
      timing: {worstSlackNs: slackNs, fmaxMHz, pass: timingPass},
      diagnostics: {errorCount: errors.length, warningCount: warnings.length, errors: errors.slice(0, 30), warnings: warnings.slice(0, 50)},
      interpretationLimits: ['Report formats vary by tool and version.', 'Parsed values require confirmation against the original report.', 'Timing closure does not establish functional correctness, signal integrity, or safe hardware operation.']
    };
  }

  function simpleHash(text) {
    let hash = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return `fnv1a-${(hash >>> 0).toString(16).padStart(8, '0')}`;
  }

  function initFpga(root) {
    const sourceOutput = q(root, '[data-scwb-v220-fpga-source]');
    const reportOutput = q(root, '[data-scwb-v220-fpga-output]');
    const metrics = q(root, '[data-scwb-v220-fpga-metrics]');
    let bundle = load(root, 'fpga-project', null);
    let review = load(root, 'fpga-review', null);
    const renderBundle = item => { if (item && sourceOutput) sourceOutput.textContent = `${item.source}\n\n--- constraints ---\n${item.constraintsText}\n--- manifest ---\n${JSON.stringify(item.manifest, null, 2)}`; };
    const renderReview = item => {
      if (!item || !reportOutput || !metrics) return;
      reportOutput.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({LUTs: item.resources.luts ?? 'Not parsed', Registers: item.resources.registers ?? 'Not parsed', Warnings: item.diagnostics.warningCount, Timing: item.timing.pass === null ? 'Not parsed' : item.timing.pass ? 'PASS' : 'FAIL'});
    };
    renderBundle(bundle);
    renderReview(review);
    action(root, 'fpga-generate', () => {
      try {
        bundle = fpgaProject(root);
        save(root, 'fpga-project', bundle);
        renderBundle(bundle);
        setStatus(root, bundle.manifest.findings.some(item => item.severity === 'error') ? 'Constraint review required' : 'Project generated');
      } catch (error) {
        sourceOutput.textContent = `FPGA project generation failed: ${error.message}`;
        setStatus(root, 'Generation failed');
      }
    });
    action(root, 'fpga-analyze', () => {
      try {
        review = analyzeFpgaReport(root);
        save(root, 'fpga-review', review);
        renderReview(review);
        setStatus(root, review.diagnostics.errorCount || review.timing.pass === false ? 'Implementation review required' : 'Report analyzed');
      } catch (error) {
        reportOutput.textContent = `Report analysis failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Analysis failed');
      }
    });
    action(root, 'fpga-discover', async () => {
      try {
        const data = await runnerRequest(root, '/hardware-tools');
        reportOutput.textContent = JSON.stringify(data, null, 2);
        setStatus(root, `Runner ${data.version || 'online'}`);
      } catch (error) {
        reportOutput.textContent = `FPGA tool discovery failed: ${error.message}\nPair with the Local Go Runner first.`;
        setStatus(root, 'Runner unavailable');
      }
    });
    action(root, 'fpga-download', () => {
      try {
        bundle = bundle || fpgaProject(root);
        download(`${bundle.name}-fpga-project.json`, JSON.stringify({schema: 'sc-workbench-project-bundle/1.0', kind: 'fpga', manifest: bundle.manifest, implementationReview: review, files: bundle.files}, null, 2));
        setStatus(root, 'Project downloaded');
      } catch (error) {
        reportOutput.textContent = `Download failed: ${error.message}`;
      }
    });
  }

  function electronicsReview(root) {
    const name = safeName(value(root, 'elec-name', 'electronics-design'));
    const vin = Number(value(root, 'elec-vin'));
    const vlogic = Number(value(root, 'elec-vlogic'));
    const currentMa = Number(value(root, 'elec-current'));
    if (![vin, vlogic, currentMa].every(Number.isFinite) || vin <= 0 || vlogic <= 0 || currentMa < 0) throw new Error('Supply, logic rail, and current values must be valid non-negative numbers.');
    const blocks = parseCSV(`reference,type,description\n${value(root, 'elec-blocks')}`);
    const interfaces = String(value(root, 'elec-interfaces')).split(/\n+/).map(item => item.trim()).filter(Boolean);
    const types = blocks.map(item => item.type.toLowerCase());
    const findings = [];
    if (new Set(blocks.map(item => item.reference)).size !== blocks.length) findings.push({severity: 'error', code: 'duplicate-reference', message: 'Functional block references must be unique.'});
    if (vin > vlogic && !types.some(type => /regulator|converter|power/.test(type))) findings.push({severity: 'error', code: 'missing-regulation', message: 'The design steps down voltage but no regulator or converter block was identified.'});
    if (!types.some(type => /protection|esd|fuse|tvs/.test(type))) findings.push({severity: 'warning', code: 'protection-review', message: 'No dedicated input or interface protection block was identified.'});
    if (!types.some(type => /decoupling|capacitor|filter/.test(type))) findings.push({severity: 'warning', code: 'decoupling-review', message: 'No decoupling or filtering block was identified.'});
    if (!types.some(type => /test|debug|header/.test(type))) findings.push({severity: 'warning', code: 'test-access', message: 'No test or debug access block was identified.'});
    const inputPowerW = vin * currentMa / 1000;
    const loadPowerW = vlogic * currentMa / 1000;
    const linearLossW = Math.max(0, (vin - vlogic) * currentMa / 1000);
    if (linearLossW > 0.5) findings.push({severity: 'warning', code: 'thermal-regulator', message: `A linear-regulator assumption would dissipate approximately ${round(linearLossW, 3)} W; review converter choice and thermal limits.`});
    return {
      schema: 'sc-workbench-electronics-architecture/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      design: {id: name, vin, vlogic, estimatedLoadMa: currentMa, inputPowerW: round(inputPowerW, 4), loadPowerW: round(loadPowerW, 4), linearRegulatorLossW: round(linearLossW, 4)},
      blocks,
      interfaces,
      findings,
      reviewGates: ['power budget', 'absolute maximum ratings', 'protection', 'decoupling', 'grounding', 'signal integrity', 'thermal', 'EMC', 'test access', 'environmental conditions']
    };
  }

  function initElectronics(root) {
    const output = q(root, '[data-scwb-v220-elec-output]');
    const metrics = q(root, '[data-scwb-v220-elec-metrics]');
    let record = load(root, 'electronics-review', null);
    const render = item => {
      if (!item) return;
      output.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({Blocks: item.blocks.length, 'Input power': `${item.design.inputPowerW} W`, 'Linear loss': `${item.design.linearRegulatorLossW} W`, Findings: item.findings.length});
    };
    render(record);
    action(root, 'elec-review', () => {
      try {
        record = electronicsReview(root);
        save(root, 'electronics-review', record);
        render(record);
        setStatus(root, record.findings.some(item => item.severity === 'error') ? 'Architecture review required' : 'Architecture reviewed');
      } catch (error) {
        output.textContent = `Architecture review failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Review failed');
      }
    });
    action(root, 'elec-download', () => {
      try {
        record = record || electronicsReview(root);
        download(`${record.design.id}-electronics-architecture.json`, JSON.stringify(record, null, 2));
        setStatus(root, 'Record downloaded');
      } catch (error) {
        output.textContent = `Download failed: ${error.message}`;
      }
    });
  }

  function schematicModel(root) {
    const components = parseCSV(`reference,value,footprint,pins\n${value(root, 'sch-components')}`).map(component => ({...component, pins: component.pins.split('|').map(pin => pin.trim()).filter(Boolean)}));
    const netRows = String(value(root, 'sch-nets')).split(/\n+/).map(line => line.trim()).filter(Boolean).map((line, index) => {
      const parts = line.split(',').map(item => item.trim()).filter(Boolean);
      if (parts.length < 2) throw new Error(`Net line ${index + 1} needs a name and at least one endpoint.`);
      return {name: parts[0], endpoints: parts.slice(1)};
    });
    const findings = [];
    const references = components.map(item => item.reference);
    if (new Set(references).size !== references.length) findings.push({severity: 'error', code: 'duplicate-component-reference', message: 'Component references must be unique.'});
    if (new Set(netRows.map(item => item.name)).size !== netRows.length) findings.push({severity: 'error', code: 'duplicate-net-name', message: 'Net names must be unique.'});
    const validEndpoints = new Set();
    components.forEach(component => component.pins.forEach(pin => validEndpoints.add(`${component.reference}.${pin}`)));
    const seenEndpoints = new Map();
    netRows.forEach(net => net.endpoints.forEach(endpoint => {
      if (!validEndpoints.has(endpoint)) findings.push({severity: 'error', code: 'unknown-endpoint', net: net.name, endpoint, message: `Endpoint ${endpoint} is not defined by the component records.`});
      if (seenEndpoints.has(endpoint) && seenEndpoints.get(endpoint) !== net.name) findings.push({severity: 'error', code: 'endpoint-on-multiple-nets', endpoint, message: `${endpoint} appears on multiple nets.`});
      seenEndpoints.set(endpoint, net.name);
    }));
    components.forEach(component => component.pins.forEach(pin => {
      const endpoint = `${component.reference}.${pin}`;
      if (!seenEndpoints.has(endpoint)) findings.push({severity: /NC|DNC/i.test(pin) ? 'info' : 'warning', code: 'unconnected-pin', endpoint, message: `${endpoint} is not connected in the structured netlist.`});
    }));
    netRows.forEach(net => {
      if (net.endpoints.length < 2) findings.push({severity: 'warning', code: 'single-endpoint-net', net: net.name, message: `Net ${net.name} has only one endpoint.`});
    });
    return {
      schema: 'sc-workbench-structured-schematic/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      components,
      nets: netRows,
      findings,
      netlist: {format: 'scwb-json-netlist/1.0', components: components.map(({reference, value: componentValue, footprint}) => ({reference, value: componentValue, footprint})), nets: netRows}
    };
  }

  function initSchematic(root) {
    const output = q(root, '[data-scwb-v220-sch-output]');
    const metrics = q(root, '[data-scwb-v220-sch-metrics]');
    let model = load(root, 'schematic-model', null);
    const render = item => {
      if (!item) return;
      output.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({Components: item.components.length, Nets: item.nets.length, Errors: item.findings.filter(finding => finding.severity === 'error').length, Warnings: item.findings.filter(finding => finding.severity === 'warning').length});
    };
    render(model);
    action(root, 'sch-validate', () => {
      try {
        model = schematicModel(root);
        save(root, 'schematic-model', model);
        render(model);
        setStatus(root, model.findings.some(item => item.severity === 'error') ? 'Schematic review required' : 'Schematic validated');
      } catch (error) {
        output.textContent = `Schematic validation failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Validation failed');
      }
    });
    action(root, 'sch-netlist', () => {
      try {
        model = model || schematicModel(root);
        download(`${project(root)}-netlist.json`, JSON.stringify(model.netlist, null, 2));
        setStatus(root, 'Netlist downloaded');
      } catch (error) {
        output.textContent = `Netlist export failed: ${error.message}`;
      }
    });
    action(root, 'sch-download', () => {
      try {
        model = model || schematicModel(root);
        download(`${project(root)}-schematic-review.json`, JSON.stringify(model, null, 2));
        setStatus(root, 'Review downloaded');
      } catch (error) {
        output.textContent = `Review export failed: ${error.message}`;
      }
    });
  }

  function bomValidation(root) {
    const records = parseCSV(value(root, 'bom-csv'));
    const required = ['reference', 'manufacturer_part', 'description', 'quantity', 'unit_cost', 'status', 'substitute'];
    const missing = required.filter(header => !(header in records[0]));
    if (missing.length) throw new Error(`Missing BOM columns: ${missing.join(', ')}`);
    const budget = Number(value(root, 'bom-budget', 0));
    const currency = value(root, 'bom-currency', 'USD');
    const policy = value(root, 'bom-policy', 'strict');
    const findings = [];
    const normalized = records.map((record, index) => {
      const quantity = Number(record.quantity);
      const unitCost = Number(record.unit_cost);
      if (!Number.isFinite(quantity) || quantity <= 0) findings.push({severity: 'error', row: index + 2, code: 'invalid-quantity', message: `${record.reference || `Row ${index + 2}`} has an invalid quantity.`});
      if (!Number.isFinite(unitCost) || unitCost < 0) findings.push({severity: 'error', row: index + 2, code: 'invalid-cost', message: `${record.reference || `Row ${index + 2}`} has an invalid unit cost.`});
      if (!record.manufacturer_part) findings.push({severity: 'error', row: index + 2, code: 'missing-mpn', message: `${record.reference || `Row ${index + 2}`} has no manufacturer part number.`});
      const status = String(record.status || 'unknown').toLowerCase();
      if (policy === 'strict' && status !== 'active') findings.push({severity: 'error', row: index + 2, code: 'lifecycle-policy', message: `${record.reference} is not marked active.`});
      else if (['obsolete', 'eol'].includes(status)) findings.push({severity: 'error', row: index + 2, code: 'obsolete-part', message: `${record.reference} is marked ${status}.`});
      else if (status !== 'active') findings.push({severity: 'warning', row: index + 2, code: 'lifecycle-review', message: `${record.reference} has lifecycle status ${status}.`});
      if (!record.substitute) findings.push({severity: 'warning', row: index + 2, code: 'no-substitute', message: `${record.reference} has no documented substitute.`});
      return {...record, quantity, unit_cost: unitCost, extended_cost: Number.isFinite(quantity * unitCost) ? round(quantity * unitCost, 4) : null};
    });
    const references = normalized.flatMap(record => String(record.reference).split(/\s+/).filter(Boolean));
    if (new Set(references).size !== references.length) findings.push({severity: 'warning', code: 'reference-overlap', message: 'One or more component references appear in multiple BOM rows.'});
    const total = normalized.reduce((sum, record) => sum + (record.extended_cost || 0), 0);
    if (Number.isFinite(budget) && budget > 0 && total > budget) findings.push({severity: 'error', code: 'over-budget', message: `Estimated BOM cost ${round(total, 2)} ${currency} exceeds the budget ceiling ${round(budget, 2)} ${currency}.`});
    return {
      schema: 'sc-workbench-validated-bom/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      currency,
      budget: budget > 0 ? budget : null,
      estimatedTotal: round(total, 4),
      lifecyclePolicy: policy,
      records: normalized,
      findings,
      sourcingLimits: ['Costs are user-entered estimates and are not live quotes.', 'Lifecycle, lead time, availability, compliance, authenticity, and substitutes require supplier and manufacturer verification.']
    };
  }

  function initBom(root) {
    const output = q(root, '[data-scwb-v220-bom-output]');
    const metrics = q(root, '[data-scwb-v220-bom-metrics]');
    let record = load(root, 'bom-validation', null);
    const render = item => {
      if (!item) return;
      output.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({Lines: item.records.length, 'Estimated total': `${item.estimatedTotal} ${item.currency}`, Errors: item.findings.filter(finding => finding.severity === 'error').length, Substitutes: item.records.filter(row => row.substitute).length});
    };
    render(record);
    action(root, 'bom-validate', () => {
      try {
        record = bomValidation(root);
        save(root, 'bom-validation', record);
        render(record);
        setStatus(root, record.findings.some(item => item.severity === 'error') ? 'BOM review required' : 'BOM validated');
      } catch (error) {
        output.textContent = `BOM validation failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Validation failed');
      }
    });
    action(root, 'bom-export', () => {
      try {
        record = record || bomValidation(root);
        download(`${project(root)}-validated-bom.csv`, toCSV(record.records, ['reference', 'manufacturer_part', 'description', 'quantity', 'unit_cost', 'extended_cost', 'status', 'substitute']), 'text/csv;charset=utf-8');
        setStatus(root, 'Validated BOM exported');
      } catch (error) {
        output.textContent = `BOM export failed: ${error.message}`;
      }
    });
    action(root, 'bom-download', () => {
      try {
        record = record || bomValidation(root);
        download(`${project(root)}-sourcing-record.json`, JSON.stringify(record, null, 2));
        setStatus(root, 'Sourcing record downloaded');
      } catch (error) {
        output.textContent = `Sourcing export failed: ${error.message}`;
      }
    });
  }

  function pcbReview(root) {
    const width = Number(value(root, 'pcb-width'));
    const height = Number(value(root, 'pcb-height'));
    const layers = Number(value(root, 'pcb-layers'));
    const track = Number(value(root, 'pcb-track'));
    const via = Number(value(root, 'pcb-via'));
    const edge = Number(value(root, 'pcb-edge'));
    const environment = value(root, 'pcb-environment', 'indoor');
    if (![width, height, layers, track, via, edge].every(Number.isFinite) || width <= 0 || height <= 0 || track <= 0 || via <= 0 || edge < 0) throw new Error('Board geometry and design-rule fields must contain valid positive values.');
    const placements = parseCSV(`reference,x_mm,y_mm,rotation,side,class\n${value(root, 'pcb-placement')}`).map((record, index) => ({...record, x_mm: Number(record.x_mm), y_mm: Number(record.y_mm), rotation: Number(record.rotation), row: index + 2}));
    const findings = [];
    placements.forEach(record => {
      if (![record.x_mm, record.y_mm, record.rotation].every(Number.isFinite)) findings.push({severity: 'error', code: 'invalid-placement', reference: record.reference, message: `${record.reference} has invalid placement coordinates or rotation.`});
      if (record.x_mm < edge || record.x_mm > width - edge || record.y_mm < edge || record.y_mm > height - edge) findings.push({severity: 'error', code: 'outside-usable-outline', reference: record.reference, message: `${record.reference} is outside the preliminary usable board outline.`});
      if (!['top', 'bottom'].includes(String(record.side).toLowerCase())) findings.push({severity: 'error', code: 'invalid-side', reference: record.reference, message: `${record.reference} side must be top or bottom.`});
    });
    const refs = placements.map(item => item.reference);
    if (new Set(refs).size !== refs.length) findings.push({severity: 'error', code: 'duplicate-reference', message: 'Placement references must be unique.'});
    for (let first = 0; first < placements.length; first += 1) {
      for (let second = first + 1; second < placements.length; second += 1) {
        const a = placements[first];
        const b = placements[second];
        if (a.side === b.side && a.x_mm === b.x_mm && a.y_mm === b.y_mm) findings.push({severity: 'error', code: 'coordinate-collision', message: `${a.reference} and ${b.reference} share the same placement coordinate.`});
      }
    }
    const minimums = environment === 'outdoor' ? {track: 0.2, edge: 0.5} : environment === 'industrial' ? {track: 0.18, edge: 0.35} : {track: 0.1, edge: 0.2};
    if (track < minimums.track) findings.push({severity: 'warning', code: 'track-space-review', message: `The ${track} mm track/space assumption is below the conservative ${minimums.track} mm review threshold for this environment.`});
    if (edge < minimums.edge) findings.push({severity: 'warning', code: 'edge-clearance-review', message: `The ${edge} mm edge clearance is below the conservative ${minimums.edge} mm review threshold for this environment.`});
    if (layers < 4 && placements.some(item => /fpga|high-speed|rf/i.test(item.class))) findings.push({severity: 'warning', code: 'stackup-review', message: 'High-speed or FPGA-class placement was identified on a board with fewer than four copper layers.'});
    return {
      schema: 'sc-workbench-pcb-plan/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      outline: {widthMm: width, heightMm: height, areaMm2: round(width * height, 2)},
      stackup: {copperLayers: layers, environment},
      preliminaryRules: {minimumTrackSpaceMm: track, minimumViaDrillMm: via, edgeClearanceMm: edge},
      placements,
      findings,
      requiredProfessionalChecks: ['fabricator capability', 'footprints', 'courtyard and component geometry', 'clearance and creepage', 'return paths', 'impedance', 'thermal design', 'DFM', 'DFT', 'EMC']
    };
  }

  function initPcb(root) {
    const output = q(root, '[data-scwb-v220-pcb-output]');
    const metrics = q(root, '[data-scwb-v220-pcb-metrics]');
    let record = load(root, 'pcb-review', null);
    const render = item => {
      if (!item) return;
      output.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({Area: `${item.outline.areaMm2} mm²`, Layers: item.stackup.copperLayers, Placements: item.placements.length, Findings: item.findings.length});
    };
    render(record);
    action(root, 'pcb-drc', () => {
      try {
        record = pcbReview(root);
        save(root, 'pcb-review', record);
        render(record);
        setStatus(root, record.findings.some(item => item.severity === 'error') ? 'PCB review required' : 'Preliminary checks complete');
      } catch (error) {
        output.textContent = `PCB review failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Review failed');
      }
    });
    action(root, 'pcb-download', () => {
      try {
        record = record || pcbReview(root);
        download(`${project(root)}-pcb-plan.json`, JSON.stringify(record, null, 2));
        setStatus(root, 'Board plan downloaded');
      } catch (error) {
        output.textContent = `Board-plan export failed: ${error.message}`;
      }
    });
  }

  function validationDossier(root) {
    const tests = parseCSV(`id,measurement,minimum,maximum,unit,method\n${value(root, 'val-tests')}`);
    const results = parseCSV(`id,value,note,evidence\n${value(root, 'val-results')}`);
    const resultMap = new Map(results.map(result => [result.id, result]));
    const duplicates = results.filter((result, index) => results.findIndex(other => other.id === result.id) !== index).map(result => result.id);
    const findings = [];
    if (duplicates.length) findings.push({severity: 'error', code: 'duplicate-result-id', ids: [...new Set(duplicates)], message: 'Each test ID must have at most one measured result.'});
    const evaluations = tests.map(test => {
      const result = resultMap.get(test.id);
      const minimum = Number(test.minimum);
      const maximum = Number(test.maximum);
      if (!Number.isFinite(minimum) || !Number.isFinite(maximum) || minimum > maximum) {
        findings.push({severity: 'error', code: 'invalid-limits', id: test.id, message: `${test.id} has invalid acceptance limits.`});
        return {...test, measuredValue: null, status: 'INVALID', note: result?.note || '', evidence: result?.evidence || ''};
      }
      if (!result) {
        findings.push({severity: 'error', code: 'missing-result', id: test.id, message: `${test.id} has no measured result.`});
        return {...test, measuredValue: null, status: 'NOT RUN', note: '', evidence: ''};
      }
      const measured = Number(result.value);
      if (!Number.isFinite(measured)) {
        findings.push({severity: 'error', code: 'invalid-result', id: test.id, message: `${test.id} result is not numeric.`});
        return {...test, measuredValue: result.value, status: 'INVALID', note: result.note, evidence: result.evidence};
      }
      const status = measured >= minimum && measured <= maximum ? 'PASS' : 'FAIL';
      if (status === 'FAIL') findings.push({severity: 'error', code: 'acceptance-failure', id: test.id, message: `${test.id} measured ${measured} ${test.unit}, outside ${minimum}–${maximum} ${test.unit}.`});
      if (!result.evidence) findings.push({severity: 'warning', code: 'missing-evidence', id: test.id, message: `${test.id} has no evidence reference.`});
      return {...test, minimum, maximum, measuredValue: measured, status, note: result.note, evidence: result.evidence};
    });
    results.filter(result => !tests.some(test => test.id === result.id)).forEach(result => findings.push({severity: 'warning', code: 'orphan-result', id: result.id, message: `${result.id} has a result but no test definition.`}));
    const pass = evaluations.filter(item => item.status === 'PASS').length;
    const fail = evaluations.filter(item => item.status === 'FAIL').length;
    return {
      schema: 'sc-workbench-hardware-validation-dossier/1.0',
      workbenchVersion: cfg.version || '2.2.0',
      generatedAt: new Date().toISOString(),
      device: {id: value(root, 'val-device'), revision: value(root, 'val-revision'), stage: value(root, 'val-stage')},
      summary: {tests: evaluations.length, pass, fail, notRun: evaluations.length - pass - fail, disposition: fail === 0 && pass === evaluations.length ? 'PASS' : 'REVIEW'},
      evaluations,
      findings,
      signoff: {preparedBy: null, reviewedBy: null, approvedBy: null, date: null},
      limits: ['Browser evaluation does not calibrate instruments or authenticate evidence.', 'Acceptance limits, methods, uncertainty, fixtures, standards, and signoff require qualified review.']
    };
  }

  function initValidation(root) {
    const output = q(root, '[data-scwb-v220-val-output]');
    const metrics = q(root, '[data-scwb-v220-val-metrics]');
    let dossier = load(root, 'validation-dossier', null);
    const render = item => {
      if (!item) return;
      output.textContent = JSON.stringify(item, null, 2);
      metrics.innerHTML = metricCards({Tests: item.summary.tests, Pass: item.summary.pass, Fail: item.summary.fail, Disposition: item.summary.disposition});
    };
    render(dossier);
    action(root, 'val-evaluate', () => {
      try {
        dossier = validationDossier(root);
        save(root, 'validation-dossier', dossier);
        render(dossier);
        setStatus(root, dossier.summary.disposition === 'PASS' ? 'Validation passed' : 'Validation review required');
      } catch (error) {
        output.textContent = `Validation evaluation failed: ${error.message}`;
        metrics.innerHTML = '';
        setStatus(root, 'Evaluation failed');
      }
    });
    action(root, 'val-download', () => {
      try {
        dossier = dossier || validationDossier(root);
        download(`${safeName(dossier.device.id)}-validation-dossier.json`, JSON.stringify(dossier, null, 2));
        setStatus(root, 'Dossier downloaded');
      } catch (error) {
        output.textContent = `Dossier export failed: ${error.message}`;
      }
    });
    action(root, 'val-csv', () => {
      try {
        dossier = dossier || validationDossier(root);
        download(`${safeName(dossier.device.id)}-validation-results.csv`, toCSV(dossier.evaluations, ['id', 'measurement', 'minimum', 'maximum', 'unit', 'method', 'measuredValue', 'status', 'note', 'evidence']), 'text/csv;charset=utf-8');
        setStatus(root, 'Results exported');
      } catch (error) {
        output.textContent = `CSV export failed: ${error.message}`;
      }
    });
  }

  function initialize(root) {
    switch (root.dataset.scwbV220Panel) {
      case 'fpga': initFpga(root); break;
      case 'electronics': initElectronics(root); break;
      case 'schematic': initSchematic(root); break;
      case 'bom': initBom(root); break;
      case 'pcb': initPcb(root); break;
      case 'validation': initValidation(root); break;
    }
  }

  const start = () => document.querySelectorAll('[data-scwb-v220-panel]').forEach(initialize);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
