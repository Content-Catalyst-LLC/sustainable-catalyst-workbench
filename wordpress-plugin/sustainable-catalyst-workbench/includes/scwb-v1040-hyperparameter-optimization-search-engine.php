<?php
/** Workbench v10.4.0 — Hyperparameter Optimization & Search Engine. */
if (!defined('ABSPATH')) { exit; }
function scwb_v1040_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v1040_status_shortcode(){ $r=scwb_v1040_backend_request('/v1040/status'); if(!empty($r['ok'])){return '<div class="scwb-v1040-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Hyperparameter Optimization &amp; Search Engine ready</div>';} return '<div class="scwb-v1040-status">Hyperparameter Optimization &amp; Search Engine unavailable</div>'; }
add_shortcode('sc_workbench_ai_optimization_status','scwb_v1040_status_shortcode');
function scwb_v1040_optimization_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>'','training_run_hash'=>'','benchmark_hash'=>''),$atts,'sc_workbench_ai_optimization'); $uid='scwb-v1040-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1040" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1040{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1040 label{display:block;margin:8px 0}.scwb-v1040 input,.scwb-v1040 textarea,.scwb-v1040 select{width:100%;max-width:850px}.scwb-v1040 button{padding:9px 14px;margin:4px}.scwb-v1040 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.4.0</small><h3>Hyperparameter Optimization &amp; Search Engine</h3><div>Compose reproducible search studies and deterministic trial manifests without automatic training, model promotion, or winner selection.</div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Search key <input data-f="searchKey" value="search-1"></label>
<label>Title <input data-f="title" value="Hyperparameter search"></label>
<label>Base training run hash <input data-f="training" value="<?php echo esc_attr($atts['training_run_hash']); ?>"></label>
<label>Benchmark hash <input data-f="benchmark" value="<?php echo esc_attr($atts['benchmark_hash']); ?>"></label>
<label>Objective metric <input data-f="metric" value="accuracy"></label>
<label>Objective direction <select data-f="direction"><option value="maximize">maximize</option><option value="minimize">minimize</option></select></label>
<label>Strategy <select data-f="strategy"><option>grid</option><option>random</option><option>latin-hypercube</option><option>bayesian-contract</option><option>custom</option></select></label>
<label>Parameters JSON <textarea data-f="parameters" rows="8">[{"parameterKey":"lr","path":"hyperparameters.learningRate","kind":"float","minimum":0.00001,"maximum":0.001,"scale":"log"}]</textarea></label>
<label>Max trials <input data-f="maxTrials" type="number" min="1" value="20"></label>
<label>External optimizer ref <input data-f="external"></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button><button data-action="save" type="button">Save search</button><button data-action="list" type="button">List searches</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1040')); ?>;const api=async(path,method='GET',body=null)=>{const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();};const body=()=>({projectKey:q('[data-f="projectKey"]').value.trim(),searchKey:q('[data-f="searchKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),baseTrainingRunHash:q('[data-f="training"]').value.trim(),benchmarkHash:q('[data-f="benchmark"]').value.trim(),objective:{metricKey:q('[data-f="metric"]').value.trim(),direction:q('[data-f="direction"]').value},parameters:JSON.parse(q('[data-f="parameters"]').value||'[]'),strategy:q('[data-f="strategy"]').value,budget:{maxTrials:Number(q('[data-f="maxTrials"]').value||20)},externalOptimizerRef:q('[data-f="external"]').value.trim(),notes:q('[data-f="notes"]').value});async function run(a){q('[data-role="status"]').textContent='Working…';try{let out;if(a==='list'){out=await api('/searches/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(a==='compose'?'/searches/compose':'/searches','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_optimization','scwb_v1040_optimization_shortcode');
add_action('rest_api_init',function(){ $perm=function(){return current_user_can('edit_posts');};
    foreach(array('searches/compose','searches','trials/generate','execution-plan','trial-results','analyze') as $route){
        register_rest_route('sc-workbench/v1/v1040','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1040_backend_request('/ai-optimization/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1040','/searches/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1040_backend_request('/ai-optimization/searches/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
