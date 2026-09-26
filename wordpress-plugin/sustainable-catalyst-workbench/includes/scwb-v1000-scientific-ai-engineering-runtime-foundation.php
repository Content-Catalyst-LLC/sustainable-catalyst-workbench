<?php
/** Workbench v10.0.0 — Scientific AI Engineering Runtime Foundation. */
if (!defined('ABSPATH')) { exit; }
function scwb_v1000_backend_request($path,$method='GET',$body=null){
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v1000_status_shortcode(){ $r=scwb_v1000_backend_request('/v1000/status'); if(!empty($r['ok'])){return '<div class="scwb-v1000-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Scientific AI Engineering foundation ready</div>';} return '<div class="scwb-v1000-status">Scientific AI Engineering foundation unavailable</div>'; }
add_shortcode('sc_workbench_ai_engineering_status','scwb_v1000_status_shortcode');
function scwb_v1000_ai_engineering_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>''),$atts,'sc_workbench_ai_engineering'); $uid='scwb-v1000-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1000" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1000{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1000 header{display:flex;justify-content:space-between;gap:16px;align-items:end;flex-wrap:wrap}.scwb-v1000 label{display:block;margin:8px 0}.scwb-v1000 input,.scwb-v1000 select,.scwb-v1000 textarea{width:100%;max-width:760px}.scwb-v1000 button{padding:9px 14px;margin:4px}.scwb-v1000 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><div><small>SUSTAINABLE CATALYST WORKBENCH · V10.0.0</small><h3>Scientific AI Engineering Runtime Foundation</h3><div>Compose provenance-first AI experiments without automatically executing models or providers.</div></div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Experiment key <input data-f="experimentKey" value="ai-experiment-1"></label>
<label>Title <input data-f="title" value="Scientific AI experiment"></label>
<label>Mode <select data-f="mode"><option>inference</option><option>training</option><option>evaluation</option><option>hybrid</option><option>scientific-ml</option></select></label>
<label>Provider <select data-f="provider"><option>local</option><option>workspace-ml</option><option>openai-compatible</option><option>huggingface</option><option>custom</option></select></label>
<label>Model ID <input data-f="modelId" value="model-placeholder"></label>
<label>Task <select data-f="task"><option>custom</option><option>text-generation</option><option>classification</option><option>regression</option><option>embedding</option><option>forecasting</option><option>surrogate-modeling</option><option>multimodal</option></select></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose experiment</button> <button data-action="save" type="button">Save experiment</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s);const body=()=>{const mode=q('[data-f="mode"]').value;return {projectKey:q('[data-f="projectKey"]').value.trim(),experimentKey:q('[data-f="experimentKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),mode,model:{modelKey:'primary-model',provider:q('[data-f="provider"]').value,modelId:q('[data-f="modelId"]').value.trim(),task:q('[data-f="task"]').value},datasets:[],training:{enabled:mode==='training'||mode==='hybrid'||mode==='scientific-ml'},inference:{enabled:mode!=='training'},evaluationHooks:[],notes:q('[data-f="notes"]').value};};const api=async(path)=>{const r=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1000')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce},body:JSON.stringify(body())});return await r.json();};async function go(path){q('[data-role="status"]').textContent='Working…';try{const out=await api(path);q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}q('[data-action="compose"]').onclick=()=>go('/compose');q('[data-action="save"]').onclick=()=>go('/experiments');})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_engineering','scwb_v1000_ai_engineering_shortcode');
add_action('rest_api_init',function(){ $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1000','/compose',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1000_backend_request('/ai-engineering/compose','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1000','/experiments',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1000_backend_request('/ai-engineering/experiments','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
