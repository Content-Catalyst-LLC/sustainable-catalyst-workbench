<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v950_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>60,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v950_status_shortcode(){
    $x=scwb_v950_backend_request('/v950/status');
    if(!empty($x['ok'])){return '<div class="scwb-v950-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Model Calibration ready</div>';}
    return '<div class="scwb-v950-status">Model Calibration Workspace unavailable</div>';
}
add_shortcode('sc_workbench_model_calibration_status','scwb_v950_status_shortcode');
function scwb_v950_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','campaign_hash'=>''),$atts);$id='scwb-v950-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v950" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Model Calibration &amp; Parameter Estimation</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Campaign hash <input data-f="campaignHash" value="<?php echo esc_attr($a['campaign_hash']); ?>"></label>
<label>Calibration key <input data-f="calibrationKey" value="calibration-001"></label>
<label>Title <input data-f="title" value="Model calibration"></label>
<label>Estimator <select data-f="estimator"><option value="linear-response-surface">Linear response surface</option><option value="campaign-search">Campaign search</option></select></label>
<label>Loss <select data-f="loss"><option value="weighted-least-squares">Weighted least squares</option><option value="least-squares">Least squares</option><option value="huber">Huber</option></select></label>
<label>Parameters JSON<textarea data-f="parameters" rows="8">[{"path":"parameters.x","lower":0,"upper":1,"initial":0.5}]</textarea></label>
<label>Targets JSON<textarea data-f="targets" rows="8">[{"metricPath":"metrics.y","observedValue":0,"weight":1}]</textarea></label>
<div><button type="button" data-action="compose">Compose</button> <button type="button" data-action="estimate">Estimate</button> <button type="button" data-action="save">Save calibration</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const body=()=>({projectKey:q('projectKey').value.trim(),campaignHash:q('campaignHash').value.trim(),calibrationKey:q('calibrationKey').value.trim(),title:q('title').value.trim(),estimator:q('estimator').value,loss:q('loss').value,parameters:JSON.parse(q('parameters').value||'[]'),targets:JSON.parse(q('targets').value||'[]')});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v950')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save'){p.createdBy='wordpress';}const path=a==='compose'?'/compose':a==='estimate'?'/estimate':'/calibrations';const out=await api(path,p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="compose"]').onclick=()=>run('compose');r.querySelector('[data-action="estimate"]').onclick=()=>run('estimate');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_model_calibration','scwb_v950_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('/compose'=>'/model-calibration/compose','/estimate'=>'/model-calibration/estimate','/calibrations'=>'/model-calibration/calibrations') as $route=>$backend){
        register_rest_route('sc-workbench/v1/v950',$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r) use ($backend){$x=scwb_v950_backend_request($backend,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
});
