(function(){
  function esc(s){return String(s == null ? '' : s).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c];});}
  async function api(path, opts){
    const res = await fetch(SCWorkbench.restUrl + path, Object.assign({headers:{'Content-Type':'application/json','X-WP-Nonce':SCWorkbench.nonce}}, opts || {}));
    return await res.json();
  }
  function fallbackTools(){return Array.isArray(SCWorkbench.fallbackTools) ? SCWorkbench.fallbackTools : [];}
  function setToolOptions(root, tools, label){
    const select = root.querySelector('[data-scwb-tool-select]');
    if(!select) return;
    if(!Array.isArray(tools) || !tools.length){
      select.innerHTML = '<option value="">No calculators found</option>';
      return;
    }
    root.__scwbTools = tools;
    select.innerHTML = tools.map(t => '<option value="'+esc(t.id)+'">'+esc(t.title)+' — '+esc(t.domain || 'Workbench')+'</option>').join('');
    const note = root.querySelector('[data-scwb-tool-note]');
    if(note && label){note.textContent = label;}
  }
  function valuesTable(values){
    if(!values || typeof values !== 'object') return '';
    return '<table class="scwb-values"><tbody>' + Object.keys(values).map(k => '<tr><th>'+esc(k.replace(/_/g,' '))+'</th><td><code>'+esc(JSON.stringify(values[k]))+'</code></td></tr>').join('') + '</tbody></table>';
  }
  function renderResult(data){
    if(!data || !data.ok){return '<div class="scwb-error">'+esc((data && (data.error || data.answer)) || 'Workbench request failed.')+'</div>';}
    let warnings = (data.warnings || []).map(w=>'<li>'+esc(w)+'</li>').join('');
    let method = (data.method || []).map(m=>'<li>'+esc(m)+'</li>').join('');
    let graphs = (data.graphs || []).map(g=>'<figure class="scwb-graph"><figcaption>'+esc(g.title || 'Graph')+'</figcaption>'+String(g.svg || '')+'</figure>').join('');
    return '<article class="scwb-result-card"><h3>'+esc(data.title || 'Workbench Result')+'</h3><p>'+esc(data.summary || '')+'</p>'+valuesTable(data.values)+(warnings?'<div class="scwb-warning"><strong>Warnings</strong><ul>'+warnings+'</ul></div>':'')+(method?'<details class="scwb-details"><summary>Method</summary><ol>'+method+'</ol></details>':'')+graphs+'<p class="scwb-engine">Engine: '+esc(data.engine || 'backend')+'</p></article>';
  }
  function renderAnswer(data){
    let tools=(data.recommended_tools||[]).map(t=>'<button type="button" data-scwb-tool-id="'+esc(t.id)+'">'+esc(t.title)+'</button>').join('');
    let paths=(data.pathways||[]).map(p=>'<a href="'+esc(p.url||'#')+'"><strong>'+esc(p.title)+'</strong><span>'+esc(p.description||'')+'</span></a>').join('');
    return '<article class="scwb-answer"><h3>Workbench Answer</h3><p>'+esc(data.answer||'')+'</p>'+(tools?'<div class="scwb-recommended"><strong>Open a related tool</strong><div>'+tools+'</div></div>':'')+(paths?'<div class="scwb-pathway-links"><strong>Learning pathways</strong>'+paths+'</div>':'')+'<p class="scwb-engine">AI: '+esc(((data.ai||{}).provider)||'fallback')+(data.scoped===false?' · outside scope':'')+'</p></article>';
  }
  function fieldHtml(f){
    const name=esc(f.name), label=esc(f.label || f.name), ph=esc(f.placeholder || '');
    if(f.type === 'textarea') return '<label class="scwb-label">'+label+'<textarea name="'+name+'" rows="5" placeholder="'+ph+'"></textarea></label>';
    if(f.type === 'select') return '<label class="scwb-label">'+label+'<select name="'+name+'">'+(f.options||[]).map(o=>'<option value="'+esc(o)+'">'+esc(o)+'</option>').join('')+'</select></label>';
    return '<label class="scwb-label">'+label+'<input name="'+name+'" type="'+esc(f.type||'text')+'" placeholder="'+ph+'"></label>';
  }
  async function loadTools(root){
    const bundled = fallbackTools();
    if(bundled.length){
      setToolOptions(root, bundled, 'Bundled calculator schemas loaded. Backend is required to run advanced Python/R/Julia/Haskell analytics.');
      openTool(root, bundled[0].id);
    }
    try{
      const data = await api('/tools?limit=100');
      const tools = data.tools || [];
      if(tools.length){
        setToolOptions(root, tools, data.fallback ? 'Bundled calculator schemas loaded. Start the backend to run analyses.' : 'Backend calculator registry connected.');
        openTool(root, tools[0].id);
      }
    }catch(err){
      const note = root.querySelector('[data-scwb-tool-note]');
      if(note){note.textContent = 'Bundled calculator schemas loaded. Backend connection failed.';}
    }
  }
  async function openTool(root, id){
    const shell = root.querySelector('[data-scwb-tool-shell]');
    if(!shell) return;
    const tools = root.__scwbTools || fallbackTools();
    const tool = (tools || []).find(t => t.id === id);
    if(!tool){shell.innerHTML='<div class="scwb-error">Tool not found.</div>'; return;}
    const fields = (((tool.schema || {}).fields) || []).map(fieldHtml).join('');
    shell.innerHTML = '<form class="scwb-tool-form" data-scwb-tool-form data-tool-id="'+esc(tool.id)+'"><h3>'+esc(tool.title)+'</h3><p>'+esc(tool.description||'')+'</p>'+fields+'<button class="scwb-button" type="submit">Run Analysis</button></form><div class="scwb-output" data-scwb-tool-output hidden></div>';
  }
  function init(root){
    root.querySelectorAll('[data-scwb-tab]').forEach(btn => btn.addEventListener('click', function(){
      root.querySelectorAll('[data-scwb-tab]').forEach(b=>b.classList.remove('is-active'));
      root.querySelectorAll('[data-scwb-panel]').forEach(p=>p.classList.remove('is-active'));
      btn.classList.add('is-active');
      const panel = root.querySelector('[data-scwb-panel="'+btn.dataset.scwbTab+'"]'); if(panel) panel.classList.add('is-active');
    }));
    loadTools(root).catch(()=>{});
  }
  document.addEventListener('click', function(e){
    const toolButton = e.target.closest('[data-scwb-tool-id]');
    if(toolButton){const root=toolButton.closest('[data-scwb-compact]'); if(root){root.querySelector('[data-scwb-tab="tools"]').click(); const sel=root.querySelector('[data-scwb-tool-select]'); if(sel){sel.value=toolButton.dataset.scwbToolId;} openTool(root, toolButton.dataset.scwbToolId);} }
    const load = e.target.closest('[data-scwb-load-tool]');
    if(load){const root=load.closest('[data-scwb-compact]'); const sel=root.querySelector('[data-scwb-tool-select]'); openTool(root, sel.value);}
  });
  document.addEventListener('submit', async function(e){
    const ask = e.target.closest('[data-scwb-ask-form]');
    if(ask){
      e.preventDefault(); const root=ask.closest('[data-scwb-compact]'); const out=root.querySelector('[data-scwb-ask-output]'); out.hidden=false; out.innerHTML='<div class="scwb-loading">Retrieving Sustainable Catalyst context…</div>';
      const question = ask.querySelector('textarea').value;
      const data = await api('/ask', {method:'POST', body:JSON.stringify({question:question, topic:root.dataset.topic || 'research-library', mode:'compact'})});
      out.innerHTML = renderAnswer(data);
    }
    const visual = e.target.closest('[data-scwb-visual-form]');
    if(visual){
      e.preventDefault(); const root=visual.closest('[data-scwb-compact]'); const out=root.querySelector('[data-scwb-visual-output]'); out.hidden=false; out.innerHTML='<div class="scwb-loading">Rendering backend visualization…</div>';
      const inputs={}; new FormData(visual).forEach((v,k)=>inputs[k]=v);
      const data = await api('/run', {method:'POST', body:JSON.stringify({tool_id:'visual-analytics-studio', inputs:inputs})});
      out.innerHTML = renderResult(data);
    }
    const form = e.target.closest('[data-scwb-tool-form]');
    if(form){
      e.preventDefault(); const out=form.parentNode.querySelector('[data-scwb-tool-output]'); out.hidden=false; out.innerHTML='<div class="scwb-loading">Running backend analytics and graphing…</div>';
      const inputs={}; new FormData(form).forEach((v,k)=>inputs[k]=v);
      const data = await api('/run', {method:'POST', body:JSON.stringify({tool_id:form.dataset.toolId, inputs:inputs})});
      out.innerHTML = renderResult(data);
    }
  });
  document.addEventListener('DOMContentLoaded', function(){document.querySelectorAll('[data-scwb-compact]').forEach(init);});
})();
