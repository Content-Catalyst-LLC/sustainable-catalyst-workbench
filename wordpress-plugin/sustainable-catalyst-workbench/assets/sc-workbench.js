(function(){
  const api = (path, opts={}) => fetch(SCWorkbench.restUrl + path, Object.assign({headers:{'Content-Type':'application/json','X-WP-Nonce':SCWorkbench.nonce}}, opts)).then(r=>r.json());
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  function renderValues(values){ if(!values) return ''; return '<dl class="scwb-values">' + Object.entries(values).map(([k,v])=>`<div><dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(typeof v==='object'?JSON.stringify(v):v)}</dd></div>`).join('') + '</dl>'; }
  function renderResult(data){
    if(!data) return '<p>No response.</p>';
    if(data.answer) return `<div class="scwb-answer"><p>${esc(data.answer).replace(/\n/g,'<br>')}</p>${data.recommended_tools?'<h4>Recommended tools</h4><ul>'+data.recommended_tools.slice(0,5).map(t=>`<li>${esc(t.title)} <span>${esc(t.domain)}</span></li>`).join('')+'</ul>':''}</div>`;
    if(data.ok === false) return `<div class="scwb-error">${esc(data.error || 'Tool failed.')}</div>`;
    let graphs = (data.graphs||[]).map(g=>`<figure class="scwb-graph"><figcaption>${esc(g.title||'Graph')}</figcaption>${g.svg||''}</figure>`).join('');
    let warnings = (data.warnings||[]).length ? '<div class="scwb-warnings"><strong>Warnings</strong><ul>'+data.warnings.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul></div>' : '';
    return `<div class="scwb-result"><h3>${esc(data.tool||'Workbench Result')}</h3><p>${esc(data.summary||'')}</p>${warnings}${renderValues(data.values)}${graphs}<p class="scwb-disclaimer">${esc(data.disclaimer||'Educational support only.')}</p></div>`;
  }
  function fieldHtml(f){
    const val = esc(f.default||'');
    if(f.type==='textarea') return `<label>${esc(f.label)}<textarea name="${esc(f.name)}" rows="4">${val}</textarea><small>${esc(f.help||'')}</small></label>`;
    if(f.type==='select') return `<label>${esc(f.label)}<select name="${esc(f.name)}">${(f.options||[]).map(o=>`<option value="${esc(o)}" ${o==f.default?'selected':''}>${esc(o)}</option>`).join('')}</select><small>${esc(f.help||'')}</small></label>`;
    return `<label>${esc(f.label)}<input name="${esc(f.name)}" type="${esc(f.type||'text')}" value="${val}"><small>${esc(f.help||'')}</small></label>`;
  }
  function initWorkbench(el){
    const topic = el.dataset.topic || 'research-library';
    let tools = Array.isArray(SCWorkbench.localTools) ? SCWorkbench.localTools : [];
    el.querySelectorAll('[data-scwb-tab]').forEach(btn=>btn.addEventListener('click',()=>{
      el.querySelectorAll('[data-scwb-tab]').forEach(b=>b.classList.remove('is-active')); btn.classList.add('is-active');
      el.querySelectorAll('[data-scwb-panel]').forEach(p=>p.classList.toggle('is-active', p.dataset.scwbPanel===btn.dataset.scwbTab));
    }));
    const askForm = el.querySelector('[data-scwb-ask-form]');
    askForm && askForm.addEventListener('submit', e=>{ e.preventDefault(); const out=el.querySelector('[data-scwb-ask-output]'); out.hidden=false; out.innerHTML='<p class="scwb-muted">Thinking…</p>'; const fd=new FormData(askForm); api('/ask',{method:'POST',body:JSON.stringify({question:fd.get('question'), topic, mode:fd.get('mode')||'guided'})}).then(d=>out.innerHTML=renderResult(d)).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); });
    const select = el.querySelector('[data-scwb-tool-select]');
    function populateTools(data){
      const incoming = data && Array.isArray(data.tools) ? data.tools : [];
      tools = incoming.length ? incoming : tools;
      if(select){
        select.innerHTML = tools.length ? tools.map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('') : '<option value="">No calculators available</option>';
      }
      const shell = el.querySelector('[data-scwb-tool-shell]');
      if(shell && data && data.backend_online === false){
        shell.innerHTML = `<div class="scwb-notice"><strong>Backend offline.</strong> ${esc(data.notice || SCWorkbench.backendRequiredHelp || 'Start the backend to run calculations.')}</div>`;
      }
      renderModels(el, tools);
    }
    populateTools({tools: tools, backend_online: false, notice: SCWorkbench.backendRequiredHelp});
    api('/tools').then(populateTools).catch(()=>populateTools({tools: tools, backend_online:false, notice:SCWorkbench.backendRequiredHelp}));
    const open = el.querySelector('[data-scwb-open-tool]');
    open && open.addEventListener('click',()=>{ const id=select && select.value; const spec=tools.find(t=>t.id===id); const shell=el.querySelector('[data-scwb-tool-shell]'); if(!shell) return; if(!spec){ shell.innerHTML='<div class="scwb-error">No calculator is selected. Reload the page or check that the Workbench plugin assets are active.</div>'; return; } shell.innerHTML=`<form class="scwb-tool-form"><h3>${esc(spec.title)}</h3><p>${esc(spec.description)}</p>${(spec.inputs||[]).map(fieldHtml).join('')}<button class="scwb-button" type="submit">Run Calculator</button><div class="scwb-output" data-tool-output></div></form>`; shell.querySelector('form').addEventListener('submit', ev=>{ ev.preventDefault(); const fd=new FormData(ev.currentTarget); const inputs={}; for(const [k,v] of fd.entries()) inputs[k]=v; const out=shell.querySelector('[data-tool-output]'); out.innerHTML='<p class="scwb-muted">Running backend analytics…</p>'; api('/run',{method:'POST',body:JSON.stringify({tool_id:id, inputs, mode:(el.querySelector('[data-scwb-tool-mode]')||{}).value||'guided', topic})}).then(d=>out.innerHTML=renderResult(d)).catch(err=>out.innerHTML='<div class="scwb-error">'+esc(err.message)+'</div>'); }); });
  }
  function renderModels(el, tools){ const box=el.querySelector('[data-scwb-models]'); if(!box) return; const groups={}; tools.forEach(t=>{ (groups[t.domain]||(groups[t.domain]=[])).push(t); }); box.innerHTML=Object.entries(groups).map(([domain,items])=>`<section><h3>${esc(domain)}</h3><ul>${items.map(t=>`<li><strong>${esc(t.title)}</strong><span>${esc(t.family)} · ${esc(t.engine)}</span></li>`).join('')}</ul></section>`).join(''); }
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-scwb]').forEach(initWorkbench));
})();
