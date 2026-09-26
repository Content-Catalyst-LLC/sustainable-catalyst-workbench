<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v970_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>60,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v970_status_shortcode(){
    $x=scwb_v970_backend_request('/v970/status');
    if(!empty($x['ok'])){return '<div class="scwb-v970-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Reproduction &amp; Replication Workflow ready</div>';}
    return '<div class="scwb-v970-status">Reproduction &amp; Replication Workflow unavailable</div>';
}
add_shortcode('sc_workbench_reproduction_replication_status','scwb_v970_status_shortcode');
function scwb_v970_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','synthesis_hash'=>''),$atts);$id='scwb-v970-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v970" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Reproduction &amp; Replication Workflow</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Workflow key <input data-f="workflowKey" value="reproduction-001"></label>
<label>Title <input data-f="title" value="Reproduction workflow"></label>
<label>Mode <select data-f="mode"><option value="reproduction">Reproduction</option><option value="replication">Replication</option></select></label>
<label>Target synthesis hash <input data-f="targetSynthesisHash" value="<?php echo esc_attr($a['synthesis_hash']); ?>"></label>
<label>Research question<textarea data-f="researchQuestion" rows="3"></textarea></label>
<label>Environment JSON<textarea data-f="environment" rows="5">{}</textarea></label>
<label>Inputs JSON<textarea data-f="inputs" rows="5">[]</textarea></label>
<label>Comparison criteria JSON<textarea data-f="comparisonCriteria" rows="7">[]</textarea></label>
<label>Planned changes JSON<textarea data-f="plannedChanges" rows="4">[]</textarea></label>
<label>Invariants JSON<textarea data-f="invariants" rows="4">[]</textarea></label>
<label>Protocol notes<textarea data-f="protocolNotes" rows="4"></textarea></label>
<div><button type="button" data-action="compose">Compose</button> <button type="button" data-action="save">Save workflow</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const j=n=>JSON.parse(q(n).value||'[]');const body=()=>({projectKey:q('projectKey').value.trim(),workflowKey:q('workflowKey').value.trim(),title:q('title').value.trim(),mode:q('mode').value,targetSynthesisHash:q('targetSynthesisHash').value.trim(),researchQuestion:q('researchQuestion').value,protocolNotes:q('protocolNotes').value,environment:JSON.parse(q('environment').value||'{}'),inputs:j('inputs'),comparisonCriteria:j('comparisonCriteria'),plannedChanges:j('plannedChanges'),invariants:j('invariants')});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v970')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save')p.createdBy='wordpress';const out=await api(a==='compose'?'/compose':'/workflows',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="compose"]').onclick=()=>run('compose');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_reproduction_replication','scwb_v970_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('/compose'=>'/reproduction-replication/compose','/workflows'=>'/reproduction-replication/workflows','/execution-plan'=>'/reproduction-replication/execution-plan','/compare'=>'/reproduction-replication/compare') as $route=>$backend){
        register_rest_route('sc-workbench/v1/v970',$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r) use ($backend){$x=scwb_v970_backend_request($backend,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
});
