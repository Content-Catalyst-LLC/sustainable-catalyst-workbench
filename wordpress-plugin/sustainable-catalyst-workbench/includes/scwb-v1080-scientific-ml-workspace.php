<?php
/** Workbench v10.8.0 — Scientific ML Workspace. */
if (!defined('ABSPATH')) { exit; }

function scwb_v1080_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1000_backend_request')){ return scwb_v1000_backend_request($path,$method,$body); }
    $base=defined('SCWB_BACKEND_URL')?rtrim(SCWB_BACKEND_URL,'/'):rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'),'/');
    $args=array('method'=>$method,'timeout'=>120,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if($body!==null){$args['body']=wp_json_encode($body);}
    $r=wp_remote_request($base.$path,$args);
    if(is_wp_error($r)){return array('ok'=>false,'error'=>$r->get_error_message(),'_httpStatus'=>502);}
    $code=wp_remote_retrieve_response_code($r);
    $d=json_decode(wp_remote_retrieve_body($r),true);
    if(!is_array($d)){$d=array('ok'=>false,'error'=>'Invalid backend response');}
    $d['_httpStatus']=$code;
    return $d;
}

function scwb_v1080_status_shortcode(){
    $r=scwb_v1080_backend_request('/v1080/status');
    if(!empty($r['ok'])){
        return '<div class="scwb-v1080-status"><strong>Workbench v'.esc_html($r['version']).'</strong> · Scientific ML Workspace ready</div>';
    }
    return '<div class="scwb-v1080-status">Scientific ML Workspace unavailable</div>';
}
add_shortcode('sc_workbench_scientific_ml_status','scwb_v1080_status_shortcode');

