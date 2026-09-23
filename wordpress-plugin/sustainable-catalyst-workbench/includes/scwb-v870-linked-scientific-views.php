<?php
/** Workbench v8.7.0 — Linked Scientific Views & Cross-Filtering. */
if (!defined('ABSPATH')) { exit; }

function scwb_v870_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v860_backend_request')) { return scwb_v860_backend_request($path,$method,$body); }
    $base=rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'), '/');
    $args=array('timeout'=>20,'headers'=>array('Accept'=>'application/json'));
    if ($method !== 'GET') { $args['method']=$method; $args['headers']['Content-Type']='application/json'; $args['body']=wp_json_encode($body===null?array():$body); }
    $response=wp_remote_request($base.$path,$args);
    if (is_wp_error($response)) { return array('ok'=>false,'error'=>$response->get_error_message(),'_httpStatus'=>502); }
    $code=(int)wp_remote_retrieve_response_code($response); $decoded=json_decode(wp_remote_retrieve_body($response),true);
    if (!is_array($decoded)) { $decoded=array('ok'=>false,'error'=>'Invalid backend response'); }
    $decoded['_httpStatus']=$code; return $decoded;
}

function scwb_v870_status_shortcode() {
    $status=scwb_v870_backend_request('/v870/status'); $ok=!empty($status['ok']); $version=isset($status['version'])?esc_html($status['version']):'unknown';
    return '<div class="scwb-v870-status"><strong>Linked Scientific Views '.esc_html($ok?'Online':'Unavailable').'</strong><br><span>Workbench '.$version.'</span></div>';
}
add_shortcode('sc_workbench_linked_scientific_views_status','scwb_v870_status_shortcode');

