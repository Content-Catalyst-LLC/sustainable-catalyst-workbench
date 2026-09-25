<?php
if (!defined('ABSPATH')) { exit; }
function scwb_v920_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>30,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v920_status_shortcode(){
    $x=scwb_v920_backend_request('/v920/status');
    if(!empty($x['ok'])){return '<div class="scwb-v920-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Batch Campaign Manager ready</div>';}
    return '<div class="scwb-v920-status">Campaign Manager unavailable</div>';
}
add_shortcode('sc_workbench_batch_campaign_manager_status','scwb_v920_status_shortcode');
function scwb_v920_campaign_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','protocol_hash'=>''),$atts);
    $id='scwb-v920-'.wp_generate_uuid4(); ob_start(); ?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v920" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Batch Experiment &amp; Computational Campaign Manager</h3>
<div class="scwb-v920-grid">
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Protocol hash <input data-f="protocolHash" value="<?php echo esc_attr($a['protocol_hash']); ?>"></label>
<label>Campaign key <input data-f="campaignKey" value="campaign-001"></label>
<label>Title <input data-f="title" value="Computational campaign"></label>
<label>Runtime <select data-f="runtimeKind"><option>unified</option><option>solver</option><option>simulation</option><option>engineering</option><option>design-space</option><option>workflow</option><option>notebook</option></select></label>
<label>Replications <input data-f="replications" type="number" min="1" value="1"></label>
</div>
<label>Request template JSON<textarea data-f="requestTemplate" rows="8">{}</textarea></label>
<label>Parameter axes JSON<textarea data-f="parameterAxes" rows="8">[]</textarea></label>
<div><button type="button" data-action="compose">Compose campaign</button> <button type="button" data-action="save">Save campaign</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const parse=(n,f)=>{try{return JSON.parse(q(n).value||f);}catch(e){throw new Error(n+' must be valid JSON');}};const body=()=>({projectKey:q('projectKey').value.trim(),protocolHash:q('protocolHash').value.trim(),campaignKey:q('campaignKey').value.trim(),title:q('title').value.trim(),runtimeKind:q('runtimeKind').value,replications:Number(q('replications').value||1),requestTemplate:parse('requestTemplate','{}'),parameterAxes:parse('parameterAxes','[]'),budget:{maxRuns:1000,maxPreparedJobs:1000}});const api=async(path,p)=>{const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v920')); ?>+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(p)});return await x.json();};const run=async(a)=>{try{r.querySelector('[data-role="status"]').textContent='Working…';const p=body();if(a==='save'){p.createdBy='wordpress';p.recordLabel='Computational campaign';}const out=await api(a==='save'?'/campaigns':'/compose',p);r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};r.querySelector('[data-action="compose"]').onclick=()=>run('compose');r.querySelector('[data-action="save"]').onclick=()=>run('save');})();</script>
</div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_batch_campaign_manager','scwb_v920_campaign_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v920','/compose',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v920_backend_request('/campaign-manager/compose','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v920','/campaigns',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v920_backend_request('/campaign-manager/campaigns','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
