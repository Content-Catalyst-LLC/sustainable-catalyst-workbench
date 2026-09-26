<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v9110_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v9110_status_shortcode(){
    $x=scwb_v9110_backend_request('/v9110/status');
    if(!empty($x['ok'])){return '<div class="scwb-v9110-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · End-to-End Research Study Certification ready</div>';}
    return '<div class="scwb-v9110-status">Research Study Certification unavailable</div>';
}
add_shortcode('sc_workbench_research_study_certification_status','scwb_v9110_status_shortcode');

function scwb_v9110_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','study_hash'=>''),$atts);$id='scwb-v9110-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v9110" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>End-to-End Research Study Certification</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Certification key <input data-f="certificationKey" value="study-certification-001"></label>
<label>Title <input data-f="title" value="Research study certification"></label>
<label>Profile <select data-f="profile"><option value="study-foundation">Study foundation</option><option value="analysis-complete">Analysis complete</option><option value="reproducible-study" selected>Reproducible study</option><option value="portable-study">Portable study</option><option value="handoff-ready">Handoff ready</option><option value="full-v9">Full v9</option></select></label>
<label>Study hash <input data-f="studyHash" value="<?php echo esc_attr($a['study_hash']); ?>"></label>
<label>Protocol hash <input data-f="protocolHash"></label>
<label>Campaign hash <input data-f="campaignHash"></label>
<label>Statistical analysis hash <input data-f="statisticalAnalysisHash"></label>
<label>Uncertainty study hash <input data-f="uncertaintyStudyHash"></label>
<label>Calibration hash <input data-f="calibrationHash"></label>
<label>Results synthesis hash <input data-f="synthesisHash"></label>
<label>Reproduction/replication workflow hash <input data-f="reproductionWorkflowHash"></label>
<label>Cross-study meta-analysis hash <input data-f="metaAnalysisHash"></label>
<label>Portable package hash <input data-f="portablePackageHash"></label>
<label>Platform-wide handoff hash <input data-f="handoffHash"></label>
<label>Reviewer <input data-f="reviewer"></label>
<label>Notes<textarea data-f="notes" rows="3"></textarea></label>
<div><button type="button" data-action="evaluate">Evaluate certification</button> <button type="button" data-action="save">Save certification</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const body=()=>({projectKey:q('projectKey').value.trim(),certificationKey:q('certificationKey').value.trim(),title:q('title').value.trim(),profile:q('profile').value,studyHash:q('studyHash').value.trim(),protocolHash:q('protocolHash').value.trim(),campaignHash:q('campaignHash').value.trim(),statisticalAnalysisHash:q('statisticalAnalysisHash').value.trim(),uncertaintyStudyHash:q('uncertaintyStudyHash').value.trim(),calibrationHash:q('calibrationHash').value.trim(),synthesisHash:q('synthesisHash').value.trim(),reproductionWorkflowHash:q('reproductionWorkflowHash').value.trim(),metaAnalysisHash:q('metaAnalysisHash').value.trim(),portablePackageHash:q('portablePackageHash').value.trim(),handoffHash:q('handoffHash').value.trim(),reviewer:q('reviewer').value.trim(),notes:q('notes').value,createdBy:'wordpress'});async function send(path){try{r.querySelector('[data-role="status"]').textContent='Working…';const x=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(body())});const out=await x.json();r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}}r.querySelector('[data-action="evaluate"]').onclick=()=>send(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v9110/evaluate')); ?>);r.querySelector('[data-action="save"]').onclick=()=>send(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v9110/certifications')); ?>);})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_research_study_certification','scwb_v9110_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v9110','/evaluate',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v9110_backend_request('/research-study-certification/evaluate','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v9110','/certifications',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v9110_backend_request('/research-study-certification/certifications','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
