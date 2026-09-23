<?php
/** Workbench v8.6.0 — Visual Research Canvas. */
if (!defined('ABSPATH')) { exit; }

function scwb_v860_backend_base() {
    return rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'), '/');
}

function scwb_v860_backend_request($path, $method='GET', $body=null) {
    $args=array('timeout'=>15,'headers'=>array('Accept'=>'application/json'));
    if ($method !== 'GET') {
        $args['method']=$method;
        $args['headers']['Content-Type']='application/json';
        $args['body']=wp_json_encode($body === null ? array() : $body);
    }
    $response=wp_remote_request(scwb_v860_backend_base().$path,$args);
    if (is_wp_error($response)) { return array('ok'=>false,'error'=>$response->get_error_message()); }
    $code=(int)wp_remote_retrieve_response_code($response);
    $decoded=json_decode(wp_remote_retrieve_body($response),true);
    if (!is_array($decoded)) { $decoded=array('ok'=>false,'error'=>'Invalid backend response'); }
    $decoded['_httpStatus']=$code;
    return $decoded;
}

function scwb_v860_status_shortcode() {
    $status=scwb_v860_backend_request('/v860/status');
    $ok=!empty($status['ok']);
    $version=isset($status['version'])?esc_html($status['version']):'unknown';
    return '<div class="scwb-v860-status"><strong>Visual Research Canvas '.esc_html($ok?'Online':'Unavailable').'</strong><br><span>Workbench '.$version.'</span></div>';
}
add_shortcode('sc_workbench_visual_research_canvas_status','scwb_v860_status_shortcode');

