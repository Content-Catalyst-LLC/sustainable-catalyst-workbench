<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v980_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>90,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v980_status_shortcode(){
    $x=scwb_v980_backend_request('/v980/status');
    if(!empty($x['ok'])){return '<div class="scwb-v980-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Cross-Study Comparison &amp; Meta-Analysis ready</div>';}
    return '<div class="scwb-v980-status">Cross-Study Comparison &amp; Meta-Analysis unavailable</div>';
}
add_shortcode('sc_workbench_cross_study_meta_analysis_status','scwb_v980_status_shortcode');
function scwb_v980_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>''),$atts);$id='scwb-v980-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v980" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Cross-Study Comparison &amp; Meta-Analysis</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Analysis key <input data-f="analysisKey" value="meta-analysis-001"></label>
<label>Title <input data-f="title" value="Cross-study meta-analysis"></label>
<label>Research question<textarea data-f="researchQuestion" rows="3"></textarea></label>
<label>Effect measure <select data-f="effectMeasure"><option value="generic">Generic effect</option><option value="mean-difference">Mean difference</option><option value="standardized-mean-difference">Standardized mean difference</option><option value="log-odds-ratio">Log odds ratio</option><option value="log-risk-ratio">Log risk ratio</option><option value="fisher-z-correlation">Fisher-z correlation</option></select></label>
<label>Studies JSON<textarea data-f="studies" rows="12">[]</textarea></label>
<label>Models JSON<textarea data-f="models" rows="3">["fixed-effect","random-effects"]</textarea></label>
<label>Confidence level <input data-f="confidenceLevel" type="number" min="0.51" max="0.999" step="0.01" value="0.95"></label>
<label><input data-f="subgroupAnalysis" type="checkbox" checked> Subgroup analysis</label>
<label><input data-f="leaveOneOut" type="checkbox" checked> Leave-one-out sensitivity</label>
<label>Researcher interpretation<textarea data-f="researcherInterpretation" rows="5"></textarea></label>
<label>Limitations JSON<textarea data-f="limitations" rows="4">[]</textarea></label>
<div><button type="button" data-action="analyze">Analyze</button> <button type="button" data-action="save">Save analysis</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const j=n=>JSON.parse(q(n).value||'[]');const body=()=>({projectKey:q('projectKey').value.trim(),analysisKey:q('analysisKey').value.trim(),title:q('title').value.trim(),researchQuestion:q('researchQuestion').value,effectMeasure:q('effectMeasure').value,studies:j('studies'),models:j('models'),confidenceLevel:Number(q('confidenceLevel').value||0.95),subgroupAnalysis:q('subgroupAnalysis').checked,leaveOneOut:q('leaveOneOut').checked,researcherInterpretation:q('researcherInterpretation').value,limitations:j('limitations')});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v980')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save')p.createdBy='wordpress';const out=await api(a==='analyze'?'/analyze':'/meta-analyses',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="analyze"]').onclick=()=>run('analyze');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_cross_study_meta_analysis','scwb_v980_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('/analyze'=>'/cross-study-meta/analyze','/meta-analyses'=>'/cross-study-meta/meta-analyses','/visualization-plan'=>'/cross-study-meta/visualization-plan') as $route=>$backend){
        register_rest_route('sc-workbench/v1/v980',$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r) use ($backend){$x=scwb_v980_backend_request($backend,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
});
