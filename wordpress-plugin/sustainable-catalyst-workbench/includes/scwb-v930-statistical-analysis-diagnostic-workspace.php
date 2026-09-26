<?php
if (!defined('ABSPATH')) { exit; }
function scwb_v930_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>45,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v930_status_shortcode(){
    $x=scwb_v930_backend_request('/v930/status');
    if(!empty($x['ok'])){return '<div class="scwb-v930-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Statistical Analysis &amp; Diagnostics ready</div>';}
    return '<div class="scwb-v930-status">Statistical Analysis Workspace unavailable</div>';
}
add_shortcode('sc_workbench_statistical_analysis_status','scwb_v930_status_shortcode');
function scwb_v930_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','campaign_hash'=>''),$atts);
    $id='scwb-v930-'.wp_generate_uuid4(); ob_start(); ?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v930" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Statistical Analysis &amp; Diagnostic Workspace</h3>
<div class="scwb-v930-grid">
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Campaign hash <input data-f="campaignHash" value="<?php echo esc_attr($a['campaign_hash']); ?>"></label>
<label>Analysis key <input data-f="analysisKey" value="analysis-001"></label>
<label>Title <input data-f="title" value="Statistical analysis"></label>
<label>Result metric path <input data-f="resultMetricPath" value="metrics.y"></label>
<label>Group parameter path <input data-f="groupParameterPath" placeholder="parameters.group"></label>
<label>Predictor parameter path <input data-f="predictorParameterPath" placeholder="parameters.x"></label>
<label>Confidence level <input data-f="confidenceLevel" type="number" min="0.51" max="0.999" step="0.01" value="0.95"></label>
</div>
<label>Job IDs JSON<textarea data-f="jobIds" rows="3">[]</textarea></label>
<label>Methods JSON<textarea data-f="methods" rows="5">["descriptive","distribution-diagnostics"]</textarea></label>
<label>Researcher interpretation<textarea data-f="researcherInterpretation" rows="4"></textarea></label>
<div><button type="button" data-action="analyze">Analyze</button> <button type="button" data-action="save">Save analysis</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const parse=(n,f)=>{try{return JSON.parse(q(n).value||f);}catch(e){throw new Error(n+' must be valid JSON');}};const body=()=>({projectKey:q('projectKey').value.trim(),campaignHash:q('campaignHash').value.trim(),analysisKey:q('analysisKey').value.trim(),title:q('title').value.trim(),jobIds:parse('jobIds','[]'),resultMetricPath:q('resultMetricPath').value.trim(),groupParameterPath:q('groupParameterPath').value.trim(),predictorParameterPath:q('predictorParameterPath').value.trim(),methods:parse('methods','["descriptive"]'),confidenceLevel:Number(q('confidenceLevel').value||0.95),researcherInterpretation:q('researcherInterpretation').value});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v930')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save'){p.createdBy='wordpress';p.recordLabel='Statistical analysis';}const out=await api(a==='save'?'/analyses':'/analyze',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="analyze"]').onclick=()=>run('analyze');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_statistical_analysis_workspace','scwb_v930_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v930','/analyze',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v930_backend_request('/statistical-workspace/analyze','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v930','/analyses',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v930_backend_request('/statistical-workspace/analyses','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
