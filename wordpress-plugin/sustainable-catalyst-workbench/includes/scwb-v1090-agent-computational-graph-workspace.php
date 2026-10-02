<?php
/** Workbench v10.9.0 — Agent / Computational Graph Workspace. */
if (!defined('ABSPATH')) { exit; }

function scwb_v1090_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);}
    $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($r);
    $d=json_decode(wp_remote_retrieve_body($r),true);
    if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}
    $d['_httpStatus']=$code; return $d;
}

function scwb_v1090_status_shortcode(){
    $r=scwb_v1090_backend_request('/v1090/status');
    if(!empty($r['ok'])){return '<div class="scwb-v1090-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Agent / Computational Graph Workspace ready</div>';}
    return '<div class="scwb-v1090-status">Agent / Computational Graph Workspace unavailable</div>';
}
add_shortcode('sc_workbench_agent_graph_status','scwb_v1090_status_shortcode');

function scwb_v1090_workspace_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>''),$atts,'sc_workbench_agent_graph');
    $uid='scwb-v1090-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1090" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1090{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1090 label{display:block;margin:8px 0}.scwb-v1090 input,.scwb-v1090 textarea{width:100%;max-width:900px}.scwb-v1090 button{padding:9px 14px;margin:4px}.scwb-v1090 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}.scwb-v1090 .boundary{border-left:4px solid #b00020;padding-left:10px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.9.0</small><h3>Agent / Computational Graph Workspace</h3><div>Define governed computational agents, DAG workflows, tool contracts, approval gates, checkpoints, handoffs, and replay plans.</div></header>
<p class="boundary"><strong>Execution boundary:</strong> composing a graph does not execute tools, perform external side effects, or bypass human approval.</p>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Graph key <input data-f="graphKey" value="research-agent-graph"></label>
<label>Title <input data-f="title" value="Research computational graph"></label>
<label>Agents JSON <textarea data-f="agents" rows="6">[]</textarea></label>
<label>Tools JSON <textarea data-f="tools" rows="6">[]</textarea></label>
<label>Nodes JSON <textarea data-f="nodes" rows="8">[{"nodeKey":"start","kind":"compute","title":"Start"}]</textarea></label>
<label>Edges JSON <textarea data-f="edges" rows="6">[]</textarea></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button><button data-action="save" type="button">Save graph</button><button data-action="list" type="button">List graphs</button></div>
<p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1090')); ?>;const api=async(path,method='GET',body=null)=>{const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();};const body=()=>({projectKey:q('[data-f="projectKey"]').value.trim(),graphKey:q('[data-f="graphKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),agents:JSON.parse(q('[data-f="agents"]').value||'[]'),tools:JSON.parse(q('[data-f="tools"]').value||'[]'),nodes:JSON.parse(q('[data-f="nodes"]').value||'[]'),edges:JSON.parse(q('[data-f="edges"]').value||'[]'),notes:q('[data-f="notes"]').value});async function run(a){q('[data-role="status"]').textContent='Working…';try{let out;if(a==='list'){out=await api('/graphs/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(a==='compose'?'/graphs/compose':'/graphs','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_agent_graph','scwb_v1090_workspace_shortcode');

add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('graphs/compose','graphs','runs','replay-plan','diagnose','core-plan') as $route){
        register_rest_route('sc-workbench/v1/v1090','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1090_backend_request('/agent-graph/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1090','/graphs/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1090_backend_request('/agent-graph/graphs/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1090','/runs/(?P<project>[^/]+)/(?P<graph>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1090_backend_request('/agent-graph/runs/'.rawurlencode($r['project']).'/'.rawurlencode($r['graph']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
