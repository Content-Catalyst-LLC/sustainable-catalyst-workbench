<?php
/** Workbench v10.3.0 — AI Evaluation & Benchmark Workspace. */
if (!defined('ABSPATH')) { exit; }
function scwb_v1030_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v1030_status_shortcode(){ $r=scwb_v1030_backend_request('/v1030/status'); if(!empty($r['ok'])){return '<div class="scwb-v1030-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · AI Evaluation &amp; Benchmark Workspace ready</div>';} return '<div class="scwb-v1030-status">AI Evaluation &amp; Benchmark Workspace unavailable</div>'; }
add_shortcode('sc_workbench_ai_evaluation_status','scwb_v1030_status_shortcode');
function scwb_v1030_evaluation_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>''),$atts,'sc_workbench_ai_evaluation'); $uid='scwb-v1030-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1030" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1030{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1030 label{display:block;margin:8px 0}.scwb-v1030 input,.scwb-v1030 textarea{width:100%;max-width:850px}.scwb-v1030 button{padding:9px 14px;margin:4px}.scwb-v1030 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.3.0</small><h3>AI Evaluation &amp; Benchmark Workspace</h3><div>Define immutable registry-backed benchmarks and inspect evaluation results without automatic ranking or model promotion.</div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Benchmark key <input data-f="benchmarkKey" value="benchmark-1"></label>
<label>Title <input data-f="title" value="AI evaluation benchmark"></label>
<label>Task <input data-f="task" value="classification"></label>
<label>Dataset record hashes JSON <textarea data-f="datasets" rows="3">[]</textarea></label>
<label>Metrics JSON <textarea data-f="metrics" rows="6">[{"metricKey":"accuracy","title":"Accuracy","kind":"accuracy","direction":"higher-is-better","regressionTolerance":0.01}]</textarea></label>
<label>Diagnostic slices JSON <textarea data-f="slices" rows="4">[]</textarea></label>
<label>Baseline model record hash <input data-f="baseline"></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button><button data-action="save" type="button">Save benchmark</button><button data-action="list" type="button">List benchmarks</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1030')); ?>;const api=async(path,method='GET',body=null)=>{const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();};const body=()=>({projectKey:q('[data-f="projectKey"]').value.trim(),benchmarkKey:q('[data-f="benchmarkKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),task:q('[data-f="task"]').value.trim(),datasetRecordHashes:JSON.parse(q('[data-f="datasets"]').value||'[]'),metrics:JSON.parse(q('[data-f="metrics"]').value||'[]'),slices:JSON.parse(q('[data-f="slices"]').value||'[]'),baselineModelRecordHash:q('[data-f="baseline"]').value.trim(),notes:q('[data-f="notes"]').value});async function run(a){q('[data-role="status"]').textContent='Working…';try{let out;if(a==='list'){out=await api('/benchmarks/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(a==='compose'?'/benchmarks/compose':'/benchmarks','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_evaluation','scwb_v1030_evaluation_shortcode');
add_action('rest_api_init',function(){ $perm=function(){return current_user_can('edit_posts');};
    foreach(array('benchmarks/compose','benchmarks','execution-plan','results','compare') as $route){
        register_rest_route('sc-workbench/v1/v1030','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1030_backend_request('/ai-evaluation/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1030','/benchmarks/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1030_backend_request('/ai-evaluation/benchmarks/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
