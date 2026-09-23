<?php
/** Workbench v8.9.0 — Interactive Scientific Figure & Visualization Composer. */
if (!defined('ABSPATH')) { exit; }

function scwb_v890_backend_request($path, $method='GET', $body=null) {
    $base = untrailingslashit((string)get_option('sc_workbench_backend_url', 'https://workbench-api.sustainablecatalyst.com'));
    $args = array('method'=>$method, 'timeout'=>30, 'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if ($body !== null) { $args['body'] = wp_json_encode($body); }
    $r = wp_remote_request($base.$path, $args);
    if (is_wp_error($r)) { return array('ok'=>false, 'error'=>$r->get_error_message()); }
    $j = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($j)) { $j = array('ok'=>false, 'error'=>'Invalid backend response'); }
    $j['_httpStatus'] = wp_remote_retrieve_response_code($r);
    return $j;
}

function scwb_v890_status_shortcode() {
    $r = scwb_v890_backend_request('/v890/status');
    return '<pre class="scwb-v890-status">'.esc_html(wp_json_encode($r, JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)).'</pre>';
}
add_shortcode('sc_workbench_scientific_figure_composer_status', 'scwb_v890_status_shortcode');

function scwb_v890_composer_shortcode($atts=array()) {
    $a = shortcode_atts(array('project'=>''), $atts);
    $project = sanitize_text_field($a['project']);
    $uid = 'scwb-v890-'.wp_generate_uuid4();
    ob_start(); ?>
<div id="<?php echo esc_attr($uid); ?>" class="scwb-v890" data-nonce="<?php echo esc_attr(wp_create_nonce('wp_rest')); ?>">
  <header class="scwb-v890-head">
    <div><small>SUSTAINABLE CATALYST WORKBENCH · V8.9.0</small><h3>Interactive Scientific Figure &amp; Visualization Composer</h3><p>Compose provenance-linked figures from completed Workbench runs with explicit metric and encoding choices.</p></div>
    <div class="scwb-v890-project"><label>Project<input data-role="project" value="<?php echo esc_attr($project); ?>" placeholder="project-key"></label><button data-action="load" type="button">Load sources</button></div>
  </header>
  <div class="scwb-v890-grid">
    <aside>
      <h4>Source runs</h4><div data-role="jobs" class="scwb-v890-jobs"><em>Load a project.</em></div>
      <h4>Figure</h4>
      <label>Title<input data-role="title" value="Scientific figure"></label>
      <label>Theme<select data-role="theme"><option value="publication">Publication</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
      <label>Columns<select data-role="columns"><option>1</option><option>2</option><option>3</option><option>4</option></select></label>
      <button data-action="add-panel" type="button">+ Add panel</button>
      <button class="scwb-v890-primary" data-action="compose" type="button">Compose figure</button>
    </aside>
    <main>
      <div data-role="status" class="scwb-v890-statusline">Select source runs and define at least one panel.</div>
      <section><h4>Panels</h4><div data-role="panels" class="scwb-v890-panels"></div></section>
      <section><h4>Preview</h4><div data-role="preview" class="scwb-v890-preview"><span>Figure preview will appear here.</span></div></section>
      <section class="scwb-v890-spec"><div><h4>Figure specification</h4><button data-action="download-json" type="button" disabled>Download JSON</button><button data-action="download-svg" type="button" disabled>Download SVG</button></div><pre data-role="spec">{}</pre></section>
    </main>
  </div>
  <footer>Figure composition is an analytical presentation view. Source jobs/results remain authoritative; Workbench does not infer significance, causality, scientific validity, or a preferred model.</footer>
</div>
<style>
.scwb-v890{background:#080909;color:#d8d8d8;border:1px solid #272929;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}.scwb-v890 *{box-sizing:border-box}.scwb-v890-head{display:flex;justify-content:space-between;gap:18px;padding:15px;border-bottom:1px solid #252727;align-items:flex-end}.scwb-v890 h3,.scwb-v890 h4{margin:4px 0 9px}.scwb-v890 small{color:#8bd3a7}.scwb-v890 p{margin:4px 0;color:#aaa;font-size:11px}.scwb-v890-project{display:flex;gap:8px;align-items:end}.scwb-v890 label{display:block;font-size:10px;color:#aaa;margin:7px 0}.scwb-v890 input,.scwb-v890 select,.scwb-v890 button{width:100%;background:#111;color:#ddd;border:1px solid #373a3a;padding:7px;font:inherit}.scwb-v890 button{cursor:pointer;margin:4px 0}.scwb-v890-primary{border-color:#617b69!important;color:#b8f2ca!important}.scwb-v890-grid{display:grid;grid-template-columns:290px minmax(0,1fr);min-height:620px}.scwb-v890 aside{padding:12px;border-right:1px solid #252727}.scwb-v890 main{padding:12px;min-width:0}.scwb-v890-jobs{max-height:220px;overflow:auto;border:1px solid #242626;padding:4px}.scwb-v890-jobs label{padding:5px;border-bottom:1px solid #202222}.scwb-v890-jobs input{width:auto;margin-right:5px}.scwb-v890-statusline{padding:8px;border:1px solid #29302b;background:#0d100e;color:#a9c7b2}.scwb-v890-panels{display:grid;gap:8px}.scwb-v890-panel{display:grid;grid-template-columns:1.2fr .7fr 1fr 1.2fr auto;gap:6px;border:1px solid #292b2b;padding:8px;align-items:end}.scwb-v890-panel button{width:auto}.scwb-v890-preview{min-height:320px;border:1px solid #2c2e2e;background:#fff;color:#111;padding:10px;overflow:auto}.scwb-v890-preview svg{width:100%;min-width:460px;height:300px}.scwb-v890-spec>div{display:flex;align-items:center;gap:8px}.scwb-v890-spec button{width:auto}.scwb-v890-spec pre{max-height:260px;overflow:auto;background:#050606;border:1px solid #232525;padding:9px;font-size:9px}.scwb-v890 footer{padding:9px 12px;border-top:1px solid #252727;color:#858585;font-size:9px}@media(max-width:850px){.scwb-v890-grid{grid-template-columns:1fr}.scwb-v890 aside{border-right:0;border-bottom:1px solid #252727}.scwb-v890-head{display:block}.scwb-v890-panel{grid-template-columns:1fr 1fr}.scwb-v890-preview svg{min-width:0}}
</style>
<script>(function(){
const root=document.getElementById(<?php echo wp_json_encode($uid); ?>);if(!root)return;
const rest=<?php echo wp_json_encode(esc_url_raw(rest_url('sc-workbench/v1/figure-composer/'))); ?>,nonce=root.dataset.nonce,$=s=>root.querySelector(s),$$=s=>Array.from(root.querySelectorAll(s));
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));let catalog=null,lastSpec=null,lastSvg='';let panelSeq=0;
const api=(path,method='GET',body=null)=>fetch(rest+path,{method,headers:{'Accept':'application/json','Content-Type':'application/json','X-WP-Nonce':nonce},body:body?JSON.stringify(body):undefined}).then(async r=>{const b=await r.json();if(!r.ok||b.ok===false)throw new Error(typeof b.detail==='string'?b.detail:(b.error||JSON.stringify(b.detail||'Request failed')));return b;});
function project(){return $('[data-role=project]').value.trim()}
function metrics(scope){if(!catalog)return[];return (scope==='request'?catalog.requestMetrics:catalog.resultMetrics).map(x=>x.metric)}
function metricOptions(scope,selected=''){return metrics(scope).map(m=>'<option value="'+esc(m)+'" '+(m===selected?'selected':'')+'>'+esc(m)+'</option>').join('')}
function addPanel(){panelSeq++;const d=document.createElement('div');d.className='scwb-v890-panel';d.dataset.panel=String(panelSeq);const first=metrics('result')[0]||'';d.innerHTML='<label>Panel title<input data-f="title" value="Panel '+panelSeq+'"></label><label>Mark<select data-f="mark"><option>line</option><option>scatter</option><option>bar</option><option>point</option><option>table</option></select></label><label>Scope<select data-f="scope"><option value="result">result</option><option value="request">request</option></select></label><label>Y metric<select data-f="y">'+metricOptions('result',first)+'</select></label><button data-action="remove-panel" type="button">×</button><label style="display:none" data-x-wrap>X metric<select data-f="x"><option value="">—</option>'+metricOptions('result')+'</select></label>'; $('[data-role=panels]').appendChild(d);d.querySelector('[data-f=scope]').addEventListener('change',e=>{const scope=e.target.value;d.querySelector('[data-f=y]').innerHTML=metricOptions(scope);d.querySelector('[data-f=x]').innerHTML='<option value="">—</option>'+metricOptions(scope)});d.querySelector('[data-f=mark]').addEventListener('change',e=>{d.querySelector('[data-x-wrap]').style.display=e.target.value==='scatter'?'block':'none'});d.querySelector('[data-action=remove-panel]').addEventListener('click',()=>d.remove())}
async function load(){if(!project())return;$('[data-role=status]').textContent='Loading figure sources…';try{catalog=await api('source-catalog/'+encodeURIComponent(project()));$('[data-role=jobs]').innerHTML=(catalog.jobs||[]).map(j=>'<label><input type="checkbox" value="'+esc(j.jobId)+'"> '+esc(j.label||j.jobId)+'<br><small>'+esc(j.runtimeKind)+' · '+j.resultMetricCount+' result metrics</small></label>').join('')||'<em>No completed runs.</em>';$$('[data-role=panels] .scwb-v890-panel').forEach(x=>x.remove());addPanel();$('[data-role=status]').textContent=catalog.completedJobCount+' completed runs · '+catalog.resultMetrics.length+' result metrics available';}catch(e){$('[data-role=status]').textContent='Error: '+e.message}}
function panelPayload(){return $$('[data-role=panels] .scwb-v890-panel').map((p,i)=>{const mark=p.querySelector('[data-f=mark]').value,scope=p.querySelector('[data-f=scope]').value;return{panelId:'panel-'+(i+1),title:p.querySelector('[data-f=title]').value,mark,metricScope:scope,xMetric:mark==='scatter'?p.querySelector('[data-f=x]').value:'',yMetrics:[p.querySelector('[data-f=y]').value].filter(Boolean),showLegend:true}})}
function render(spec){const panel=spec.panels[0];if(!panel){return ''}if(panel.mark==='table'){const ys=panel.encoding.y.map(x=>x.field);return '<table style="border-collapse:collapse;width:100%;font:12px sans-serif"><tr><th style="text-align:left">Run</th>'+ys.map(y=>'<th>'+esc(y)+'</th>').join('')+'</tr>'+panel.rows.map(r=>'<tr><td>'+esc(r.label)+'</td>'+ys.map(y=>'<td style="text-align:right">'+esc(r[y]??'—')+'</td>').join('')+'</tr>').join('')+'</table>'}const ys=panel.encoding.y.map(x=>x.field),y=ys[0],rows=panel.rows.filter(r=>Number.isFinite(Number(r[y]))&&Number.isFinite(Number(r.x)));if(!rows.length)return '<span>No finite values available for preview.</span>';const W=760,H=280,pad=42,xs=rows.map(r=>Number(r.x)),vs=rows.map(r=>Number(r[y])),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...vs),ymax=Math.max(...vs),sx=x=>pad+((x-xmin)/(xmax-xmin||1))*(W-2*pad),sy=v=>H-pad-((v-ymin)/(ymax-ymin||1))*(H-2*pad);let marks='';if(panel.mark==='bar'){const bw=Math.max(10,(W-2*pad)/(rows.length*1.8));marks=rows.map(r=>'<rect x="'+(sx(Number(r.x))-bw/2)+'" y="'+sy(Number(r[y]))+'" width="'+bw+'" height="'+(H-pad-sy(Number(r[y])))+'" fill="currentColor" opacity=".72"/>').join('')}else{const pts=rows.map(r=>sx(Number(r.x))+','+sy(Number(r[y]))).join(' ');if(panel.mark==='line')marks+='<polyline points="'+pts+'" fill="none" stroke="currentColor" stroke-width="2"/>';marks+=rows.map(r=>'<circle cx="'+sx(Number(r.x))+'" cy="'+sy(Number(r[y]))+'" r="4" fill="currentColor"><title>'+esc(r.label)+': '+esc(r[y])+'</title></circle>').join('')}lastSvg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+H+'" role="img"><rect width="100%" height="100%" fill="white"/><g color="#111"><line x1="'+pad+'" y1="'+(H-pad)+'" x2="'+(W-pad)+'" y2="'+(H-pad)+'" stroke="#777"/><line x1="'+pad+'" y1="'+pad+'" x2="'+pad+'" y2="'+(H-pad)+'" stroke="#777"/>'+marks+'<text x="'+pad+'" y="20" font-family="sans-serif" font-size="14">'+esc(panel.title)+'</text><text x="'+pad+'" y="'+(H-8)+'" font-family="sans-serif" font-size="10">'+esc(panel.encoding.x.label)+'</text></g></svg>';return lastSvg}
async function compose(){const ids=$$('[data-role=jobs] input:checked').map(x=>x.value),panels=panelPayload();if(!ids.length){$('[data-role=status]').textContent='Select at least one completed run.';return}if(!panels.length||panels.some(p=>!p.yMetrics.length)){ $('[data-role=status]').textContent='Define at least one panel with a metric.';return }try{$('[data-role=status]').textContent='Composing…';lastSpec=await api('compose','POST',{projectKey:project(),jobIds:ids,title:$('[data-role=title]').value,theme:$('[data-role=theme]').value,columns:Number($('[data-role=columns]').value),panels});$('[data-role=status]').textContent='Figure '+lastSpec.figureHash.slice(0,12)+' · '+lastSpec.panels.length+' panel(s) · provenance preserved';$('[data-role=spec]').textContent=JSON.stringify(lastSpec,null,2);$('[data-role=preview]').innerHTML=render(lastSpec);$('[data-action=download-json]').disabled=false;$('[data-action=download-svg]').disabled=!lastSvg}catch(e){$('[data-role=status]').textContent='Error: '+e.message}}
function download(name,type,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$('[data-action=load]').addEventListener('click',load);$('[data-action=add-panel]').addEventListener('click',addPanel);$('[data-action=compose]').addEventListener('click',compose);$('[data-action=download-json]').addEventListener('click',()=>lastSpec&&download('workbench-figure-'+lastSpec.figureHash.slice(0,12)+'.json','application/json',JSON.stringify(lastSpec,null,2)));$('[data-action=download-svg]').addEventListener('click',()=>lastSvg&&download('workbench-figure-'+(lastSpec?lastSpec.figureHash.slice(0,12):'preview')+'.svg','image/svg+xml',lastSvg));if(project())load();else addPanel();
})();</script>
<?php return ob_get_clean();
}
add_shortcode('sc_workbench_scientific_figure_composer', 'scwb_v890_composer_shortcode');

add_action('rest_api_init', function(){
    register_rest_route('sc-workbench/v1', '/figure-composer/source-catalog/(?P<project>[A-Za-z0-9._:-]+)', array(
        'methods'=>'GET', 'permission_callback'=>'__return_true',
        'callback'=>function($req){ return rest_ensure_response(scwb_v890_backend_request('/figure-composer/source-catalog/'.rawurlencode($req['project']))); }
    ));
    register_rest_route('sc-workbench/v1', '/figure-composer/compose', array(
        'methods'=>'POST', 'permission_callback'=>'__return_true',
        'callback'=>function($req){ $body=$req->get_json_params(); $result=scwb_v890_backend_request('/figure-composer/compose','POST',is_array($body)?$body:array()); $status=isset($result['_httpStatus'])?(int)$result['_httpStatus']:200; unset($result['_httpStatus']); return new WP_REST_Response($result,$status); }
    ));
});
