(function(){
  const api = (path, opts={}) => fetch(SCWorkbench.restUrl + path, Object.assign({headers:{'Content-Type':'application/json','X-WP-Nonce':SCWorkbench.nonce}}, opts)).then(r=>r.json());
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const safeName = s => String(s||'workbench').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80) || 'workbench';
  function downloadBlob(name, blob){ const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); setTimeout(()=>{URL.revokeObjectURL(a.href); a.remove();},500); }
  function renderValues(values){ if(!values) return ''; return '<dl class="scwb-values">' + Object.entries(values).map(([k,v])=>`<div><dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(typeof v==='object'?JSON.stringify(v):v)}</dd></div>`).join('') + '</dl>'; }
  function exportRow(hasGraphs){ return `<div class="scwb-export-row"><button type="button" class="scwb-mini" data-scwb-export="pdf">PDF Report</button><button type="button" class="scwb-mini" data-scwb-export="json">Download JSON</button>${hasGraphs?'<span>Graph images: use SVG/PNG buttons below each figure.</span>':''}</div>`; }
  function renderResult(data){
    if(!data) return '<p>No response.</p>';
    if(data.answer) return `<div class="scwb-answer"><p>${esc(data.answer).replace(/\n/g,'<br>')}</p>${data.recommended_tools?'<h4>Recommended tools</h4><ul>'+data.recommended_tools.slice(0,5).map(t=>`<li>${esc(t.title)} <span>${esc(t.domain)}</span></li>`).join('')+'</ul>':''}</div>`;
    if(data.ok === false) return `<div class="scwb-error">${esc(data.error || 'Tool failed.')}</div>`;
    let graphs = (data.graphs||[]).map((g,i)=>`<figure class="scwb-graph" data-graph-index="${i}"><figcaption>${esc(g.title||'Graph')}</figcaption>${g.svg||''}<div class="scwb-graph-actions"><button type="button" class="scwb-mini" data-scwb-export="svg">Download SVG</button><button type="button" class="scwb-mini" data-scwb-export="png">Download PNG</button></div></figure>`).join('');
    let warnings = (data.warnings||[]).length ? '<div class="scwb-warnings"><strong>Warnings</strong><ul>'+data.warnings.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul></div>' : '';
    return `<div class="scwb-result"><h3>${esc(data.tool||'Workbench Result')}</h3><p>${esc(data.summary||'')}</p>${exportRow((data.graphs||[]).length>0)}${warnings}${renderValues(data.values)}${graphs}<p class="scwb-disclaimer">${esc(data.disclaimer||'Educational support only.')}</p></div>`;
  }
  function fieldHtml(f){
    const val = esc(f.default||'');
    if(f.type==='textarea') return `<label>${esc(f.label)}<textarea name="${esc(f.name)}" rows="4">${val}</textarea><small>${esc(f.help||'')}</small></label>`;
    if(f.type==='select') return `<label>${esc(f.label)}<select name="${esc(f.name)}">${(f.options||[]).map(o=>`<option value="${esc(o)}" ${o==f.default?'selected':''}>${esc(o)}</option>`).join('')}</select><small>${esc(f.help||'')}</small></label>`;
    return `<label>${esc(f.label)}<input name="${esc(f.name)}" type="${esc(f.type||'text')}" value="${val}"><small>${esc(f.help||'')}</small></label>`;
  }
  function storeAndRender(out, d){ out.hidden=false; out.__scwbLastResult=d; out.innerHTML=renderResult(d); }
  function openPdfReport(data, html){
    const w=window.open('', '_blank'); if(!w) return alert('Popup blocked. Allow popups to create the PDF-ready report.');
    const title=esc(data && data.tool ? data.tool : 'Sustainable Catalyst Workbench Report');
    w.document.write(`<!doctype html><html><head><title>${title}</title><meta charset="utf-8"><style>body{font-family:Arial,Helvetica,sans-serif;margin:34px;color:#111}.scwb-result{max-width:980px}.scwb-export-row,.scwb-graph-actions{display:none}.scwb-values{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.scwb-values div{border:1px solid #ddd;padding:8px}.scwb-graph{break-inside:avoid;border:1px solid #ddd;padding:12px;margin:16px 0}.scwb-graph svg{max-width:100%;height:auto}.scwb-warnings{border-left:4px solid #b40000;padding-left:12px}.scwb-disclaimer{font-size:12px;color:#555;border-top:1px solid #ddd;padding-top:12px}@page{margin:.6in}</style></head><body><p style="text-transform:uppercase;letter-spacing:.08em;color:#b40000;font-weight:bold">Sustainable Catalyst Workbench</p>${html}<script>window.onload=()=>setTimeout(()=>window.print(),300)<\/script></body></html>`);
    w.document.close();
  }
  function svgMarkupFromFigure(fig){ const svg=fig && fig.querySelector('svg'); return svg ? new XMLSerializer().serializeToString(svg) : ''; }
  function downloadSvg(fig){ const title=(fig.querySelector('figcaption')||{}).textContent || 'graph'; const svg=svgMarkupFromFigure(fig); if(!svg) return; downloadBlob(safeName(title)+'.svg', new Blob([svg], {type:'image/svg+xml'})); }
  function downloadPng(fig){ const title=(fig.querySelector('figcaption')||{}).textContent || 'graph'; const svg=svgMarkupFromFigure(fig); if(!svg) return; const img=new Image(); const url=URL.createObjectURL(new Blob([svg], {type:'image/svg+xml'})); img.onload=function(){ const scale=2; const canvas=document.createElement('canvas'); canvas.width=(img.width||900)*scale; canvas.height=(img.height||520)*scale; const ctx=canvas.getContext('2d'); ctx.fillStyle='#ffffff'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.drawImage(img,0,0,canvas.width,canvas.height); canvas.toBlob(blob=>downloadBlob(safeName(title)+'.png', blob), 'image/png'); URL.revokeObjectURL(url); }; img.src=url; }


  function keyboardPreview(s){
    let out=String(s||'').split('\n')[0] || '';
    const reps=[['theta','θ'],['lambda','λ'],['sigma','σ'],['omega','ω'],['alpha','α'],['beta','β'],['gamma','γ'],['delta','δ'],['phi','φ'],['pi','π'],['sqrt','√'],['<=','≤'],['>=','≥'],['!=','≠'],['->','→'],['+-','±']];
    reps.forEach(([a,b])=>{ out=out.replace(new RegExp('(^|[^A-Za-z])'+a+'([^A-Za-z]|$)','g'), (m,p,q)=>p+b+q); });
    const sup={'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','=':'⁼','(':'⁽',')':'⁾','n':'ⁿ'};
    const sub={'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','=':'₌','(':'₍',')':'₎','n':'ₙ'};
    out=out.replace(/\^\{([^{}]+)\}/g, (_,x)=>String(x).split('').map(ch=>sup[ch]||ch).join(''));
    out=out.replace(/\^([A-Za-z0-9+\-=()]+)/g, (_,x)=>String(x).split('').map(ch=>sup[ch]||ch).join(''));
    out=out.replace(/_\{([^{}]+)\}/g, (_,x)=>String(x).split('').map(ch=>sub[ch]||ch).join(''));
    out=out.replace(/_([A-Za-z0-9+\-=()]+)/g, (_,x)=>String(x).split('').map(ch=>sub[ch]||ch).join(''));
    out=out.replace(/\*/g,'·').replace(/-/g,'−');
    return out || 'Type an equation to preview it here.';
  }
  function renderCodeBlock(label, value){ if(value===undefined || value===null || value==='') return ''; return `<div class="scwb-code-row"><strong>${esc(label)}</strong><code>${esc(typeof value==='object'?JSON.stringify(value,null,2):value)}</code></div>`; }
  function renderSymbolicResult(data){
    if(!data) return '<p>No response.</p>';
    if(data.ok===false) return renderResult(data);
    const v=data.values||{};
    const unit=v.unit_analysis ? `<div class="scwb-unit-box"><h4>Unit-aware engineering notes</h4>${renderCodeBlock('Result', v.unit_analysis.quantity || '')}${renderCodeBlock('Units', v.unit_analysis.units || '')}${renderCodeBlock('Assignments', v.unit_analysis.assignments || {})}</div>` : '';
    const steps=(data.steps||[]).length ? '<ol class="scwb-steps">'+data.steps.map(step=>`<li>${esc(step)}</li>`).join('')+'</ol>' : '';
    const warnings=(data.warnings||[]).length ? '<div class="scwb-warnings"><strong>Warnings</strong><ul>'+data.warnings.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul></div>' : '';
    const graphs=(data.graphs||[]).map((g,i)=>`<figure class="scwb-graph" data-graph-index="${i}"><figcaption>${esc(g.title||'Graph')}</figcaption>${g.svg||''}<div class="scwb-graph-actions"><button type="button" class="scwb-mini" data-scwb-export="svg">Download SVG</button><button type="button" class="scwb-mini" data-scwb-export="png">Download PNG</button></div></figure>`).join('');
    return `<div class="scwb-result scwb-symbolic-result"><h3>${esc(data.tool||'Chalkboard Translator')}</h3><p>${esc(data.summary||'')}</p>${exportRow((data.graphs||[]).length>0)}<div class="scwb-symbolic-layout"><div class="scwb-chalkboard-display scwb-chalkboard-display-large">${esc(v.chalkboard_preview||'')}</div><div class="scwb-code-stack">${renderCodeBlock('LaTeX', v.latex)}${renderCodeBlock('SymPy', v.sympy_code)}${renderCodeBlock('Operation', v.operation)}${renderCodeBlock('Symbolic result', v.symbolic_result)}${renderCodeBlock('LaTeX result', v.latex_result)}${renderCodeBlock('Variables', v.variables)}</div></div>${unit}${warnings}${steps}${graphs}<p class="scwb-disclaimer">${esc(data.disclaimer||'Educational support only. Engineering outputs require qualified professional review.')}</p></div>`;
  }
  function renderList(title, items){
    if(!items || !items.length) return '';
    return `<div class="scwb-engineering-section"><h4>${esc(title)}</h4><ul>${items.map(item=>`<li>${esc(item)}</li>`).join('')}</ul></div>`;
  }
  function renderVariablesTable(vars){
    if(!vars || !vars.length) return '';
    return `<div class="scwb-engineering-section"><h4>Inputs and variables</h4><div class="scwb-engineering-table"><table><thead><tr><th>Symbol</th><th>Meaning</th><th>Assigned value</th><th>Review note</th></tr></thead><tbody>${vars.map(row=>`<tr><td><code>${esc(row.symbol)}</code></td><td>${esc(row.meaning)}</td><td>${esc(row.assigned_value)}</td><td>${esc(row.review_note)}</td></tr>`).join('')}</tbody></table></div></div>`;
  }
  function renderEngineeringResult(data){
    if(!data) return '<p>No response.</p>';
    if(data.ok===false) return renderResult(data);
    const v=data.values||{};
    const note=v.engineering_note || data.engineering_mode || {};
    const formula=v.formula_summary || {};
    const unit=v.unit_analysis || {};
    const warnings=(data.warnings||[]).length ? '<div class="scwb-warnings"><strong>Warnings</strong><ul>'+data.warnings.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul></div>' : '';
    const method=(data.method||[]).length ? '<ol class="scwb-steps">'+data.method.map(step=>`<li>${esc(step)}</li>`).join('')+'</ol>' : '';
    const interpretation=(data.interpretation||[]).length ? renderList('Interpretation and next use', data.interpretation) : '';
    const resultBox = unit && unit.quantity ? `<div class="scwb-engineering-result-box"><p class="scwb-card-label">Computed result</p><strong>${esc(unit.target||formula.target||'Result')}</strong><span>${esc(unit.quantity)}</span><small>${esc(unit.units ? 'Units: '+unit.units : '')}</small></div>` : `<div class="scwb-engineering-result-box"><p class="scwb-card-label">Computed result</p><span>No numerical unit-aware result yet. Add unit assignments such as <code>F = 1000 N</code>.</span></div>`;
    const solve = v.symbolic_solve ? `<div class="scwb-engineering-section"><h4>Symbolic solve</h4>${renderCodeBlock('Solve result', v.symbolic_solve)}</div>` : '';
    return `<div class="scwb-result scwb-engineering-result"><h3>${esc(data.tool||'Engineering Mode')}</h3><p>${esc(data.summary||'')}</p>${exportRow(false)}<div class="scwb-engineering-hero"><div><p class="scwb-card-label">Recognized domain</p><strong>${esc(v.engineering_domain||'general engineering')}</strong><span>${esc(formula.primary_formula||'')}</span></div>${resultBox}</div><div class="scwb-symbolic-layout"><div class="scwb-chalkboard-display scwb-chalkboard-display-large">${esc(v.chalkboard_preview||'')}</div><div class="scwb-code-stack">${renderCodeBlock('LaTeX', v.latex)}${renderCodeBlock('SymPy', v.sympy_code)}${renderCodeBlock('Formula summary', formula)}</div></div>${renderVariablesTable(v.variables)}${renderList('Assumptions', note.assumptions||[])}${renderList('Validation checks', note.validation_checks||[])}${renderList('Sensitivity template', note.sensitivity_template||[])}${solve}${warnings}<div class="scwb-engineering-section"><h4>Method</h4>${method}</div>${interpretation}<p class="scwb-disclaimer">${esc(data.disclaimer||'Educational support only. Engineering outputs require qualified professional review.')}</p></div>`;
  }

  function renderEngineeringCalculatorResult(data){
    if(!data) return '<p>No response.</p>';
    if(data.ok===false) return renderResult(data);
    const v=data.values||{};
    const note=v.engineering_note||{};
    const results=v.results||{};
    const inputs=v.inputs||{};
    const warnings=(data.warnings||[]).length ? '<div class="scwb-warnings"><strong>Warnings</strong><ul>'+data.warnings.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul></div>' : '';
    const method=(data.method||[]).length ? '<ol class="scwb-steps">'+data.method.map(step=>`<li>${esc(step)}</li>`).join('')+'</ol>' : '';
    const graphs=(data.graphs||[]).map((g,i)=>`<figure class="scwb-graph" data-graph-index="${i}"><figcaption>${esc(g.title||'Graph')}</figcaption>${g.svg||''}<div class="scwb-graph-actions"><button type="button" class="scwb-mini" data-scwb-export="svg">Download SVG</button><button type="button" class="scwb-mini" data-scwb-export="png">Download PNG</button></div></figure>`).join('');
    const resultCards=Object.entries(results).map(([k,val])=>`<article><span>${esc(k.replaceAll('_',' '))}</span><strong>${esc(val)}</strong></article>`).join('');
    return `<div class="scwb-result scwb-engineering-calculator-result"><h3>${esc(data.tool||'Engineering Calculator')}</h3><p>${esc(data.summary||'')}</p>${exportRow((data.graphs||[]).length>0)}<div class="scwb-engineering-calc-hero"><div><p class="scwb-card-label">Formula</p><strong>${esc(v.formula||note.formula||'')}</strong><span>${esc(note.calculation_title||'Core engineering calculator')}</span></div><div><p class="scwb-card-label">Primary result</p>${resultCards || '<span>No result fields returned.</span>'}</div></div><div class="scwb-engineering-section"><h4>Inputs</h4>${renderCodeBlock('Inputs', inputs)}</div><div class="scwb-engineering-section"><h4>Calculation note</h4>${renderCodeBlock('Formula', note.formula||v.formula)}${renderCodeBlock('Results', note.results||results)}</div>${renderList('Assumptions', note.assumptions||[])}${renderList('Validation checks', note.validation_checks||[])}${warnings}${graphs}<div class="scwb-engineering-section"><h4>Method</h4>${method}</div><p class="scwb-disclaimer">${esc(data.disclaimer||'Educational support only. Engineering outputs require qualified professional review.')}</p></div>`;
  }

  function calcFieldHtml(f){
    const val=esc(f.default||'');
    const unit=f.unit ? `<span class="scwb-unit-chip">${esc(f.unit)}</span>` : '';
    if(f.type==='select') return `<label>${esc(f.label)} ${unit}<select name="${esc(f.name)}">${(f.options||[]).map(o=>`<option value="${esc(o)}" ${o==f.default?'selected':''}>${esc(o.replaceAll('_',' '))}</option>`).join('')}</select><small>${esc(f.help||'')}</small></label>`;
    return `<label>${esc(f.label)} ${unit}<input name="${esc(f.name)}" type="${esc(f.type||'number')}" value="${val}" step="any"><small>${esc(f.help||'')}</small></label>`;
  }

  function initEngineeringCalculatorForms(root=document){
    root.querySelectorAll('[data-scwb-engineering-calculators]').forEach(wrap=>{
      if(wrap.__scwbEngineeringCalculatorsReady) return;
      wrap.__scwbEngineeringCalculatorsReady=true;
      const select=wrap.querySelector('[data-scwb-engineering-calculator-select]');
      const desc=wrap.querySelector('[data-scwb-engineering-calculator-description]');
      const fields=wrap.querySelector('[data-scwb-engineering-calculator-fields]');
      const form=wrap.querySelector('[data-scwb-engineering-calculator-form]');
      const out=wrap.querySelector('[data-scwb-engineering-calculator-output]');
      let specs=[];
      function showSpec(){
        const spec=specs.find(s=>s.id===select.value) || specs[0];
        if(!spec) return;
        select.value=spec.id;
        if(desc) desc.innerHTML=`<strong>${esc(spec.title)}</strong><br>${esc(spec.domain||'Engineering')} · ${esc(spec.family||'Core calculator')}<br>${esc(spec.description||'')}`;
        if(fields) fields.innerHTML=(spec.inputs||[]).map(calcFieldHtml).join('');
      }
      api('/engineering-calculators').then(d=>{
        specs=(d && d.calculators) || [];
        if(!specs.length){ if(desc) desc.innerHTML='<div class="scwb-error">Engineering calculator catalog is unavailable. Confirm the backend is deployed.</div>'; return; }
        if(select){ select.innerHTML=specs.map(s=>`<option value="${esc(s.id)}">${esc(s.title)}</option>`).join(''); }
        showSpec();
      }).catch(err=>{ if(desc) desc.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'; });
      select && select.addEventListener('change', showSpec);
      form && form.addEventListener('submit', ev=>{
        ev.preventDefault();
        const fd=new FormData(form);
        const inputs={};
        for(const [k,v] of fd.entries()) inputs[k]=v;
        const payload={calculator_id:select ? select.value : '', inputs};
        if(out){ out.hidden=false; out.innerHTML='<p class="scwb-muted">Running engineering calculator…</p>'; }
        api('/engineering-calculate',{method:'POST',body:JSON.stringify(payload)}).then(d=>{ if(out){ out.__scwbLastResult=d; out.innerHTML=renderEngineeringCalculatorResult(d); } }).catch(err=>{ if(out){ out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'; } });
      });
    });
  }

  function initEngineeringForms(root=document){
    root.querySelectorAll('[data-scwb-engineering-form]').forEach(form=>{
      if(form.__scwbEngineeringReady) return;
      form.__scwbEngineeringReady=true;
      const wrap=form.closest('[data-scwb-engineering-mode]') || form.closest('.scwb') || root;
      const out=wrap.querySelector('[data-scwb-engineering-output]');
      form.addEventListener('submit', ev=>{
        ev.preventDefault();
        const fd=new FormData(form);
        const payload={input:fd.get('input')||'', variable:fd.get('variable')||'', include_solve:!!fd.get('include_solve')};
        if(out){ out.hidden=false; out.innerHTML='<p class="scwb-muted">Generating engineering calculation note…</p>'; }
        api('/engineering',{method:'POST',body:JSON.stringify(payload)}).then(d=>{ if(out){ out.__scwbLastResult=d; out.innerHTML=renderEngineeringResult(d); } }).catch(err=>{ if(out){ out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'; } });
      });
    });
  }

  function initSymbolicForms(root=document){
    root.querySelectorAll('[data-scwb-symbolic-form]').forEach(form=>{
      if(form.__scwbSymbolicReady) return;
      form.__scwbSymbolicReady=true;
      const wrap=form.closest('[data-scwb-chalkboard]') || form.closest('.scwb') || root;
      const input=form.querySelector('[data-scwb-symbolic-input]') || form.querySelector('textarea[name="input"]');
      const preview=wrap.querySelector('[data-scwb-chalkboard-preview]');
      const out=wrap.querySelector('[data-scwb-symbolic-output]');
      const update=()=>{ if(preview && input) preview.textContent=keyboardPreview(input.value); };
      input && input.addEventListener('input', update);
      update();
      form.addEventListener('submit', ev=>{
        ev.preventDefault();
        const fd=new FormData(form);
        const payload={input:fd.get('input')||'', action:fd.get('action')||'translate', variable:fd.get('variable')||'x', x_min:fd.get('x_min')||-10, x_max:fd.get('x_max')||10};
        if(out){ out.hidden=false; out.innerHTML='<p class="scwb-muted">Running symbolic math and unit checks…</p>'; }
        api('/symbolic',{method:'POST',body:JSON.stringify(payload)}).then(d=>{ if(out){ out.__scwbLastResult=d; out.innerHTML=renderSymbolicResult(d); } }).catch(err=>{ if(out){ out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'; } });
      });
    });
  }

  function graphPayloadFromForm(form, parameters){
    const fd=new FormData(form);
    return {
      input: fd.get('input') || '',
      variable: fd.get('variable') || 'x',
      x_min: fd.get('x_min') || -10,
      x_max: fd.get('x_max') || 10,
      points: fd.get('points') || 700,
      show_derivative: !!fd.get('show_derivative'),
      parameters: parameters || form.__scwbGraphParameters || {}
    };
  }

  function renderGraphSliders(wrap, form, controls){
    const panel=wrap.querySelector('[data-scwb-graph-sliders]');
    if(!panel) return;
    const params=(controls && controls.parameters) || [];
    if(!params.length){ panel.hidden=false; panel.innerHTML='<p class="scwb-muted">No adjustable parameters detected. Add symbols such as <code>a</code>, <code>b</code>, <code>k</code>, or <code>omega</code> to generate sliders.</p>'; return; }
    panel.hidden=false;
    panel.innerHTML='<p class="scwb-card-label">Parameter sliders</p><div class="scwb-slider-grid">'+params.map(p=>`<label class="scwb-slider-label"><span><strong>${esc(p.label||p.name)}</strong> <output data-scwb-param-output="${esc(p.name)}">${esc(p.value)}</output></span><input type="range" data-scwb-param="${esc(p.name)}" min="${esc(p.min)}" max="${esc(p.max)}" step="${esc(p.step||0.05)}" value="${esc(p.value)}"></label>`).join('')+'</div><p class="scwb-muted">Move a slider to regenerate the graph with the new parameter value.</p>';
    form.__scwbGraphParameters={};
    params.forEach(p=>{ form.__scwbGraphParameters[p.name]=Number(p.value); });
    let timer=null;
    panel.querySelectorAll('[data-scwb-param]').forEach(input=>{
      input.addEventListener('input', ()=>{
        const name=input.dataset.scwbParam;
        const val=Number(input.value);
        form.__scwbGraphParameters[name]=val;
        const output=panel.querySelector(`[data-scwb-param-output="${CSS.escape(name)}"]`);
        if(output) output.textContent=String(Number.isInteger(val)?val:Math.round(val*1000)/1000);
        clearTimeout(timer);
        timer=setTimeout(()=>runGraphStudio(form, true), 260);
      });
    });
  }

  function runGraphStudio(form, fromSlider=false){
    const wrap=form.closest('[data-scwb-graph-studio]') || form.closest('.scwb') || document;
    const out=wrap.querySelector('[data-scwb-graph-output]');
    const payload=graphPayloadFromForm(form, form.__scwbGraphParameters || {});
    if(out){ out.hidden=false; out.innerHTML='<p class="scwb-muted">'+(fromSlider?'Updating graph…':'Generating parameter-aware graph…')+'</p>'; }
    return api('/graph',{method:'POST',body:JSON.stringify(payload)}).then(d=>{
      if(out){ out.__scwbLastResult=d; out.innerHTML=renderResult(d); }
      if(d && d.graph_controls) renderGraphSliders(wrap, form, d.graph_controls);
      return d;
    }).catch(err=>{ if(out){ out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'; } });
  }

  function initGraphStudioForms(root=document){
    root.querySelectorAll('[data-scwb-graph-form]').forEach(form=>{
      if(form.__scwbGraphReady) return;
      form.__scwbGraphReady=true;
      form.addEventListener('submit', ev=>{ ev.preventDefault(); runGraphStudio(form, false); });
    });
  }

  function handleWorkbenchExportClick(ev){
    const action=ev.target && ev.target.dataset && ev.target.dataset.scwbExport;
    if(!action) return false;
    ev.preventDefault();
    ev.stopPropagation();
    const out=ev.target.closest('.scwb-output') || document.querySelector('.scwb-output');
    const data=out && out.__scwbLastResult ? out.__scwbLastResult : null;
    if(action==='json' && data){ downloadBlob(safeName(data.tool||'workbench-result')+'.json', new Blob([JSON.stringify(data,null,2)], {type:'application/json'})); return true; }
    if(action==='pdf'){ const res=ev.target.closest('.scwb-result'); openPdfReport(data||{}, res ? res.outerHTML : ''); return true; }
    if(action==='svg'){ downloadSvg(ev.target.closest('.scwb-graph')); return true; }
    if(action==='png'){ downloadPng(ev.target.closest('.scwb-graph')); return true; }
    return false;
  }

  function shouldUseLibraryEquationMode(el){
    const topic = (el.dataset.topic || '').toLowerCase();
    const slug = (el.dataset.articleSlug || '').toLowerCase();
    const mode = (el.dataset.mode || '').toLowerCase();
    const display = (el.dataset.equationDisplay || '').toLowerCase();
    if(display === 'hidden' || display === 'off') return true;
    if(mode === 'library') return true;
    return (topic === 'research-library' || slug === 'research-library') && mode !== 'article' && mode !== 'auto-full';
  }

  function renderEquationsBox(el, force=false){
    const box=el.querySelector('[data-scwb-equations]'); if(!box) return;
    const postId=el.dataset.postId || '';
    const slug=el.dataset.articleSlug || '';
    const libraryMode=shouldUseLibraryEquationMode(el);
    if(libraryMode && !force){
      box.innerHTML=`<div class="scwb-equation-summary"><p><strong>Equation-aware tools are available.</strong> The Research Library keeps the equation registry compact so the page does not expand into dozens of analyzer cards.</p><p class="scwb-muted">Use article pages for article-specific equation analysis, or preview a limited registry list here.</p><button type="button" class="scwb-button scwb-button-secondary" data-scwb-load-equations>Preview equations</button></div>`;
      return;
    }
    const params=new URLSearchParams();
    if(postId && postId !== '0') params.set('post_id', postId);
    if(!params.has('post_id') && slug) params.set('slug', slug);
    params.set('limit', libraryMode ? '8' : '12');
    if(!postId && !slug){ box.innerHTML='<p class="scwb-muted">No current article detected. Use <code>[sc_workbench mode="auto"]</code> on an article, or scan equations in the admin registry.</p>'; return; }
    box.innerHTML='<p class="scwb-muted">Loading indexed equations…</p>';
    api('/equations/current?'+params.toString()).then(d=>{
      const equations=(d && d.equations) || [];
      if(!equations.length){ box.innerHTML='<p class="scwb-muted">No LaTeX equations are indexed for this article yet. In WordPress admin, open SC Workbench → Equation Registry and run Scan / Rebuild.</p>'; return; }
      const heading = libraryMode ? `<p class="scwb-muted">Showing a compact preview of ${Math.min(equations.length, 8)} indexed equations. Full registry exports are available in WordPress admin.</p>` : `<p class="scwb-muted">${equations.length} indexed equation${equations.length===1?'':'s'} found for this article. Select one equation to analyze.</p>`;
      box.innerHTML=heading+'<div class="scwb-equation-list scwb-equation-list-compact">'+equations.map((eq,i)=>{
        const tools=(eq.suggested_tools||[]).slice(0,4).join(', ');
        return `<article class="scwb-equation-card scwb-equation-card-compact" data-eq-index="${i}"><p class="scwb-card-label">${esc(eq.suggested_domain||'Equation')}</p><pre>${esc(eq.equation_normalized||eq.equation_raw)}</pre><small>${esc(tools)}</small><button type="button" class="scwb-mini" data-scwb-analyze-equation="${i}">Analyze selected equation</button><div class="scwb-output" data-scwb-equation-output hidden></div></article>`;
      }).join('')+'</div>';
      box.__scwbEquations=equations;
    }).catch(err=>{ box.innerHTML='<div class="scwb-error">Equation registry unavailable: '+esc(err.message)+'</div>'; });
  }

  function initWorkbench(el){
    initSymbolicForms(el);
    initGraphStudioForms(el);
    initEngineeringForms(el);
    initEngineeringCalculatorForms(el);
    const topic = el.dataset.topic || 'research-library';
    const displayMode = (el.dataset.display || 'compact').toLowerCase();
    if(displayMode === 'drawer'){
      el.classList.add('scwb-drawer-collapsed');
      const toggle=document.createElement('button');
      toggle.type='button';
      toggle.className='scwb-drawer-toggle';
      toggle.textContent='Open calculator';
      const head=el.querySelector('.scwb-head');
      if(head){ head.insertAdjacentElement('afterend', toggle); }
      toggle.addEventListener('click',()=>{ const collapsed=el.classList.toggle('scwb-drawer-collapsed'); toggle.textContent=collapsed?'Open calculator':'Close calculator'; });
    }
    const defaultTool = el.dataset.defaultTool || '';
    const startTab = el.dataset.startTab || (defaultTool ? 'calculate' : '');
    let tools = Array.isArray(SCWorkbench.localTools) ? SCWorkbench.localTools : [];
    renderEquationsBox(el);
    el.addEventListener('click', ev=>{
      if(ev.target && ev.target.dataset && ev.target.dataset.scwbLoadEquations !== undefined){
        renderEquationsBox(el, true);
        return;
      }
      const idx=ev.target && ev.target.dataset && ev.target.dataset.scwbAnalyzeEquation;
      if(idx !== undefined){
        const card=ev.target.closest('.scwb-equation-card');
        const box=el.querySelector('[data-scwb-equations]');
        const eq=box && box.__scwbEquations ? box.__scwbEquations[Number(idx)] : null;
        if(box){ box.querySelectorAll('[data-scwb-equation-output]').forEach(o=>{ if(!card || !card.contains(o)){ o.hidden=true; o.innerHTML=''; } }); }
        const out=card && card.querySelector('[data-scwb-equation-output]');
        if(out && eq){
          out.hidden=false;
          out.innerHTML='<p class="scwb-muted">Analyzing selected equation…</p>';
          api('/equations/analyze',{method:'POST',body:JSON.stringify({equation:eq.equation_normalized||eq.equation_raw, context:(eq.context_before||'')+' '+(eq.context_after||''), article_title:eq.post_title||'', suggested_tools:eq.suggested_tools||[], mode:'analyst'})}).then(d=>{ out.__scwbLastResult=d; out.innerHTML=renderResult(d); }).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>');
        }
        return;
      }
      if(handleWorkbenchExportClick(ev)) return;
    });
    el.querySelectorAll('[data-scwb-tab]').forEach(btn=>btn.addEventListener('click',()=>{
      el.querySelectorAll('[data-scwb-tab]').forEach(b=>b.classList.remove('is-active')); btn.classList.add('is-active');
      el.querySelectorAll('[data-scwb-panel]').forEach(p=>p.classList.toggle('is-active', p.dataset.scwbPanel===btn.dataset.scwbTab));
    }));
    const askForm = el.querySelector('[data-scwb-ask-form]');
    askForm && askForm.addEventListener('submit', e=>{ e.preventDefault(); const out=el.querySelector('[data-scwb-ask-output]'); out.hidden=false; out.innerHTML='<p class="scwb-muted">Thinking…</p>'; const fd=new FormData(askForm); api('/ask',{method:'POST',body:JSON.stringify({question:fd.get('question'), topic, mode:fd.get('mode')||'guided'})}).then(d=>storeAndRender(out,d)).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); });
    const select = el.querySelector('[data-scwb-tool-select]');
    function toolShellHasOpenForm(shell){ return !!(shell && shell.querySelector('.scwb-tool-form')); }
    function populateTools(data){
      const incoming = data && Array.isArray(data.tools) ? data.tools : [];
      tools = incoming.length ? incoming : tools;
      if(select){ select.innerHTML = tools.length ? tools.map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('') : '<option value="">No calculators available</option>'; }
      const shell = el.querySelector('[data-scwb-tool-shell]');
      if(shell && data && data.backend_online === false){
        if(!toolShellHasOpenForm(shell)){
          shell.innerHTML = `<div class="scwb-notice"><strong>Backend offline.</strong> ${esc(data.notice || SCWorkbench.backendRequiredHelp || 'Start the backend to run calculations.')}</div>`;
        }
      } else if(shell && data && data.backend_online === true){
        if(!toolShellHasOpenForm(shell)){
          shell.innerHTML = '<p class="scwb-muted">Backend connected. Choose a calculator and click Open Calculator.</p>';
        }
      } else if(shell && !shell.innerHTML.trim()){
        shell.innerHTML = '<p class="scwb-muted">Choose a calculator and click Open Calculator.</p>';
      }
      renderModels(el, tools);
      if(defaultTool && !el.__scwbDefaultToolOpened){
        const hasDefault = tools.some(t=>t.id===defaultTool);
        if(hasDefault && select){
          select.value = defaultTool;
          const tabName = startTab || 'calculate';
          el.querySelectorAll('[data-scwb-tab]').forEach(b=>b.classList.toggle('is-active', b.dataset.scwbTab===tabName));
          el.querySelectorAll('[data-scwb-panel]').forEach(p=>p.classList.toggle('is-active', p.dataset.scwbPanel===tabName));
          el.__scwbDefaultToolOpened = true;
          setTimeout(()=>{ const openBtn=el.querySelector('[data-scwb-open-tool]'); if(openBtn) openBtn.click(); }, 80);
        }
      }

    }
    populateTools({tools: tools, backend_online: null});
    api('/tools').then(populateTools).catch(()=>populateTools({tools: tools, backend_online:false, notice:SCWorkbench.backendRequiredHelp}));
    const open = el.querySelector('[data-scwb-open-tool]');
    open && open.addEventListener('click',()=>{ const id=select && select.value; const spec=tools.find(t=>t.id===id); const shell=el.querySelector('[data-scwb-tool-shell]'); if(!shell) return; if(!spec){ shell.innerHTML='<div class="scwb-error">No calculator is selected. Reload the page or check that the Workbench plugin assets are active.</div>'; return; } shell.innerHTML=`<form class="scwb-tool-form"><h3>${esc(spec.title)}</h3><p>${esc(spec.description)}</p>${(spec.inputs||[]).map(fieldHtml).join('')}<button class="scwb-button" type="submit">Run Calculator</button><div class="scwb-output" data-tool-output></div></form>`; shell.querySelector('form').addEventListener('submit', ev=>{ ev.preventDefault(); const fd=new FormData(ev.currentTarget); const inputs={}; for(const [k,v] of fd.entries()) inputs[k]=v; const out=shell.querySelector('[data-tool-output]'); out.innerHTML='<p class="scwb-muted">Running backend analytics…</p>'; api('/run',{method:'POST',body:JSON.stringify({tool_id:id, inputs, mode:(el.querySelector('[data-scwb-tool-mode]')||{}).value||'guided', topic})}).then(d=>storeAndRender(out,d)).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); }); });
  }
  function renderModels(el, tools){ const box=el.querySelector('[data-scwb-models]'); if(!box) return; const groups={}; tools.forEach(t=>{ (groups[t.domain]||(groups[t.domain]=[])).push(t); }); box.innerHTML=Object.entries(groups).map(([domain,items])=>`<section><h3>${esc(domain)}</h3><ul>${items.map(t=>`<li><strong>${esc(t.title)}</strong><span>${esc(t.family)} · ${esc(t.engine)}</span></li>`).join('')}</ul></section>`).join(''); }
  document.addEventListener('click', ev=>{ if(!ev.defaultPrevented && ev.target && ev.target.dataset && ev.target.dataset.scwbExport){ handleWorkbenchExportClick(ev); } });
  document.addEventListener('DOMContentLoaded',()=>{ document.querySelectorAll('[data-scwb]').forEach(initWorkbench); initSymbolicForms(document); initGraphStudioForms(document); initEngineeringForms(document); initEngineeringCalculatorForms(document); });
})();
