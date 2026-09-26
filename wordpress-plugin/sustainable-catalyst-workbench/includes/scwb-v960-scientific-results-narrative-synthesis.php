<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v960_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>60,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v960_status_shortcode(){
    $x=scwb_v960_backend_request('/v960/status');
    if(!empty($x['ok'])){return '<div class="scwb-v960-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Scientific Results &amp; Narrative Synthesis ready</div>';}
    return '<div class="scwb-v960-status">Scientific Results &amp; Narrative Synthesis unavailable</div>';
}
add_shortcode('sc_workbench_scientific_results_synthesis_status','scwb_v960_status_shortcode');
function scwb_v960_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>''),$atts);$id='scwb-v960-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v960" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Scientific Results &amp; Narrative Synthesis</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Synthesis key <input data-f="synthesisKey" value="synthesis-001"></label>
<label>Title <input data-f="title" value="Scientific results synthesis"></label>
<label>Statistical analysis hashes JSON<textarea data-f="statisticalAnalysisHashes" rows="3">[]</textarea></label>
<label>Uncertainty study hashes JSON<textarea data-f="uncertaintyStudyHashes" rows="3">[]</textarea></label>
<label>Calibration hashes JSON<textarea data-f="calibrationHashes" rows="3">[]</textarea></label>
<label>Analysis snapshot hashes JSON<textarea data-f="analysisSnapshotHashes" rows="3">[]</textarea></label>
<label>Publication package hashes JSON<textarea data-f="publicationPackageHashes" rows="3">[]</textarea></label>
<label>Narrative statements JSON<textarea data-f="statements" rows="9">[]</textarea></label>
<label>Abstract<textarea data-f="abstract" rows="4"></textarea></label>
<label>Methods narrative<textarea data-f="methodsNarrative" rows="5"></textarea></label>
<label>Results narrative<textarea data-f="resultsNarrative" rows="7"></textarea></label>
<label>Interpretation<textarea data-f="interpretation" rows="5"></textarea></label>
<label>Limitations JSON<textarea data-f="limitations" rows="4">[]</textarea></label>
<label>Conclusion<textarea data-f="conclusion" rows="4"></textarea></label>
<div><button type="button" data-action="compose">Compose</button> <button type="button" data-action="save">Save synthesis</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const j=n=>JSON.parse(q(n).value||'[]');const body=()=>({projectKey:q('projectKey').value.trim(),synthesisKey:q('synthesisKey').value.trim(),title:q('title').value.trim(),statisticalAnalysisHashes:j('statisticalAnalysisHashes'),uncertaintyStudyHashes:j('uncertaintyStudyHashes'),calibrationHashes:j('calibrationHashes'),analysisSnapshotHashes:j('analysisSnapshotHashes'),publicationPackageHashes:j('publicationPackageHashes'),statements:j('statements'),abstract:q('abstract').value,methodsNarrative:q('methodsNarrative').value,resultsNarrative:q('resultsNarrative').value,interpretation:q('interpretation').value,limitations:j('limitations'),conclusion:q('conclusion').value});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v960')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save'){p.createdBy='wordpress';}const out=await api(a==='compose'?'/compose':'/syntheses',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="compose"]').onclick=()=>run('compose');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_scientific_results_synthesis','scwb_v960_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('/compose'=>'/results-synthesis/compose','/syntheses'=>'/results-synthesis/syntheses') as $route=>$backend){
        register_rest_route('sc-workbench/v1/v960',$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r) use ($backend){$x=scwb_v960_backend_request($backend,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
});
