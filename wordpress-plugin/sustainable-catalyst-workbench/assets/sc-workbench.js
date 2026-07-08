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

  function renderEquationsBox(el){
    const box=el.querySelector('[data-scwb-equations]'); if(!box) return;
    const postId=el.dataset.postId || '';
    const slug=el.dataset.articleSlug || '';
    const params=new URLSearchParams();
    if(postId && postId !== '0') params.set('post_id', postId);
    if(!params.has('post_id') && slug) params.set('slug', slug);
    params.set('limit','25');
    if(!postId && !slug){ box.innerHTML='<p class="scwb-muted">No current article detected. Use <code>[sc_workbench mode="auto"]</code> on an article, or scan equations in the admin registry.</p>'; return; }
    api('/equations/current?'+params.toString()).then(d=>{
      const equations=(d && d.equations) || [];
      if(!equations.length){ box.innerHTML='<p class="scwb-muted">No LaTeX equations are indexed for this article yet. In WordPress admin, open SC Workbench → Equation Registry and run Scan / Rebuild.</p>'; return; }
      box.innerHTML='<div class="scwb-equation-list">'+equations.map((eq,i)=>{
        const tools=(eq.suggested_tools||[]).slice(0,4).join(', ');
        return `<article class="scwb-equation-card" data-eq-index="${i}"><p class="scwb-card-label">${esc(eq.suggested_domain||'Equation')}</p><pre>${esc(eq.equation_normalized||eq.equation_raw)}</pre><p>${esc(eq.context_before||'').slice(-220)} ${esc(eq.context_after||'').slice(0,220)}</p><small>${esc(tools)}</small><button type="button" class="scwb-mini" data-scwb-analyze-equation="${i}">Analyze equation</button><div class="scwb-output" data-scwb-equation-output hidden></div></article>`;
      }).join('')+'</div>';
      box.__scwbEquations=equations;
    }).catch(err=>{ box.innerHTML='<div class="scwb-error">Equation registry unavailable: '+esc(err.message)+'</div>'; });
  }

  function initWorkbench(el){
    const topic = el.dataset.topic || 'research-library';
    let tools = Array.isArray(SCWorkbench.localTools) ? SCWorkbench.localTools : [];
    renderEquationsBox(el);
    el.addEventListener('click', ev=>{ const idx=ev.target && ev.target.dataset && ev.target.dataset.scwbAnalyzeEquation; if(idx !== undefined){ const card=ev.target.closest('.scwb-equation-card'); const out=card && card.querySelector('[data-scwb-equation-output]'); const box=el.querySelector('[data-scwb-equations]'); const eq=box && box.__scwbEquations ? box.__scwbEquations[Number(idx)] : null; if(out && eq){ out.hidden=false; out.innerHTML='<p class="scwb-muted">Analyzing equation…</p>'; api('/equations/analyze',{method:'POST',body:JSON.stringify({equation:eq.equation_normalized||eq.equation_raw, context:(eq.context_before||'')+' '+(eq.context_after||''), article_title:eq.post_title||'', suggested_tools:eq.suggested_tools||[], mode:'analyst'})}).then(d=>{ out.__scwbLastResult=d; out.innerHTML=renderResult(d); }).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); } return; } const action=ev.target && ev.target.dataset && ev.target.dataset.scwbExport; if(!action) return; const out=ev.target.closest('.scwb-output') || el.querySelector('.scwb-output'); const data=out && out.__scwbLastResult ? out.__scwbLastResult : null; if(action==='json' && data){ downloadBlob(safeName(data.tool||'workbench-result')+'.json', new Blob([JSON.stringify(data,null,2)], {type:'application/json'})); } if(action==='pdf'){ const res=ev.target.closest('.scwb-result'); openPdfReport(data||{}, res ? res.outerHTML : ''); } if(action==='svg'){ downloadSvg(ev.target.closest('.scwb-graph')); } if(action==='png'){ downloadPng(ev.target.closest('.scwb-graph')); } });
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
    }
    populateTools({tools: tools, backend_online: null});
    api('/tools').then(populateTools).catch(()=>populateTools({tools: tools, backend_online:false, notice:SCWorkbench.backendRequiredHelp}));
    const open = el.querySelector('[data-scwb-open-tool]');
    open && open.addEventListener('click',()=>{ const id=select && select.value; const spec=tools.find(t=>t.id===id); const shell=el.querySelector('[data-scwb-tool-shell]'); if(!shell) return; if(!spec){ shell.innerHTML='<div class="scwb-error">No calculator is selected. Reload the page or check that the Workbench plugin assets are active.</div>'; return; } shell.innerHTML=`<form class="scwb-tool-form"><h3>${esc(spec.title)}</h3><p>${esc(spec.description)}</p>${(spec.inputs||[]).map(fieldHtml).join('')}<button class="scwb-button" type="submit">Run Calculator</button><div class="scwb-output" data-tool-output></div></form>`; shell.querySelector('form').addEventListener('submit', ev=>{ ev.preventDefault(); const fd=new FormData(ev.currentTarget); const inputs={}; for(const [k,v] of fd.entries()) inputs[k]=v; const out=shell.querySelector('[data-tool-output]'); out.innerHTML='<p class="scwb-muted">Running backend analytics…</p>'; api('/run',{method:'POST',body:JSON.stringify({tool_id:id, inputs, mode:(el.querySelector('[data-scwb-tool-mode]')||{}).value||'guided', topic})}).then(d=>storeAndRender(out,d)).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); }); });
  }
  function renderModels(el, tools){ const box=el.querySelector('[data-scwb-models]'); if(!box) return; const groups={}; tools.forEach(t=>{ (groups[t.domain]||(groups[t.domain]=[])).push(t); }); box.innerHTML=Object.entries(groups).map(([domain,items])=>`<section><h3>${esc(domain)}</h3><ul>${items.map(t=>`<li><strong>${esc(t.title)}</strong><span>${esc(t.family)} · ${esc(t.engine)}</span></li>`).join('')}</ul></section>`).join(''); }
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-scwb]').forEach(initWorkbench));
})();
