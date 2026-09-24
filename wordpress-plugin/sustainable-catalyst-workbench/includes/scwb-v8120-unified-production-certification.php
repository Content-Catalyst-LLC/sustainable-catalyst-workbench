<?php
/** Workbench v8.12.0 — Unified Workbench Production Certification. */
if (!defined('ABSPATH')) { exit; }
function scwb_v8120_backend_request($path,$method='GET',$body=null){
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>30,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);} $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);} $code=wp_remote_retrieve_response_code($r);$d=json_decode(wp_remote_retrieve_body($r),true);if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}$d['_httpStatus']=$code;return $d;
}
function scwb_v8120_status_shortcode(){ $r=scwb_v8120_backend_request('/v8120/status'); return '<pre class="scwb-v8120-status">'.esc_html(wp_json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)).'</pre>'; }
add_shortcode('sc_workbench_production_certification_status','scwb_v8120_status_shortcode');
function scwb_v8120_certification_shortcode(){ $uid='scwb-v8120-'.wp_generate_uuid4();ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v8120" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>.scwb-v8120{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}.scwb-v8120 header{display:flex;justify-content:space-between;gap:16px;align-items:end;flex-wrap:wrap}.scwb-v8120 button{padding:9px 14px;margin:4px}.scwb-v8120 pre{max-height:620px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}.scwb-v8120 .pass{font-weight:700}</style>
<header><div><small>SUSTAINABLE CATALYST WORKBENCH · V8.12.0</small><h3>Unified Workbench Production Certification</h3><div>Audit operational readiness across the complete Workbench stack.</div></div><button data-action="run" type="button">Run certification</button></header><div data-role="status"></div><pre data-role="output">{}</pre>
<script>(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),q=s=>root.querySelector(s);const api=async(path,method='GET',body=null)=>{const r=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v8120')); ?>+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce},body:body?JSON.stringify(body):undefined});return await r.json();};q('[data-action="run"]').onclick=async()=>{q('[data-role="status"]').textContent='Running certification…';const out=await api('/run','POST',{includeStoreWriteProbe:true,includeCoreConfiguration:true,requestedBy:'wordpress'});q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?`PASS · ${out.summary?.passed||0}/${out.summary?.total||0} checks`:`FAIL · ${out.summary?.failed||0} checks failed`;};})();</script></div><?php return ob_get_clean();}
add_shortcode('sc_workbench_production_certification','scwb_v8120_certification_shortcode');
add_action('rest_api_init',function(){register_rest_route('sc-workbench/v1/v8120','/run',array('methods'=>'POST','permission_callback'=>function(){return current_user_can('manage_options');},'callback'=>function($r){$x=scwb_v8120_backend_request('/production-certification/run','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));});
