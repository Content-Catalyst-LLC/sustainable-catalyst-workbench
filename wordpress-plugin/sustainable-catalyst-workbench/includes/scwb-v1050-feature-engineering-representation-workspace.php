<?php
/** Workbench v10.5.0 — Feature Engineering & Representation Workspace. */
if (!defined('ABSPATH')) { exit; }

function scwb_v1050_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}

function scwb_v1050_status_shortcode(){
    $r=scwb_v1050_backend_request('/v1050/status');
    if(!empty($r['ok'])){return '<div class="scwb-v1050-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Feature Engineering &amp; Representation Workspace ready</div>';}
    return '<div class="scwb-v1050-status">Feature Engineering &amp; Representation Workspace unavailable</div>';
}
add_shortcode('sc_workbench_ai_features_status','scwb_v1050_status_shortcode');

function scwb_v1050_workspace_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>'','dataset_hash'=>''),$atts,'sc_workbench_ai_features');
    $uid='scwb-v1050-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1050" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1050{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1050 label{display:block;margin:8px 0}.scwb-v1050 input,.scwb-v1050 textarea,.scwb-v1050 select{width:100%;max-width:900px}.scwb-v1050 button{padding:9px 14px;margin:4px}.scwb-v1050 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.5.0</small><h3>Feature Engineering &amp; Representation Workspace</h3><div>Define reproducible feature representations, split-aware transformations, and lineage without silently fitting or materializing data.</div></header>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Representation key <input data-f="representationKey" value="baseline"></label>
<label>Title <input data-f="title" value="Baseline feature representation"></label>
<label>Dataset record hash <input data-f="datasetHash" value="<?php echo esc_attr($atts['dataset_hash']); ?>"></label>
<label>Fields JSON <textarea data-f="fields" rows="9">[{"fieldKey":"x","sourcePath":"x","kind":"numeric","role":"feature"},{"fieldKey":"y","sourcePath":"y","kind":"numeric","role":"target"}]</textarea></label>
<label>Transforms JSON <textarea data-f="transforms" rows="9">[{"stepKey":"x-impute","kind":"impute-median","inputs":["x"],"outputKey":"x_i","fitScope":"train-only"},{"stepKey":"x-scale","kind":"standardize","inputs":["x_i"],"outputKey":"x_z","fitScope":"train-only"}]</textarea></label>
<label>Output keys JSON <textarea data-f="outputs" rows="3">["x_z"]</textarea></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button><button data-action="save" type="button">Save representation</button><button data-action="list" type="button">List representations</button></div><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1050')); ?>;const api=async(path,method='GET',body=null)=>{const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();};const body=()=>({projectKey:q('[data-f="projectKey"]').value.trim(),representationKey:q('[data-f="representationKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),datasetRecordHash:q('[data-f="datasetHash"]').value.trim(),fields:JSON.parse(q('[data-f="fields"]').value||'[]'),transforms:JSON.parse(q('[data-f="transforms"]').value||'[]'),outputKeys:JSON.parse(q('[data-f="outputs"]').value||'[]'),notes:q('[data-f="notes"]').value});async function run(a){q('[data-role="status"]').textContent='Working…';try{let out;if(a==='list'){out=await api('/representations/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(a==='compose'?'/representations/compose':'/representations','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_features','scwb_v1050_workspace_shortcode');

add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('representations/compose','representations','materialization-plan','fit-state/record','diagnose','core-plan') as $route){
        register_rest_route('sc-workbench/v1/v1050','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1050_backend_request('/ai-features/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1050','/representations/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1050_backend_request('/ai-features/representations/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
