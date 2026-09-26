<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v990_backend_request($path,$method='GET',$body=null){
    $base=rtrim(get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $res=wp_remote_request($base.$path,$args);
    if(is_wp_error($res)){return array('ok'=>false,'error'=>$res->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($res);$data=json_decode(wp_remote_retrieve_body($res),true);
    if(!is_array($data)){$data=array('ok'=>false,'error'=>'Invalid backend response');}$data['_httpStatus']=$code;return $data;
}
function scwb_v990_status_shortcode(){
    $x=scwb_v990_backend_request('/v990/status');
    if(!empty($x['ok'])){return '<div class="scwb-v990-status"><strong>Workbench v'.esc_html($x['version']).'</strong> · Research Package Exchange &amp; Portability ready</div>';}
    return '<div class="scwb-v990-status">Research Package Exchange &amp; Portability unavailable</div>';
}
add_shortcode('sc_workbench_research_package_exchange_status','scwb_v990_status_shortcode');
function scwb_v990_workspace_shortcode($atts){
    $a=shortcode_atts(array('project'=>''),$atts);$id='scwb-v990-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($id); ?>" class="scwb-v990" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<h3>Research Package Exchange &amp; Portability</h3>
<label>Project <input data-f="projectKey" value="<?php echo esc_attr($a['project']); ?>"></label>
<label>Package key <input data-f="packageKey" value="research-package-001"></label>
<label>Title <input data-f="title" value="Portable research package"></label>
<label>Description<textarea data-f="description" rows="3"></textarea></label>
<label>Object selections JSON<textarea data-f="selections" rows="12">[]</textarea></label>
<label><input data-f="includeProjectWorkspace" type="checkbox" checked> Include project workspace</label>
<label><input data-f="strictDependencyClosure" type="checkbox"> Require closed dependency inventory</label>
<label>License <input data-f="license"></label>
<div><button type="button" data-action="build">Build portable package</button></div>
<p data-role="status">Ready</p><pre data-role="output"></pre>
<script>(function(){const r=document.getElementById(<?php echo wp_json_encode($id); ?>),q=n=>r.querySelector('[data-f="'+n+'"]');const body=()=>({projectKey:q('projectKey').value.trim(),packageKey:q('packageKey').value.trim(),title:q('title').value.trim(),description:q('description').value,selections:JSON.parse(q('selections').value||'[]'),includeProjectWorkspace:q('includeProjectWorkspace').checked,strictDependencyClosure:q('strictDependencyClosure').checked,license:q('license').value,createdBy:'wordpress'});r.querySelector('[data-action="build"]').onclick=async()=>{try{r.querySelector('[data-role="status"]').textContent='Building…';const x=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v990/packages')); ?>,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':r.dataset.nonce},body:JSON.stringify(body())});const out=await x.json();r.querySelector('[data-role="output"]').textContent=JSON.stringify(out,null,2);r.querySelector('[data-role="status"]').textContent=out.ok?'Ready':'Error';}catch(e){r.querySelector('[data-role="status"]').textContent=e.message;}};})();</script>
</div><?php return ob_get_clean();}
add_shortcode('sc_workbench_research_package_exchange','scwb_v990_workspace_shortcode');
add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v990','/packages',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v990_backend_request('/research-package-exchange/packages','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v990','/import/validate',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v990_backend_request('/research-package-exchange/import/validate','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v990','/import/stage',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v990_backend_request('/research-package-exchange/import/stage','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
