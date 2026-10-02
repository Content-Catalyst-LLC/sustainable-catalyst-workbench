<?php
/** Workbench v10.6.0 — Explainability Workspace. */
if (!defined('ABSPATH')) { exit; }

function scwb_v1060_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);}
    $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($r); $d=json_decode(wp_remote_retrieve_body($r),true);
    if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}
    $d['_httpStatus']=$code; return $d;
}

function scwb_v1060_status_shortcode(){
    $r=scwb_v1060_backend_request('/v1060/status');
    if(!empty($r['ok'])){return '<div class="scwb-v1060-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Explainability Workspace ready</div>';}
    return '<div class="scwb-v1060-status">Explainability Workspace unavailable</div>';
}
add_shortcode('sc_workbench_ai_explainability_status','scwb_v1060_status_shortcode');

function scwb_v1060_workspace_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>'','model_hash'=>'','dataset_hash'=>''),$atts,'sc_workbench_ai_explainability');
    $uid='scwb-v1060-'.wp_generate_uuid4(); ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1060" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v1060{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v1060 label{display:block;margin:8px 0}.scwb-v1060 input,.scwb-v1060 textarea,.scwb-v1060 select{width:100%;max-width:900px}.scwb-v1060 button{padding:9px 14px;margin:4px}.scwb-v1060 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}.scwb-v1060 .boundary{border-left:4px solid #b00020;padding-left:10px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.6.0</small><h3>Explainability Workspace</h3><div>Define reproducible explanation contracts without silently executing explainers or treating attribution as causation.</div></header>
<p class="boundary"><strong>Interpretation boundary:</strong> explanations describe model behavior. They do not establish causal effects.</p>
<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Explanation key <input data-f="explanationKey" value="permutation-importance"></label>
<label>Title <input data-f="title" value="Global permutation importance"></label>
<label>Model record hash <input data-f="modelRecordHash" value="<?php echo esc_attr($atts['model_hash']); ?>"></label>
<label>Dataset record hash <input data-f="datasetRecordHash" value="<?php echo esc_attr($atts['dataset_hash']); ?>"></label>
<label>Explainer <select data-f="explainerKind"><option>permutation-importance</option><option>shap-compatible</option><option>partial-dependence</option><option>ice</option><option>coefficient</option><option>tree-native</option><option>gradient-attribution</option><option>counterfactual-contract</option></select></label>
<label>Scope <select data-f="scope"><option>global</option><option>local</option><option>cohort</option></select></label>
<label>Target output key <input data-f="outputKey" value="y"></label>
<label>Feature keys JSON <textarea data-f="featureKeys" rows="3">["x1","x2"]</textarea></label>
<label>Notes <textarea data-f="notes" rows="3"></textarea></label>
<div><button data-action="compose" type="button">Compose</button><button data-action="save" type="button">Save explanation</button><button data-action="list" type="button">List explanations</button></div>
<p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1060')); ?>;const api=async(path,method='GET',body=null)=>{const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body!==null)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();};const body=()=>({projectKey:q('[data-f="projectKey"]').value.trim(),explanationKey:q('[data-f="explanationKey"]').value.trim(),title:q('[data-f="title"]').value.trim(),modelRecordHash:q('[data-f="modelRecordHash"]').value.trim(),datasetRecordHash:q('[data-f="datasetRecordHash"]').value.trim(),explainerKind:q('[data-f="explainerKind"]').value,scope:q('[data-f="scope"]').value,target:{outputKey:q('[data-f="outputKey"]').value.trim(),outputKind:"scalar"},parameters:{featureKeys:JSON.parse(q('[data-f="featureKeys"]').value||'[]')},notes:q('[data-f="notes"]').value});async function run(a){q('[data-role="status"]').textContent='Working…';try{let out;if(a==='list'){out=await api('/explanations/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));}else{out=await api(a==='compose'?'/explanations/compose':'/explanations','POST',body());}q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}}root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_ai_explainability','scwb_v1060_workspace_shortcode');

add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    foreach(array('explanations/compose','explanations','results','compare','diagnose','core-plan') as $route){
        register_rest_route('sc-workbench/v1/v1060','/'.$route,array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r)use($route){$x=scwb_v1060_backend_request('/ai-explainability/'.$route,'POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    }
    register_rest_route('sc-workbench/v1/v1060','/explanations/(?P<project>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1060_backend_request('/ai-explainability/explanations/'.rawurlencode($r['project']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v1060','/results/(?P<project>[^/]+)/(?P<explanation>[^/]+)',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v1060_backend_request('/ai-explainability/results/'.rawurlencode($r['project']).'/'.rawurlencode($r['explanation']));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
