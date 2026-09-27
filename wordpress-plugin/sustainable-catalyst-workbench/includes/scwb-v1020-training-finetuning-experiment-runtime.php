<?php
/** Workbench v10.2.0 — Training & Fine-Tuning Experiment Runtime. */
if (!defined('ABSPATH')) { exit; }
function scwb_v1020_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v1020_status_shortcode(){ $r=scwb_v1020_backend_request('/v1020/status'); if(!empty($r['ok'])){return '<div class="scwb-v1020-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Training &amp; Fine-Tuning Runtime ready</div>';} return '<div class="scwb-v1020-status">Training &amp; Fine-Tuning Runtime unavailable</div>'; }
add_shortcode('sc_workbench_ai_training_status','scwb_v1020_status_shortcode');
function scwb_v1020_training_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>'','experiment_hash'=>'','binding_hash'=>'','model_hash'=>''),$atts,'sc_workbench_ai_training'); $uid='scwb-v1020-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1020" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1020{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1020 header{margin-bottom:12px}.scwb-v1020 label{display:block;margin:8px 0}.scwb-v1020 input,.scwb-v1020 select,.scwb-v1020 textarea{width:100%;max-width:820px}.scwb-v1020 button{padding:9px 14px;margin:4px}.scwb-v1020 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.2.0</small><h3>Training &amp; Fine-Tuning Experiment Runtime</h3><div>Prepare immutable registry-backed training runs. Execution remains explicit and separately authorized.</div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Experiment hash <input data-f="experimentHash" value="<?php echo esc_attr($atts['experiment_hash']); ?>"></label>
<label>Registry binding hash <input data-f="registryBindingHash" value="<?php echo esc_attr($atts['binding_hash']); ?>"></label>
<label>Base model record hash <input data-f="baseModelRecordHash" value="<?php echo esc_attr($atts['model_hash']); ?>"></label>
<label>Training key <input data-f="trainingKey" value="training-run"></label>
<label>Title <input data-f="title" value="Training &amp; fine-tuning run"></label>
<label>Fine-tuning method <select data-f="method"><option>supervised-finetuning</option><option>full-finetune</option><option>lora</option><option>qlora</option><option>adapter</option><option>prompt-tuning</option><option>linear-probe</option><option>continued-pretraining</option><option>custom</option></select></label>
<label>Output model key <input data-f="outputModelKey" value="trained-model"></label>
<label>Output version <input data-f="outputVersionLabel" value="1.0"></label>
<label>Seed <input type="number" data-f="seed" value="42"></label>
<label>Epochs <input type="number" data-f="epochs" value="1"></label>
<label>Batch size <input type="number" data-f="batchSize" value="1"></label>
<label>Learning rate <input type="number" step="0.000001" data-f="learningRate" value="0.0001"></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button> <button data-action="save" type="button">Save run</button> <button data-action="list" type="button">List runs</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1020')); ?>;const api=async(path,method='GET',body=null)=>{const opt={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)opt.body=JSON.stringify(body);const r=await fetch(base+path,opt);return await r.json();};const body=()=>{const method=q('[data-f="method"]').value,pe=['lora','qlora','adapter','prompt-tuning','linear-probe'].includes(method);return {projectKey:q('[data-f="projectKey"]').value.trim(),trainingKey:q('[data-f="trainingKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),experimentHash:q('[data-f="experimentHash"]').value.trim(),registryBindingHash:q('[data-f="registryBindingHash"]').value.trim(),baseModelRecordHash:q('[data-f="baseModelRecordHash"]').value.trim(),fineTuning:{method,trainableParameterPolicy:pe?'adapters-only':'all',quantizationBits:method==='qlora'?4:null},hyperparameters:{seed:Number(q('[data-f="seed"]').value),epochs:Number(q('[data-f="epochs"]').value),batchSize:Number(q('[data-f="batchSize"]').value),learningRate:Number(q('[data-f="learningRate"]').value)},evaluation:{enabled:false},outputModelKey:q('[data-f="outputModelKey"]').value.trim(),outputVersionLabel:q('[data-f="outputVersionLabel"]').value.trim(),notes:q('[data-f="notes"]').value};};async function run(action){q('[data-role="status"]').textContent='Working…';try{let out;if(action==='list'){out=await api('/runs/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(action==='compose'?'/compose':'/runs','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_training','scwb_v1020_training_shortcode');
add_action('rest_api_init',function(){ $perm=function(){return current_user_can('edit_posts');};
    foreach(array('compose','runs','execution-plan','events','results','derived-model-plan') as $route){
        register_rest_route('sc-workbench/v1/v1020','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1020_backend_request('/ai-training/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1020','/runs/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1020_backend_request('/ai-training/runs/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
