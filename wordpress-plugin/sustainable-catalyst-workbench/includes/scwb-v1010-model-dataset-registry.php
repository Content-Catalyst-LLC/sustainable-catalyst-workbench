<?php
/** Workbench v10.1.0 — Model & Dataset Registry. */
if (!defined('ABSPATH')) { exit; }
function scwb_v1010_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v1010_registry_status_shortcode(){ $r=scwb_v1010_backend_request('/v1010/status'); if(!empty($r['ok'])){return '<div class="scwb-v1010-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Model & Dataset Registry ready</div>';} return '<div class="scwb-v1010-status">Model & Dataset Registry unavailable</div>'; }
add_shortcode('sc_workbench_model_dataset_registry_status','scwb_v1010_registry_status_shortcode');
function scwb_v1010_registry_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>''),$atts,'sc_workbench_model_dataset_registry'); $uid='scwb-v1010-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1010" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1010{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1010 header{margin-bottom:12px}.scwb-v1010 label{display:block;margin:8px 0}.scwb-v1010 input,.scwb-v1010 select,.scwb-v1010 textarea{width:100%;max-width:760px}.scwb-v1010 button{padding:9px 14px;margin:4px}.scwb-v1010 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.1.0</small><h3>Model & Dataset Registry</h3><div>Create immutable, content-addressed AI model and dataset versions with provenance, licensing and compatibility metadata.</div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Record type <select data-f="kind"><option value="model">Model</option><option value="dataset">Dataset</option></select></label>
<label>Key <input data-f="key" value="registry-item"></label>
<label>Version label <input data-f="versionLabel" value="1.0"></label>
<label>Title <input data-f="title" value="Registry item"></label>
<label>SHA-256 hash <input data-f="hash" placeholder="64-character SHA-256"></label>
<label>Reference / Model ID <input data-f="ref" value="sc://registry/item"></label>
<label>License <input data-f="license"></label>
<label>Tags (comma-separated) <input data-f="tags"></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="save" type="button">Save immutable version</button> <button data-action="list" type="button">List registry</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s);const api=async(path,method='GET',body=null)=>{const opt={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)opt.body=JSON.stringify(body);const r=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1010')); ?>+path,opt);return await r.json();};const body=()=>{const kind=q('[data-f="kind"]').value,base={projectKey:q('[data-f="projectKey"]').value.trim(),versionLabel:q('[data-f="versionLabel"]').value.trim(),title:q('[data-f="title"]').value.trim(),license:q('[data-f="license"]').value.trim(),tags:q('[data-f="tags"]').value.split(',').map(x=>x.trim()).filter(Boolean),notes:q('[data-f="notes"]').value};if(kind==='model')return {...base,modelKey:q('[data-f="key"]').value.trim(),provider:'local',modelId:q('[data-f="ref"]').value.trim(),task:'custom',artifactHash:q('[data-f="hash"]').value.trim(),sourceUri:q('[data-f="ref"]').value.trim()};return {...base,datasetKey:q('[data-f="key"]').value.trim(),datasetHash:q('[data-f="hash"]').value.trim(),datasetRef:q('[data-f="ref"]').value.trim(),format:'custom'};};async function run(){q('[data-role="status"]').textContent='Working…';try{const kind=q('[data-f="kind"]').value,out=await api('/'+(kind==='model'?'models':'datasets'),'POST',body());q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}async function list(){q('[data-role="status"]').textContent='Working…';try{const kind=q('[data-f="kind"]').value,p=encodeURIComponent(q('[data-f="projectKey"]').value.trim()),out=await api('/'+(kind==='model'?'models':'datasets')+'/'+p);q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}q('[data-action="save"]').onclick=run;q('[data-action="list"]').onclick=list;})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_model_dataset_registry','scwb_v1010_registry_shortcode');
add_action('rest_api_init',function(){ $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1010','/models',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1010_backend_request('/ai-registry/models','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1010','/datasets',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1010_backend_request('/ai-registry/datasets','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1010','/models/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1010_backend_request('/ai-registry/models/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1010','/datasets/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1010_backend_request('/ai-registry/datasets/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