function scwb_v860_canvas_shortcode($atts=array()) {
    $atts=shortcode_atts(array('project'=>'','timeline'=>'80','height'=>'720'),$atts,'sc_workbench_visual_research_canvas');
    $project=sanitize_text_field($atts['project']);
    $timeline=max(1,min(250,(int)$atts['timeline']));
    $height=max(420,min(1400,(int)$atts['height']));
    $uid='scwb-v860-'.wp_generate_uuid4();
    $nonce=wp_create_nonce('wp_rest');
    ob_start();
    ?>
    <section id="<?php echo esc_attr($uid); ?>" class="scwb-v860-canvas" data-project="<?php echo esc_attr($project); ?>" data-timeline="<?php echo esc_attr($timeline); ?>" data-nonce="<?php echo esc_attr($nonce); ?>" style="--scwb-v860-height:<?php echo esc_attr($height); ?>px">
      <header class="scwb-v860-toolbar">
        <div>
          <div class="scwb-v860-kicker">SUSTAINABLE CATALYST WORKBENCH · V8.6.0</div>
          <h3>Visual Research Canvas</h3>
          <p>Arrange linked project, environment, asset, execution, and timeline objects without duplicating their scientific source records.</p>
        </div>
        <div class="scwb-v860-controls">
          <label>Project <input class="scwb-v860-project" value="<?php echo esc_attr($project); ?>" placeholder="project-key"></label>
          <button type="button" data-action="load">Load</button>
          <button type="button" data-action="fit">Fit</button>
          <button type="button" data-action="save">Save layout</button>
        </div>
      </header>
      <div class="scwb-v860-meta"><span data-role="status">Ready</span><span data-role="summary"></span></div>
      <div class="scwb-v860-stage">
        <svg class="scwb-v860-edges" aria-hidden="true"></svg>
        <div class="scwb-v860-nodes" role="application" aria-label="Visual research canvas"></div>
      </div>
      <footer class="scwb-v860-legend"><span>Project</span><span>Environment</span><span>Asset</span><span>Execution</span><span>Timeline</span><em>Layout is view state only; authoritative research objects remain in their owning Workbench subsystems.</em></footer>
    </section>
    <style>
      .scwb-v860-canvas{border:1px solid #222;background:#090909;color:#f5f5f5;font-family:Montserrat,Arial,sans-serif;overflow:hidden}
      .scwb-v860-toolbar{display:flex;justify-content:space-between;gap:24px;padding:18px 20px;border-bottom:1px solid #262626;background:#0e0e0e;align-items:flex-end;flex-wrap:wrap}
      .scwb-v860-toolbar h3{margin:3px 0 5px;font-size:24px}.scwb-v860-toolbar p{margin:0;max-width:760px;color:#bdbdbd;font-size:13px}.scwb-v860-kicker{font-size:10px;letter-spacing:.14em;color:#8fd6a3;font-weight:800}
      .scwb-v860-controls{display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap}.scwb-v860-controls label{font-size:11px;color:#aaa;display:grid;gap:4px}.scwb-v860-controls input{background:#151515;border:1px solid #333;color:#fff;padding:8px 10px;min-width:180px}.scwb-v860-controls button{background:#171717;border:1px solid #3a3a3a;color:#fff;padding:9px 12px;cursor:pointer;font-weight:700}.scwb-v860-controls button:hover{border-color:#777}
      .scwb-v860-meta{display:flex;justify-content:space-between;padding:7px 12px;background:#111;border-bottom:1px solid #202020;color:#9b9b9b;font-size:11px}
      .scwb-v860-stage{height:var(--scwb-v860-height);position:relative;overflow:auto;background-image:linear-gradient(#171717 1px,transparent 1px),linear-gradient(90deg,#171717 1px,transparent 1px);background-size:32px 32px;background-color:#0a0a0a}
      .scwb-v860-edges{position:absolute;left:0;top:0;width:2600px;height:2400px;pointer-events:none;overflow:visible}.scwb-v860-edges line{stroke:#454545;stroke-width:1.4}.scwb-v860-edges line[data-kind="lineage"]{stroke-dasharray:5 5;stroke:#647d6c}.scwb-v860-edges line[data-kind="researcher"]{stroke:#a16d75;stroke-width:2}
      .scwb-v860-nodes{position:relative;width:2600px;height:2400px;transform-origin:0 0}.scwb-v860-node{position:absolute;border:1px solid #363636;border-left:4px solid #888;background:#121212;box-shadow:0 5px 18px rgba(0,0,0,.28);padding:10px 11px;box-sizing:border-box;cursor:grab;user-select:none;overflow:hidden}.scwb-v860-node:active{cursor:grabbing}.scwb-v860-node[data-kind="project"]{border-left-color:#e5e5e5}.scwb-v860-node[data-kind="environment"]{border-left-color:#8fd6a3}.scwb-v860-node[data-kind="asset"]{border-left-color:#86a8d8}.scwb-v860-node[data-kind="execution"]{border-left-color:#d3a66f}.scwb-v860-node[data-kind="timeline"]{border-left-color:#aa85b8}.scwb-v860-node strong{display:block;font-size:12px;line-height:1.35;margin-bottom:6px}.scwb-v860-node small{display:block;color:#8f8f8f;font-size:9px;text-transform:uppercase;letter-spacing:.08em}.scwb-v860-node code{display:block;color:#bcbcbc;font-size:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:7px}.scwb-v860-node.is-selected{outline:2px solid #f0f0f0;outline-offset:2px}
      .scwb-v860-legend{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:9px 12px;border-top:1px solid #222;background:#0e0e0e;font-size:10px;color:#aaa}.scwb-v860-legend em{margin-left:auto;font-style:normal;color:#777}
      @media(max-width:800px){.scwb-v860-toolbar{align-items:stretch}.scwb-v860-controls{width:100%}.scwb-v860-controls label{flex:1}.scwb-v860-controls input{min-width:0;width:100%}.scwb-v860-stage{height:600px}}
    </style>
    <script>
    (function(){
      const root=document.getElementById(<?php echo wp_json_encode($uid); ?>); if(!root)return;
      const stage=root.querySelector('.scwb-v860-stage'), nodesEl=root.querySelector('.scwb-v860-nodes'), svg=root.querySelector('.scwb-v860-edges');
      const projectInput=root.querySelector('.scwb-v860-project'), statusEl=root.querySelector('[data-role="status"]'), summaryEl=root.querySelector('[data-role="summary"]');
      const restBase=<?php echo wp_json_encode(esc_url_raw(rest_url('sc-workbench/v1/visual-research-canvas/'))); ?>; const nonce=root.dataset.nonce;
      let canvas=null, selected=new Set(), drag=null;
      function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
      function project(){return (projectInput.value||'').trim();}
      function api(path,opts={}){opts.headers=Object.assign({'Accept':'application/json','X-WP-Nonce':nonce},opts.headers||{});return fetch(restBase+path,opts).then(async r=>{const b=await r.json();if(!r.ok||b.ok===false)throw new Error(b.error||b.message||b.detail||('HTTP '+r.status));return b;});}
      function center(n){return [Number(n.x)+Number(n.width)/2,Number(n.y)+Number(n.height)/2];}
      function drawEdges(){if(!canvas)return;svg.innerHTML='';const map=new Map(canvas.nodes.map(n=>[n.nodeId,n]));canvas.edges.forEach(e=>{const a=map.get(e.from),b=map.get(e.to);if(!a||!b||a.hidden||b.hidden)return;const [x1,y1]=center(a),[x2,y2]=center(b);const l=document.createElementNS('http://www.w3.org/2000/svg','line');for(const [k,v] of Object.entries({x1,y1,x2,y2}))l.setAttribute(k,v);l.dataset.kind=e.kind||'derived';svg.appendChild(l);});}
      function draw(){nodesEl.innerHTML='';if(!canvas)return;canvas.nodes.forEach(n=>{if(n.hidden)return;const el=document.createElement('div');el.className='scwb-v860-node'+(selected.has(n.nodeId)?' is-selected':'');el.dataset.id=n.nodeId;el.dataset.kind=n.kind;el.style.left=n.x+'px';el.style.top=n.y+'px';el.style.width=n.width+'px';el.style.height=n.height+'px';el.innerHTML='<small>'+esc(n.kind)+' · '+esc(n.sourceAuthority)+'</small><strong>'+esc(n.title)+'</strong><code>'+esc(n.sourceRef)+'</code>';el.addEventListener('click',e=>{if(!e.shiftKey)selected.clear();selected.has(n.nodeId)?selected.delete(n.nodeId):selected.add(n.nodeId);draw();});el.addEventListener('pointerdown',e=>{if(e.button!==0)return;drag={id:n.nodeId,startX:e.clientX,startY:e.clientY,x:n.x,y:n.y};el.setPointerCapture(e.pointerId);e.preventDefault();});el.addEventListener('pointermove',e=>{if(!drag||drag.id!==n.nodeId)return;n.x=Math.round(drag.x+(e.clientX-drag.startX));n.y=Math.round(drag.y+(e.clientY-drag.startY));el.style.left=n.x+'px';el.style.top=n.y+'px';drawEdges();});el.addEventListener('pointerup',()=>{drag=null;});nodesEl.appendChild(el);});drawEdges();summaryEl.textContent=canvas.nodeCount+' nodes · '+canvas.edgeCount+' links · layout r'+canvas.layoutRevision;}
      async function load(){const p=project();if(!p){statusEl.textContent='Enter a project key';return;}statusEl.textContent='Loading…';try{canvas=await api(encodeURIComponent(p)+'?timeline_limit='+encodeURIComponent(root.dataset.timeline));selected.clear();draw();statusEl.textContent='Canvas online · v'+canvas.version;}catch(e){statusEl.textContent='Error: '+e.message;}}
      async function save(){if(!canvas)return;statusEl.textContent='Saving layout…';const body={expectedLayoutRevision:canvas.layoutRevision,nodes:canvas.nodes.map(n=>({nodeId:n.nodeId,x:n.x,y:n.y,width:n.width,height:n.height,hidden:!!n.hidden,pinned:!!n.pinned})),links:canvas.edges.filter(e=>e.kind==='researcher').map(e=>({fromNodeId:e.from,toNodeId:e.to,relation:e.relation,label:e.label||''})),viewport:{x:stage.scrollLeft,y:stage.scrollTop,zoom:1},layers:canvas.layers||{},reason:'wordpress-visual-canvas-save',actor:'wordpress'};try{const saved=await api(encodeURIComponent(project())+'/layout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});canvas.layoutRevision=saved.layoutRevision;canvas.layoutHash=saved.layoutHash;statusEl.textContent='Layout saved · revision '+saved.layoutRevision;draw();}catch(e){statusEl.textContent='Save error: '+e.message;}}
      function fit(){if(!canvas||!canvas.nodes.length)return;let minX=Infinity,minY=Infinity;canvas.nodes.filter(n=>!n.hidden).forEach(n=>{minX=Math.min(minX,n.x);minY=Math.min(minY,n.y)});stage.scrollLeft=Math.max(0,minX-30);stage.scrollTop=Math.max(0,minY-30);}
      root.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>({load,save,fit}[b.dataset.action]||(()=>{}))()));
      if(project())load();
    })();
    </script>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_workbench_visual_research_canvas','scwb_v860_canvas_shortcode');

add_action('rest_api_init',function(){
    register_rest_route('sc-workbench/v1','/visual-research-canvas/status',array('methods'=>'GET','permission_callback'=>'__return_true','callback'=>function(){ return rest_ensure_response(scwb_v860_backend_request('/v860/status')); }));
    register_rest_route('sc-workbench/v1','/visual-research-canvas/(?P<project>[A-Za-z0-9._:-]+)',array('methods'=>'GET','permission_callback'=>'__return_true','callback'=>function($req){
        $project=rawurlencode((string)$req['project']); $timeline=max(1,min(250,(int)$req->get_param('timeline_limit'))); if(!$timeline){$timeline=80;}
        $result=scwb_v860_backend_request('/research-canvas/'.$project.'?timeline_limit='.$timeline); $status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200; unset($result['_httpStatus']); return new WP_REST_Response($result,$status);
    }));
    register_rest_route('sc-workbench/v1','/visual-research-canvas/(?P<project>[A-Za-z0-9._:-]+)/layout',array('methods'=>'POST','permission_callback'=>function(){return current_user_can('edit_posts');},'callback'=>function($req){
        $project=rawurlencode((string)$req['project']); $body=$req->get_json_params(); if(!is_array($body)){$body=array();}
        $result=scwb_v860_backend_request('/research-canvas/'.$project.'/layout/save','POST',$body); $status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200; unset($result['_httpStatus']); return new WP_REST_Response($result,$status);
    }));
    register_rest_route('sc-workbench/v1','/visual-research-canvas/(?P<project>[A-Za-z0-9._:-]+)/lineage',array('methods'=>'GET','permission_callback'=>'__return_true','callback'=>function($req){
        $project=rawurlencode((string)$req['project']); $result=scwb_v860_backend_request('/research-canvas/'.$project.'/lineage-overlay'); $status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200; unset($result['_httpStatus']); return new WP_REST_Response($result,$status);
    }));
});
