<?php
/**
 * Workbench v10.10.0 — Hybrid Numerical Runtime & Standalone Application Foundation.
 *
 * WordPress is an optional adapter, not the canonical Workbench runtime.
 * Standalone backend contract: wordpressRequired = false.
 * WordPress is an optional adapter. Authoritative calculation happens in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10100_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);}
    $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($r);
    $d=json_decode(wp_remote_retrieve_body($r),true);
    if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}
    $d['_httpStatus']=$code; return $d;
}

function scwb_v10100_status_shortcode(){
    $r=scwb_v10100_backend_request('/v10100/status');
    if(!empty($r['ok'])){
        return '<div class="scwb-v10100-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Hybrid Numerical Runtime ready · Backend-first · WordPress optional</div>';
    }
    return '<div class="scwb-v10100-status">Hybrid Numerical Runtime unavailable</div>';
}
add_shortcode('sc_workbench_hybrid_numerical_status','scwb_v10100_status_shortcode');

function scwb_v10100_calculator_shortcode(){
    $uid='scwb-v10100-'.wp_generate_uuid4(); ob_start(); ?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v10100" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v10100{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v10100 input,.scwb-v10100 select{width:100%;max-width:900px;margin:5px 0 12px}.scwb-v10100 button{padding:9px 14px}.scwb-v10100 pre{max-height:520px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}</style>
<header><small>SUSTAINABLE CATALYST WORKBENCH · V10.10.0</small><h3>Hybrid Numerical Runtime</h3><p>Backend-first calculator adapter. WordPress does not execute authoritative mathematics.</p></header>
<label>Operation <select data-f="operation"><option>exact</option><option>evaluate</option><option>simplify</option><option>solve</option><option>differentiate</option><option>integrate-symbolic</option><option>root</option><option>integrate-numeric</option><option>optimize-scalar</option></select></label>
<label>Expression <input data-f="expression" value="x**2 - 2"></label>
<label>Variable <input data-f="variable" value="x"></label>
<button type="button" data-action="calculate">Calculate</button><p data-role="status">Ready</p><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s),base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v10100')); ?>;async function api(path,method='GET',body=null){const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};if(body)o.body=JSON.stringify(body);const r=await fetch(base+path,o);return await r.json();}q('[data-action="calculate"]').onclick=async()=>{q('[data-role="status"]').textContent='Calculating…';try{const body={operation:q('[data-f="operation"]').value,expression:q('[data-f="expression"]').value,variable:q('[data-f="variable"]').value};const out=await api('/compute','POST',body);q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';}catch(e){q('[data-role="status"]').textContent=e.message;}};})();</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_hybrid_numerical','scwb_v10100_calculator_shortcode');

add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v10100','/status',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function(){ $x=scwb_v10100_backend_request('/v10100/status'); $st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v10100','/capabilities',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function(){ $x=scwb_v10100_backend_request('/numerical/capabilities'); $st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v10100','/compute',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v10100_backend_request('/numerical/compute','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v10100','/plan',array('methods'=>'POST','permission_callback'=>$perm,'callback'=>function($r){$x=scwb_v10100_backend_request('/numerical/plan','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v10100','/standalone-bootstrap',array('methods'=>'GET','permission_callback'=>$perm,'callback'=>function(){ $x=scwb_v10100_backend_request('/standalone/bootstrap'); $st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
