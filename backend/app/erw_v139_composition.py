"""ERW v1.3.9.0 -- additive canonical research report composition.

No scientific computation, database writes, schema changes, or automatic publication.
"""
from __future__ import annotations

PANEL = """<section id="sc-erw139" class="controls" aria-labelledby="sc-erw139-title">
<h3 id="sc-erw139-title">Research Assets · Unified Wexford Report</h3>
<p>Read-only project overview. This panel does not certify net CO₂ removal, validate scientific
models, or automatically insert material into the manuscript.</p>
<div class="sc-erw139-grid">
  <div><strong>Workbench · Calculations</strong><p>Discover saved scenario packages and eligible source-linked graphics.</p>
    <button type="button" id="sc-erw139-discover">Discover project calculations</button>
    <div id="sc-erw139-discover-result" role="status">Not requested</div></div>
  <div><strong>Evidence · Claim and source records</strong><p>Browse append-only records for this project.</p>
    <button type="button" id="sc-erw139-records">Review evidence records</button>
    <div id="sc-erw139-records-result" role="status">Not requested</div></div>
  <div><strong>Research Lab · Statistical figures</strong><p>External figure generation is not auto-executed.
    Approved SVG and provenance packages may be reviewed before manuscript insertion.</p><span>Manual review required</span></div>
  <div><strong>Knowledge Library · Sources</strong><p>Use existing PDF source and Harvard bibliography
    tools in this report. Do not treat uploaded papers as automatically verified.</p></div>
  <div><strong>Platform Core · Reproducibility</strong><p>Model and figure hashes are shown with supporting assets.
    No independent scientific certification is claimed.</p></div>
  <div><strong>Site Intelligence · Environmental context</strong><p>No vetted Wexford boundary map
    or locally verified climate series is supplied with this release.</p><span>Evidence pending</span></div>
</div>
<details><summary>Existing scientific-graphics workspaces (compatibility)</summary>
<p><a href="/erw/v1.3.8/report">Exploratory graphics</a> ·
<a href="/erw/v1.3.8.1/report">Source-linked graphics</a> ·
<a href="/erw/v1.3.8.1.1/report">Calculation discovery</a></p></details>
<p id="sc-erw139-note">Saved manuscript snapshots, existing export controls, and
authentication remain owned by the established report workspace.</p>
</section>"""

STYLE = """<style id="sc-erw139-style">
#sc-erw139{border:1px solid #cdd2d9;border-left:4px solid #a52536;
background:#f9fafb;padding:18px;margin:18px 0;border-radius:8px;color:#20242c}
#sc-erw139 .sc-erw139-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
#sc-erw139 .sc-erw139-grid>div{background:white;border:1px solid #e1e3e8;
padding:12px;border-radius:5px}
#sc-erw139 p{font-size:13px;line-height:1.5}
#sc-erw139 button{margin:6px 0}
#sc-erw139 [role=status]{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
@media print{#sc-erw139{display:none!important}}
</style>"""

# Inject into inherited authenticated script scope; project() and api() are already established there.
SCRIPT = r"""
(function(){
 const byId=id=>document.getElementById(id);
 const summary=(result)=>{
   const objects=result.objects||[];
   const total=Number.isInteger(result.total)?result.total:objects.length;
   const ready=Number.isInteger(result.chartReady)?result.chartReady:0;
   return total+' saved research object(s); '+ready+' eligible for source-derived plotting.'+
     (total && ready===0?' No compatible saved trajectory is currently available.':'');
 };
 byId('sc-erw139-discover').onclick=async()=>{
   const out=byId('sc-erw139-discover-result');out.textContent='Reading project calculation inventory…';
   try{
     const result=await api('/erw/v1.3.8.1.1/projects/'+encodeURIComponent(project())+'/discover');
     out.textContent=summary(result);
   }catch(err){out.textContent='Discovery unavailable: '+String(err.message||err)}
 };
 byId('sc-erw139-records').onclick=async()=>{
   const out=byId('sc-erw139-records-result');out.textContent='Reading project evidence registry…';
   try{
     const result=await api('/erw/v1.3.8.1.6/projects/'+encodeURIComponent(project())+'/records');
     const keys=Object.keys(result);
     const collection=keys.map(k=>result[k]).find(v=>Array.isArray(v));
     out.textContent=(collection?collection.length:'Available')+' evidence record(s).'+
       ' Review source citations and classification before publication.';
   }catch(err){out.textContent='Evidence registry unavailable: '+String(err.message||err)}
 };
})();
"""

def compose_page(page: str) -> str:
    """Return original authenticated canvas plus additive asset navigation."""
    if 'id="sc-erw139"' in page:
        raise ValueError("Unified report panel already inserted")
    anchor = '<label>Saved object</label>'
    script_anchor = "el('addsection').onclick="
    if page.count(anchor) != 1 or page.count(script_anchor) != 1 or not (0 <= page.find('</head>') < page.find('<body')):
        raise ValueError("Unexpected inherited report markup; refusing unsafe injection")
    # Place inside the existing side workspace and inside its authenticated JS scope.
    page = page.replace(anchor, PANEL + '\n' + anchor, 1)
    page = page.replace(script_anchor, SCRIPT + '\n' + script_anchor, 1)
    page = page.replace('</head>', STYLE + '</head>', 1)
    return page
