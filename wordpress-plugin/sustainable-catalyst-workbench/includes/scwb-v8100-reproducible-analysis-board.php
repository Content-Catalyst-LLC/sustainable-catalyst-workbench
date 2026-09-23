<?php
/** Workbench v8.10.0 — Reproducible Analysis Board. */
if (!defined('ABSPATH')) { exit; }

function scwb_v8100_backend_request($path, $method='GET', $body=null) {
    $base=untrailingslashit((string)get_option('sc_workbench_backend_url','https://workbench-api.sustainablecatalyst.com'));
    $args=array('method'=>$method,'timeout'=>45,'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if ($body!==null) { $args['body']=wp_json_encode($body); }
    $r=wp_remote_request($base.$path,$args);
    if (is_wp_error($r)) { return array('ok'=>false,'error'=>$r->get_error_message()); }
    $j=json_decode(wp_remote_retrieve_body($r),true);
    if (!is_array($j)) { $j=array('ok'=>false,'error'=>'Invalid backend response'); }
    $j['_httpStatus']=wp_remote_retrieve_response_code($r); return $j;
}

function scwb_v8100_status_shortcode() {
    $r=scwb_v8100_backend_request('/v8100/status');
    return '<pre class="scwb-v8100-status">'.esc_html(wp_json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)).'</pre>';
}
add_shortcode('sc_workbench_reproducible_analysis_board_status','scwb_v8100_status_shortcode');