function scwb_v870_views_shortcode($atts=array()) {
    $atts=shortcode_atts(array('project'=>'','timeline'=>'120','height'=>'760'),$atts,'sc_workbench_linked_scientific_views');
    $project=sanitize_text_field($atts['project']); $timeline=max(1,min(250,(int)$atts['timeline'])); $height=max(520,min(1600,(int)$atts['height']));
    $uid='scwb-v870-'.wp_generate_uuid4(); $nonce=wp_create_nonce('wp_rest'); ob_start(); ?>
    <section id="<?php echo esc_attr($uid); ?>" class="scwb-v870" data-project="<?php echo esc_attr($project); ?>" data-timeline="<?php echo esc_attr($timeline); ?>" data-nonce="<?php echo esc_attr($nonce); ?>" style="--scwb-v870-height:<?php echo esc_attr($height); ?>px">
      <header class="scwb-v870-head"><div><div class="scwb-v870-kicker">SUSTAINABLE CATALYST WORKBENCH · V8.7.0</div><h3>Linked Scientific Views &amp; Cross-Filtering</h3><p>Filter once and inspect the same authoritative research objects across canvas, asset, execution, timeline, lineage, and facet views.</p></div><div class="scwb-v870-project"><label>Project <input data-role="project" value="<?php echo esc_attr($project); ?>" placeholder="project-key"></label><button data-action="load" type="button">Load</button></div></header>
      <div class="scwb-v870-filterbar">
        <label>Search <input data-filter="text" placeholder="title, ref, tag, runtime…"></label>
        <label>Kind <select data-filter="kind"><option value="">All</option><option value="asset">Assets</option><option value="execution">Executions</option><option value="timeline">Timeline</option><option value="project">Project</option><option value="environment">Environment</option></select></label>
        <label>Runtime <select data-filter="runtime"><option value="">All</option></select></label>
        <label>Status <select data-filter="status"><option value="">All</option></select></label>
        <label><input type="checkbox" data-filter="neighbors"> Include neighbors</label>
        <button data-action="apply" type="button">Apply</button><button data-action="clear" type="button">Clear</button>
      </div>
      <div class="scwb-v870-meta"><span data-role="status">Ready</span><span data-role="summary"></span></div>
      <div class="scwb-v870-grid" style="height:var(--scwb-v870-height)">
        <aside class="scwb-v870-facets"><h4>Facets</h4><div data-role="facets"></div></aside>
        <main class="scwb-v870-main">
          <nav class="scwb-v870-tabs"><button class="is-active" data-view="canvas">Canvas</button><button data-view="assets">Assets</button><button data-view="executions">Executions</button><button data-view="timeline">Timeline</button><button data-view="lineage">Lineage</button></nav>
          <div class="scwb-v870-view is-active" data-panel="canvas"><svg data-role="edges" aria-hidden="true"></svg><div data-role="nodes"></div></div>
          <div class="scwb-v870-view" data-panel="assets"><table><thead><tr><th>Asset</th><th>Type</th><th>Origin</th><th>Revision</th></tr></thead><tbody data-role="assets"></tbody></table></div>
          <div class="scwb-v870-view" data-panel="executions"><table><thead><tr><th>Execution</th><th>Runtime</th><th>Status</th><th>Revision</th></tr></thead><tbody data-role="executions"></tbody></table></div>
          <div class="scwb-v870-view" data-panel="timeline"><table><thead><tr><th>Time</th><th>Event</th><th>Type</th><th>Source</th></tr></thead><tbody data-role="timeline"></tbody></table></div>
          <div class="scwb-v870-view" data-panel="lineage"><div data-role="lineage"></div></div>
        </main>
      </div>
      <footer>Cross-filter and selection state are visual analysis state only. They do not alter scientific records, infer causality, or choose a preferred result.</footer>
    </section>
    <style>
      .scwb-v870{border:1px solid #222;background:#090909;color:#f4f4f4;font-family:Montserrat,Arial,sans-serif}.scwb-v870-head{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;padding:18px 20px;background:#0e0e0e;border-bottom:1px solid #252525;flex-wrap:wrap}.scwb-v870-kicker{font-size:10px;letter-spacing:.14em;color:#8fd6a3;font-weight:800}.scwb-v870 h3{margin:3px 0 5px;font-size:24px}.scwb-v870 p{margin:0;color:#b8b8b8;max-width:780px;font-size:13px}.scwb-v870 label{font-size:10px;color:#aaa;display:grid;gap:4px}.scwb-v870 input,.scwb-v870 select{background:#151515;border:1px solid #333;color:#fff;padding:8px}.scwb-v870 button{background:#171717;border:1px solid #353535;color:#eee;padding:8px 10px;cursor:pointer}.scwb-v870 button:hover,.scwb-v870 button.is-active{border-color:#8fd6a3;color:#fff}.scwb-v870-project{display:flex;gap:7px;align-items:flex-end}.scwb-v870-filterbar{display:flex;gap:8px;align-items:end;flex-wrap:wrap;padding:10px 12px;background:#111;border-bottom:1px solid #222}.scwb-v870-filterbar label:first-child{min-width:240px;flex:1}.scwb-v870-filterbar label:has(input[type=checkbox]){display:flex;align-items:center;gap:6px;padding-bottom:8px}.scwb-v870-meta{display:flex;justify-content:space-between;padding:6px 12px;color:#8f8f8f;font-size:10px;border-bottom:1px solid #202020}.scwb-v870-grid{display:grid;grid-template-columns:220px 1fr;min-height:520px}.scwb-v870-facets{border-right:1px solid #222;padding:12px;overflow:auto}.scwb-v870-facets h4{margin:0 0 10px}.scwb-v870-facet{margin-bottom:12px}.scwb-v870-facet strong{display:block;font-size:10px;text-transform:uppercase;color:#888;margin-bottom:4px}.scwb-v870-facet button{display:flex;width:100%;justify-content:space-between;padding:5px 7px;font-size:10px;margin:2px 0}.scwb-v870-main{min-width:0;display:flex;flex-direction:column}.scwb-v870-tabs{display:flex;gap:5px;padding:8px;border-bottom:1px solid #222}.scwb-v870-view{display:none;position:relative;flex:1;overflow:auto}.scwb-v870-view.is-active{display:block}.scwb-v870-view[data-panel=canvas]{background-image:linear-gradient(#171717 1px,transparent 1px),linear-gradient(90deg,#171717 1px,transparent 1px);background-size:32px 32px}.scwb-v870-view[data-panel=canvas] svg{position:absolute;width:2400px;height:2200px;pointer-events:none}.scwb-v870-view[data-panel=canvas] svg line{stroke:#444;stroke-width:1.3}.scwb-v870-view[data-panel=canvas]>div{position:relative;width:2400px;height:2200px}.scwb-v870-node{position:absolute;background:#121212;border:1px solid #383838;border-left:4px solid #888;padding:8px;box-sizing:border-box;overflow:hidden;cursor:pointer}.scwb-v870-node[data-kind=asset]{border-left-color:#86a8d8}.scwb-v870-node[data-kind=execution]{border-left-color:#d3a66f}.scwb-v870-node[data-kind=timeline]{border-left-color:#aa85b8}.scwb-v870-node.is-selected,tr.is-selected{outline:2px solid #fff;outline-offset:-2px}.scwb-v870-node small{font-size:8px;color:#888;text-transform:uppercase}.scwb-v870-node strong{display:block;font-size:11px;margin-top:4px}.scwb-v870 table{border-collapse:collapse;width:100%;font-size:11px}.scwb-v870 th,.scwb-v870 td{text-align:left;border-bottom:1px solid #222;padding:8px}.scwb-v870 tbody tr{cursor:pointer}.scwb-v870 tbody tr:hover{background:#151515}.scwb-v870-lineage-row{display:grid;grid-template-columns:90px 1fr 70px;gap:8px;padding:7px 10px;border-bottom:1px solid #222;font-size:10px}.scwb-v870 footer{padding:8px 12px;border-top:1px solid #222;color:#777;font-size:9px}@media(max-width:800px){.scwb-v870-grid{grid-template-columns:1fr}.scwb-v870-facets{display:none}.scwb-v870-filterbar label:first-child{min-width:100%}}
    </style>
    <script>
    (function(){
      const root=document.getElementById(<?php echo wp_json_encode($uid); ?>); if(!root)return; const rest=<?php echo wp_json_encode(esc_url_raw(rest_url('sc-workbench/v1/linked-scientific-views/'))); ?>, nonce=root.dataset.nonce;
      const $=s=>root.querySelector(s), $$=s=>Array.from(root.querySelectorAll(s)); let result=null, selected=new Set(), active='canvas';
      const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
      const api=(path,body)=>fetch(rest+path,{method:body?'POST':'GET',headers:{'Accept':'application/json','Content-Type':'application/json','X-WP-Nonce':nonce},body:body?JSON.stringify(body):undefined}).then(async r=>{const b=await r.json();if(!r.ok||b.ok===false)throw new Error(typeof b.detail==='string'?b.detail:(b.error||'Request failed'));return b;});
      function filters(){const kind=$('[data-filter=kind]').value,runtime=$('[data-filter=runtime]').value,status=$('[data-filter=status]').value;return {text:$('[data-filter=text]').value||'',kinds:kind?[kind]:[],runtimeKinds:runtime?[runtime]:[],executionStatuses:status?[status]:[],includeNeighbors:$('[data-filter=neighbors]').checked};}
      function project(){return $('[data-role=project]').value.trim();}
      function body(){return {projectKey:project(),filters:filters(),selectedNodeIds:Array.from(selected),sourceView:active,timelineLimit:Number(root.dataset.timeline||120)};}
      function rowClick(id,e){if(!e.shiftKey)selected.clear();selected.has(id)?selected.delete(id):selected.add(id); apply();}
      function renderCanvas(){const p=result.views.canvas,nodes=p.nodes||[],edges=p.edges||[],box=$('[data-role=nodes]'),svg=$('[data-role=edges]');box.innerHTML='';svg.innerHTML='';const map=new Map(nodes.map(n=>[n.nodeId,n]));nodes.forEach(n=>{const d=document.createElement('div');d.className='scwb-v870-node'+(selected.has(n.nodeId)?' is-selected':'');d.dataset.kind=n.kind;d.style.cssText='left:'+n.x+'px;top:'+n.y+'px;width:'+n.width+'px;height:'+n.height+'px';d.innerHTML='<small>'+esc(n.kind)+'</small><strong>'+esc(n.title)+'</strong>';d.addEventListener('click',e=>rowClick(n.nodeId,e));box.appendChild(d)});edges.forEach(e=>{const a=map.get(e.from),b=map.get(e.to);if(!a||!b)return;const l=document.createElementNS('http://www.w3.org/2000/svg','line');l.setAttribute('x1',a.x+a.width/2);l.setAttribute('y1',a.y+a.height/2);l.setAttribute('x2',b.x+b.width/2);l.setAttribute('y2',b.y+b.height/2);svg.appendChild(l)});}
      function rows(role,rows,cols){const tb=$('[data-role='+role+']');tb.innerHTML='';rows.forEach(r=>{const tr=document.createElement('tr');if(selected.has(r.nodeId))tr.classList.add('is-selected');tr.innerHTML=cols.map(c=>'<td>'+esc(typeof c==='function'?c(r):r[c])+'</td>').join('');tr.addEventListener('click',e=>rowClick(r.nodeId,e));tb.appendChild(tr)});}
      function renderFacets(){const el=$('[data-role=facets]');el.innerHTML='';Object.entries(result.views.facets||{}).forEach(([k,vals])=>{if(!vals.length)return;const d=document.createElement('div');d.className='scwb-v870-facet';d.innerHTML='<strong>'+esc(k)+'</strong>'+vals.slice(0,12).map(x=>'<button type="button"><span>'+esc(x.value)+'</span><b>'+x.count+'</b></button>').join('');el.appendChild(d)});}
      function renderLineage(){const el=$('[data-role=lineage]');el.innerHTML=(result.views.lineage.nodes||[]).map(n=>'<div class="scwb-v870-lineage-row'+(selected.has(n.nodeId)?' is-selected':'')+'"><span>'+esc(n.kind)+'</span><span>'+esc(n.title)+'</span><b>'+esc(n.linkedDegree)+'</b></div>').join('');}
      function fillSelect(sel,facet){const el=$(sel),current=el.value,vals=(result.views.facets[facet]||[]);el.innerHTML='<option value="">All</option>'+vals.map(x=>'<option value="'+esc(x.value)+'">'+esc(x.value)+' ('+x.count+')</option>').join('');if(Array.from(el.options).some(o=>o.value===current))el.value=current;}
      function render(){renderCanvas();rows('assets',result.views.assets.rows||[],['title','assetType','origin','assetRevision']);rows('executions',result.views.executions.rows||[],['title','runtimeKind','status','jobRevision']);rows('timeline',result.views.timeline.rows||[],['at','title','eventType','source']);renderFacets();renderLineage();fillSelect('[data-filter=runtime]','runtimeKind');fillSelect('[data-filter=status]','executionStatus');$('[data-role=summary]').textContent=result.filteredNodeCount+' / '+result.sourceNodeCount+' nodes · '+result.filteredEdgeCount+' links · '+selected.size+' selected';}
      async function apply(){if(!project()){ $('[data-role=status]').textContent='Enter a project key';return;} $('[data-role=status]').textContent='Filtering…';try{result=await api('query',body());selected=new Set(result.selectedNodeIds||[]);render();$('[data-role=status]').textContent='Linked views online · v'+result.version;}catch(e){$('[data-role=status]').textContent='Error: '+e.message;}}
      function clear(){selected.clear();$('[data-filter=text]').value='';$('[data-filter=kind]').value='';$('[data-filter=runtime]').value='';$('[data-filter=status]').value='';$('[data-filter=neighbors]').checked=false;apply();}
      $$('[data-view]').forEach(b=>b.addEventListener('click',()=>{active=b.dataset.view;$$('[data-view]').forEach(x=>x.classList.toggle('is-active',x===b));$$('[data-panel]').forEach(x=>x.classList.toggle('is-active',x.dataset.panel===active));}));
      $('[data-action=load]').addEventListener('click',apply);$('[data-action=apply]').addEventListener('click',apply);$('[data-action=clear]').addEventListener('click',clear);$('[data-filter=text]').addEventListener('keydown',e=>{if(e.key==='Enter')apply()}); if(project())apply();
    })();
    </script>
    <?php return ob_get_clean();
}
add_shortcode('sc_workbench_linked_scientific_views','scwb_v870_views_shortcode');

add_action('rest_api_init',function(){
    register_rest_route('sc-workbench/v1','/linked-scientific-views/status',array('methods'=>'GET','permission_callback'=>'__return_true','callback'=>function(){return rest_ensure_response(scwb_v870_backend_request('/v870/status'));}));
    register_rest_route('sc-workbench/v1','/linked-scientific-views/query',array('methods'=>'POST','permission_callback'=>'__return_true','callback'=>function($req){$body=$req->get_json_params();if(!is_array($body)){$body=array();}$result=scwb_v870_backend_request('/linked-scientific-views/query','POST',$body);$status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200;unset($result['_httpStatus']);return new WP_REST_Response($result,$status);}));
    register_rest_route('sc-workbench/v1','/linked-scientific-views/selection',array('methods'=>'POST','permission_callback'=>'__return_true','callback'=>function($req){$body=$req->get_json_params();if(!is_array($body)){$body=array();}$result=scwb_v870_backend_request('/linked-scientific-views/selection/resolve','POST',$body);$status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200;unset($result['_httpStatus']);return new WP_REST_Response($result,$status);}));
});
