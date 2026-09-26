<?php
if (!defined('ABSPATH')) { exit; }
function scwb_v940_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>60,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v940_status_shortcode(){
    $x=scwb_v940_backend_request('/v940/status');
    if(!empty($x['ok'])){return '<div class="scwb-v940-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Uncertainty &amp; Sensitivity ready</div>';}
    return '<div class="scwb-v940-status">Uncertainty &amp; Sensitivity Workspace unavailable</div>';
}
add_shortcode('sc_workbench_uncertainty_sensitivity_status','scwb_v940_status_shortcode');
function scwb_v940_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','campaign_hash'=>''),$atts);$id='scwb-v940-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v940" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Uncertainty &amp; Sensitivity Study Composer</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Campaign hash <input data-f="campaignHash" value="<?php echo esc_attr($a['campaign_hash']); ?>"></label>
<label>Study key <input data-f="studyKey" value="uncertainty-001"></label>
<label>Title <input data-f="title" value="Uncertainty & sensitivity study"></label>
<label>Sampling method <select data-f="samplingMethod"><option value="monte-carlo">Monte Carlo</option><option value="latin-hypercube">Latin hypercube</option><option value="sobol">Sobol</option></select></label>
<label>Sample count <input data-f="sampleCount" type="number" value="1000" min="2" max="10000"></label>
<label>Seed <input data-f="seed" type="number" value="20260925"></label>
<label>Uncertain inputs JSON<textarea data-f="uncertainInputs" rows="9">[{"path":"parameters.x","distribution":"uniform","minimum":0,"maximum":1}]</textarea></label>
<div><button type="button" data-action="compose">Compose</button> <button type="button" data-action="save">Save study</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const body=()=>({projectKey:q('projectKey').value.trim(),campaignHash:q('campaignHash').value.trim(),studyKey:q('studyKey').value.trim(),title:q('title').value.trim(),samplingMethod:q('samplingMethod').value,sampleCount:Number(q('sampleCount').value||1000),seed:Number(q('seed').value||0),uncertainInputs:JSON.parse(q('uncertainInputs').value||'[]')});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v940')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save'){p.createdBy='wordpress';}const out=await api(a==='save'?'/studies':'/compose',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="compose"]').onclick=()=>run('compose');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_uncertainty_sensitivity_study','scwb_v940_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v940','/compose',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v940_backend_request('/uncertainty-sensitivity/compose','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v940','/studies',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v940_backend_request('/uncertainty-sensitivity/studies','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