function scwb_v8100_board_shortcode($atts=array()) {
    $a=shortcode_atts(array('project'=>''),$atts); $project=sanitize_text_field($a['project']); $uid='scwb-v8100-'.wp_generate_uuid4();
    ob_start(); ?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v8100" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
<style>
#<?php echo esc_attr($uid); ?>{font-family:inherit;border:1px solid #d8d8d8;border-radius:14px;overflow:hidden;background:#fff;color:#161616}#<?php echo esc_attr($uid); ?> *{box-sizing:border-box}
#<?php echo esc_attr($uid); ?> header{padding:18px 20px;background:#111;color:#fff;display:flex;justify-content:space-between;gap:20px;align-items:end}#<?php echo esc_attr($uid); ?> header small{letter-spacing:.08em}#<?php echo esc_attr($uid); ?> header h3{margin:5px 0 4px}#<?php echo esc_attr($uid); ?> .grid{display:grid;grid-template-columns:minmax(260px,340px) 1fr;min-height:520px}#<?php echo esc_attr($uid); ?> aside{padding:16px;border-right:1px solid #ddd;background:#fafafa}#<?php echo esc_attr($uid); ?> main{padding:18px;min-width:0}#<?php echo esc_attr($uid); ?> label{display:block;font-size:12px;font-weight:700;margin:10px 0 4px}#<?php echo esc_attr($uid); ?> input,#<?php echo esc_attr($uid); ?> textarea{width:100%;padding:8px;border:1px solid #bbb;border-radius:7px;background:#fff}#<?php echo esc_attr($uid); ?> textarea{min-height:72px}#<?php echo esc_attr($uid); ?> button{padding:8px 11px;border:1px solid #111;border-radius:7px;background:#fff;cursor:pointer;margin:5px 5px 5px 0}#<?php echo esc_attr($uid); ?> button.primary{background:#111;color:#fff}#<?php echo esc_attr($uid); ?> .sources{max-height:180px;overflow:auto;border:1px solid #ddd;padding:7px;border-radius:7px;background:#fff}#<?php echo esc_attr($uid); ?> .sources label{font-weight:500;margin:4px 0}#<?php echo esc_attr($uid); ?> pre{white-space:pre-wrap;word-break:break-word;background:#111;color:#e8ffe8;padding:14px;border-radius:9px;max-height:480px;overflow:auto}@media(max-width:800px){#<?php echo esc_attr($uid); ?> .grid{grid-template-columns:1fr}#<?php echo esc_attr($uid); ?> aside{border-right:0;border-bottom:1px solid #ddd}}
</style>
<header><div><small>SUSTAINABLE CATALYST WORKBENCH · V8.10.0</small><h3>Reproducible Analysis Board</h3><div>Assemble source-linked analysis, figures, narrative, provenance and immutable snapshots.</div></div><div><input data-role="project" value="<?php echo esc_attr($project); ?>" placeholder="project-key"><button data-action="load" type="button">Load</button></div></header>
<div class="grid"><aside>
<label>Title</label><input data-role="title" value="Reproducible analysis board">
<label>Description</label><textarea data-role="description"></textarea>
<h4>Execution runs</h4><div class="sources" data-role="jobs"><em>Load a project.</em></div>
<h4>Research assets</h4><div class="sources" data-role="assets"><em>Load a project.</em></div>
<label>Assumptions (one per line)</label><textarea data-role="assumptions"></textarea>
<label>Methods (one per line)</label><textarea data-role="methods"></textarea>
<label>Findings (researcher-authored, one per line)</label><textarea data-role="findings"></textarea>
<label>Notes (one per line)</label><textarea data-role="notes"></textarea>
<button class="primary" data-action="build" type="button">Build board</button><button data-action="snapshot" type="button">Save immutable snapshot</button>
</aside><main><div data-role="status">Load a project to begin.</div><h4>Analysis board specification</h4><pre data-role="output">{}</pre></main></div>
<script>
(()=>{const root=document.getElementById(<?php echo wp_json_encode($uid); ?>);if(!root)return;const q=s=>root.querySelector(s), qa=s=>[...root.querySelectorAll(s)];let catalog=null;
const api=async(path,method='GET',body=null)=>{const r=await fetch(<?php echo wp_json_encode(rest_url('sc-workbench/v1/v8100')); ?>+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-WP-Nonce':root.dataset.nonce},body:body?JSON.stringify(body):undefined});return await r.json();};
const lines=(role,kind)=>q(`[data-role="${role}"]`).value.split(/\n+/).map(x=>x.trim()).filter(Boolean).map((text,i)=>({itemId:`${kind}-${i+1}`,kind,title:'',text,evidenceRefs:[],state:'working'}));
const payload=()=>({projectKey:q('[data-role="project"]').value.trim(),title:q('[data-role="title"]').value,description:q('[data-role="description"]').value,jobIds:qa('[data-job]:checked').map(x=>x.value),assetKeys:qa('[data-asset]:checked').map(x=>x.value),narrative:[...lines('assumptions','assumption'),...lines('methods','method'),...lines('findings','finding'),...lines('notes','note')],includeTimeline:true,includeLineage:true});
q('[data-action="load"]').onclick=async()=>{const p=q('[data-role="project"]').value.trim();if(!p)return; q('[data-role="status"]').textContent='Loading…';catalog=await api('/catalog?project='+encodeURIComponent(p));q('[data-role="jobs"]').innerHTML=(catalog.jobs||[]).map(j=>`<label><input type="checkbox" data-job value="${String(j.jobId||'').replace(/"/g,'&quot;')}"> ${j.label||j.jobId} · ${j.status||''}</label>`).join('')||'<em>No jobs.</em>';q('[data-role="assets"]').innerHTML=(catalog.assets||[]).map(a=>`<label><input type="checkbox" data-asset value="${String(a.assetKey||'').replace(/"/g,'&quot;')}"> ${a.title||a.assetKey}</label>`).join('')||'<em>No assets.</em>';q('[data-role="status"]').textContent=`Loaded ${catalog.jobs?.length||0} jobs, ${catalog.assets?.length||0} assets, ${catalog.snapshotCount||0} snapshots.`;};
q('[data-action="build"]').onclick=async()=>{q('[data-role="status"]').textContent='Building…';const out=await api('/build','POST',payload());q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?`Board ${out.boardHash?.slice(0,12)||''} built.`:(out.error||'Build failed');};
q('[data-action="snapshot"]').onclick=async()=>{q('[data-role="status"]').textContent='Saving snapshot…';const body={...payload(),snapshotLabel:q('[data-role="title"]').value,createdBy:'wordpress'};const out=await api('/snapshot','POST',body);q('[data-role="output"]').textContent=JSON.stringify(out,null,2);q('[data-role="status"]').textContent=out.ok?`Snapshot ${out.snapshotHash?.slice(0,12)||''} saved.`:(out.error||'Snapshot failed');};
})();
</script></div><?php return ob_get_clean();
}
add_shortcode('sc_workbench_reproducible_analysis_board','scwb_v8100_board_shortcode');

add_action('rest_api_init',function(){
    register_rest_route('sc-workbench/v1/v8100','/catalog',array('methods'=>'GET','permission_callback'=>function(){return current_user_can('read');},'callback'=>function($r){$p=sanitize_text_field($r->get_param('project'));$x=scwb_v8100_backend_request('/analysis-board/source-catalog/'.rawurlencode($p));$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v8100','/build',array('methods'=>'POST','permission_callback'=>function(){return current_user_can('read');},'callback'=>function($r){$x=scwb_v8100_backend_request('/analysis-board/build','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
    register_rest_route('sc-workbench/v1/v8100','/snapshot',array('methods'=>'POST','permission_callback'=>function(){return current_user_can('edit_posts');},'callback'=>function($r){$x=scwb_v8100_backend_request('/analysis-board/snapshots','POST',$r->get_json_params());$st=intval($x['_httpStatus']??200);unset($x['_httpStatus']);return new WP_REST_Response($x,$st);}));
});