function scwb_v1080_workspace_shortcode($atts=array()){
    $atts=shortcode_atts(array('project'=>'','dataset_hash'=>''),$atts,'sc_workbench_scientific_ml');
    $uid='scwb-v1080-'.wp_generate_uuid4();
    ob_start();?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v1080" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>
.scwb-v1080{border:1px solid #d7d7d7;padding:20px;border-radius:12px;font-family:system-ui,sans-serif}
.scwb-v1080 label{display:block;margin:8px 0}
.scwb-v1080 input,.scwb-v1080 textarea,.scwb-v1080 select{width:100%;max-width:900px}
.scwb-v1080 button{padding:9px 14px;margin:4px}
.scwb-v1080 pre{max-height:680px;overflow:auto;background:#111;color:#d8ffd8;padding:12px;border-radius:8px}
.scwb-v1080 .boundary{border-left:4px solid #b00020;padding-left:10px}
</style>
<header>
<small>SUSTAINABLE CATALYST WORKBENCH · V10.8.0</small>
<h3>Scientific ML Workspace</h3>
<div>Define reproducible scientific-ML studies, simulation lineage, surrogate models, hybrid mechanistic+ML contracts, and scientific constraints.</div>
</header>
<p class="boundary"><strong>Interpretation boundary:</strong> predictive performance does not certify physical truth, mechanism, or causal validity.</p>

<label>Project key <input data-f="projectKey" value="<?php echo esc_attr($atts['project']); ?>"></label>
<label>Study key <input data-f="studyKey" value="scientific-ml-study"></label>
<label>Title <input data-f="title" value="Scientific ML study"></label>
<label>Dataset record hash <input data-f="datasetRecordHash" value="<?php echo esc_attr($atts['dataset_hash']); ?>"></label>

<label>Scientific ML kind
<select data-f="scientificMLKind">
<option>surrogate-model</option>
<option>emulator</option>
<option>physics-informed-contract</option>
<option>constraint-aware-contract</option>
<option>operator-learning-contract</option>
<option>reduced-order-model</option>
<option>hybrid-mechanistic-ml</option>
<option>simulation-calibrated-ml</option>
</select>
</label>

<label>Task kind
<select data-f="taskKind">
<option>regression</option>
<option>classification</option>
<option>forecasting</option>
<option>field-prediction</option>
<option>inverse-problem</option>
<option>other</option>
</select>
</label>

<label>Variables JSON
<textarea data-f="variables" rows="6">[{"key":"x","role":"feature"},{"key":"y","role":"target"}]</textarea>
</label>

<label>Constraints JSON
<textarea data-f="constraints" rows="5">[]</textarea>
</label>

<label>Simulation bindings JSON
<textarea data-f="simulations" rows="5">[]</textarea>
</label>

<label>Objective
<textarea data-f="objective" rows="3"></textarea>
</label>

<label>Notes
<textarea data-f="notes" rows="3"></textarea>
</label>

<div>
<button data-action="compose" type="button">Compose</button>
<button data-action="save" type="button">Save study</button>
<button data-action="list" type="button">List studies</button>
</div>

<p data-role="status">Ready</p>
<pre data-role="output">{}</pre>

<script>
(()=>{
 const root=document.getElementById(<?php echo wp_json_encode($uid); ?>),
 q=s=>root.querySelector(s),
 base=<?php echo wp_json_encode(rest_url('sc-workbench/v1/v1080')); ?>;

 const api=async(path,method='GET',body=null)=>{
   const o={method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce}};
   if(body!==null)o.body=JSON.stringify(body);
   const r=await fetch(base+path,o);
   return await r.json();
 };

 const body=()=>({
   projectKey:q('[data-f="projectKey"]').value.trim(),
   studyKey:q('[data-f="studyKey"]').value.trim(),
   title:q('[data-f="title"]').value.trim(),
   datasetRecordHash:q('[data-f="datasetRecordHash"]').value.trim(),
   scientificMLKind:q('[data-f="scientificMLKind"]').value,
   taskKind:q('[data-f="taskKind"]').value,
   variables:JSON.parse(q('[data-f="variables"]').value||'[]'),
   constraints:JSON.parse(q('[data-f="constraints"]').value||'[]'),
   simulations:JSON.parse(q('[data-f="simulations"]').value||'[]'),
   objective:q('[data-f="objective"]').value,
   notes:q('[data-f="notes"]').value
 });

 async function run(a){
   q('[data-role="status"]').textContent='Working…';
   try{
     let out;
     if(a==='list'){
       out=await api('/studies/'+encodeURIComponent(q('[data-f="projectKey"]').value.trim()));
     }else{
       out=await api(a==='compose'?'/studies/compose':'/studies','POST',body());
     }
     q('[data-role="output"]').textContent=JSON.stringify(out,null,2);
     q('[data-role="status"]').textContent=out.ok?'Ready':'Request failed';
   }catch(e){
     q('[data-role="status"]').textContent=e.message;
   }
 }

 root.querySelectorAll('button[data-action]').forEach(b=>b.onclick=()=>run(b.dataset.action));
})();
</script>
</div>
<?php
    return ob_get_clean();
}
add_shortcode('sc_workbench_scientific_ml','scwb_v1080_workspace_shortcode');

add_action('rest_api_init',function(){
    $perm=function(){return current_user_can('edit_posts');};

    foreach(array('studies/compose','studies','results','compare','diagnose','core-plan') as $route){
        register_rest_route('sc-workbench/v1/v1080','/'.$route,array(
            'methods'=>'POST',
            'permission_callback'=>$perm,
            'callback'=>function($r)use($route){
                $x=scwb_v1080_backend_request('/scientific-ml/'.$route,'POST',$r->get_json_params());
                $st=intval($x['_httpStatus']??200);
                unset($x['_httpStatus']);
                return new WP_REST_Response($x,$st);
            }
        ));
    }

    register_rest_route('sc-workbench/v1/v1080','/studies/(?P<project>[^/]+)',array(
        'methods'=>'GET',
        'permission_callback'=>$perm,
        'callback'=>function($r){
            $x=scwb_v1080_backend_request('/scientific-ml/studies/'.rawurlencode($r['project']));
            $st=intval($x['_httpStatus']??200);
            unset($x['_httpStatus']);
            return new WP_REST_Response($x,$st);
        }
    ));

    register_rest_route('sc-workbench/v1/v1080','/results/(?P<project>[^/]+)/(?P<study>[^/]+)',array(
        'methods'=>'GET',
        'permission_callback'=>$perm,
        'callback'=>function($r){
            $x=scwb_v1080_backend_request('/scientific-ml/results/'.rawurlencode($r['project']).'/'.rawurlencode($r['study']));
            $st=intval($x['_httpStatus']??200);
            unset($x['_httpStatus']);
            return new WP_REST_Response($x,$st);
        }
    ));
});
