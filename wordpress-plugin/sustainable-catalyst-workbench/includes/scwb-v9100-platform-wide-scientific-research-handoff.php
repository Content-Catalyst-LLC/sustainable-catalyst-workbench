<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v9100_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v9100_status_shortcode(){
    $x=scwb_v9100_backend_request('/v9100/status');
    if(!empty($x['ok'])){return '<div class="scwb-v9100-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Platform-Wide Scientific Research Handoff ready</div>';}
    return '<div class="scwb-v9100-status">Platform-Wide Scientific Research Handoff unavailable</div>';
}
add_shortcode('sc_workbench_scientific_research_handoff_status','scwb_v9100_status_shortcode');
function scwb_v9100_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>'','package_hash'=>''),$atts);$id='scwb-v9100-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v9100" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Platform-Wide Scientific Research Handoff</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Handoff key <input data-f="handoffKey" value="research-handoff-001"></label>
<label>Title <input data-f="title" value="Scientific research handoff"></label>
<label>Portable package hash <input data-f="portablePackageHash" value="<?php echo esc_attr($a['package_hash']); ?>"></label>
<label>Destinations JSON<textarea data-f="destinations" rows="4">["platform-core","knowledge-library","research-lab","archive"]</textarea></label>
<label>Description<textarea data-f="description" rows="3"></textarea></label>
<label><input data-f="requireAllDestinationsReady" type="checkbox"> Require every requested destination to be ready</label>
<div><button type="button" data-action="compose">Preview handoff</button> <button type="button" data-action="save">Save handoff</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const body=()=>({projectKey:q('projectKey').value.trim(),handoffKey:q('handoffKey').value.trim(),title:q('title').value.trim(),portablePackageHash:q('portablePackageHash').value.trim(),description:q('description').value,destinations:JSON.parse(q('destinations').value||'[]'),requireAllDestinationsReady:q('requireAllDestinationsReady').checked,createdBy:'wordpress'});async function send(path){try{r.querySelector('[data-role="status"]').textContent='Working…';const x=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(body())});const out=await x.json();r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}}r.querySelector('[data-action="compose"]').onclick=()=>send(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v9100/compose')); ?>);r.querySelector('[data-action="save"]').onclick=()=>send(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v9100/handoffs')); ?>);})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_scientific_research_handoff','scwb_v9100_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v9100','/compose',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v9100_backend_request('/scientific-research-handoff/compose','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v9100','/handoffs',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v9100_backend_request('/scientific-research-handoff/handoffs','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
