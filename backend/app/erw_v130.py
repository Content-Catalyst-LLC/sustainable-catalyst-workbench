"""ERW 1.3.0 — Scientific Document Canvas & Rich-Text Authoring foundation.

Retains v1.2.2 identity/project ownership, append-only report snapshots,
source integrity checks and export. Uses a legible page-oriented canvas
without claiming DOCX/PDF generation or PDF ingestion.
"""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .erw_v122 import build_page as authenticated_page

router=APIRouter(tags=["erw-1.3.0-document-canvas"])
STYLE=r"""
<style id="sc-document-canvas-theme">
:root{--ink:#17191e;--muted:#586273;--red:#b62335;--line:#dfe2e7;--paper:#fff;--s:#f1f3f5}
body{background:var(--s);color:var(--ink);font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:15px;line-height:1.5}
header{padding:17px 3vw;background:#101115;border-bottom:3px solid var(--red)}
header h1{font-size:19px;letter-spacing:.035em}
main{max-width:1640px;grid-template-columns:minmax(290px,340px) minmax(0,1fr);gap:20px;margin:24px auto}
aside,article{background:white;border:1px solid var(--line);border-radius:10px;box-shadow:0 5px 25px #11111109;padding:22px}
aside{max-height:calc(100vh - 115px);overflow-y:auto;position:sticky;top:16px}
article{padding:32px 46px;min-width:0}
h2{font-size:20px;margin:0 0 10px}h3{font-size:16px}
label{font-size:13px;color:#333b48}input,textarea,select{border:1px solid #c8cdd4;border-radius:5px;background:white;color:var(--ink);line-height:1.5}
input:focus,textarea:focus,select:focus{outline:2px solid #9c2b3b;outline-offset:1px}
button{border-radius:5px;background:#17191e;font-size:13px;font-weight:600;padding:10px 13px}
button:hover{background:#9d2636}.caution{background:#fbf1f0;color:#612d2f;border-left-color:var(--red)}
#editor-tools{display:flex;flex-wrap:wrap;gap:7px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);margin-bottom:18px}
#editor-tools button{margin:0}#editor-tools button[aria-pressed=true]{background:#a62e3a}
#document-outline{border:1px solid var(--line);padding:12px 14px;background:#f9fafb;margin:14px 0;border-radius:6px}
#document-outline h3{margin:0 0 8px}#document-outline button{display:block;text-align:left;width:100%;margin:3px 0;padding:7px 10px;background:white;color:#333;border:1px solid var(--line)}
#document-outline button:hover{background:#f4e9e9}
.section{padding:18px 0;border-bottom:1px solid #e4e6eb}
.section label{font-size:17px;font-weight:700;color:#262a32;margin-bottom:9px}
.section textarea{font-family:Georgia,'Times New Roman',serif;font-size:16px;line-height:1.75;padding:14px 16px;min-height:135px}
#previewbox{background:#fff;width:min(100%,850px);min-height:600px;margin:20px auto;padding:55px 68px;box-shadow:0 7px 35px #10101018;border:1px solid #e6e6e6}
#previewbox h1{font:700 27px Georgia,serif;line-height:1.25}
#previewbox h2{font:700 20px Georgia,serif;margin-top:34px}
#previewbox p{font:16px/1.65 Georgia,serif;color:#222}
#previewbox table{font-family:system-ui;font-size:13px}
#previewbox th{background:#eff1f4;text-align:left}
#previewbox .insert{border-left:3px solid #8d2938;padding:8px 12px;background:#fbfaf9;font:13px/1.5 system-ui}
#source-note{padding:10px 12px;border:1px solid #d9b8b4;background:#fff8f7;color:#643d3b;font-size:13px;border-radius:5px}
#canvas-mode-note{font-size:12px;color:#626c7a}
body.reading-mode #sections{display:none}
body.reading-mode #previewbox{display:block}
body:not(.reading-mode) #previewbox:empty{display:none}
@media(max-width:1020px){main{grid-template-columns:1fr}aside{position:static;max-height:none}article{padding:22px}#previewbox{padding:30px}}
@media print{body{background:white}header,aside,.controls,#editor-tools,#document-outline,#source-note,.section,article>h2{display:none!important}main{display:block;margin:0;max-width:none}article{padding:0;border:0;box-shadow:none}#previewbox{border:0;box-shadow:none;width:100%;min-height:0;margin:0;padding:0;display:block!important}#previewbox p{font-size:11pt}#previewbox h2{break-after:avoid}}
</style>
"""
TOOLS=r"""<div id="editor-tools" class="controls" role="toolbar" aria-label="Document mode">
<button id="editmode" aria-pressed="true" type="button">Edit manuscript</button>
<button id="readmode" aria-pressed="false" type="button">Document preview</button>
<span id="canvas-mode-note">Save a snapshot to preserve changes. Preview does not save.</span>
</div>
<div id="source-note">Source PDFs, automatic Harvard citations, native DOCX/PDF files, and journal-style typesetting are planned—not available in this build. Figures and equations may still display provenance placeholders.</div>
<div id="document-outline" class="controls"><h3>Document outline</h3><div id="outline-items"></div></div>"""
SCRIPT=r"""<script id="sc-canvas-controls">
(()=>{'use strict';
const E=id=>document.getElementById(id);
const outline=E('outline-items'),sections=E('sections');
let observed=0;
function makeOutline(){
 const entries=Array.from(sections.querySelectorAll('.section'));
 if(entries.length===observed&&outline.children.length===observed)return;
 observed=entries.length;outline.replaceChildren();
 entries.forEach((entry,i)=>{
  const label=entry.querySelector('label');
  const button=document.createElement('button');button.type='button';
  button.textContent=(i+1)+'. '+(label?.textContent||'Section');
  button.onclick=()=>{document.body.classList.remove('reading-mode');E('editmode').setAttribute('aria-pressed','true');E('readmode').setAttribute('aria-pressed','false');entry.scrollIntoView({behavior:'smooth',block:'center'});entry.querySelector('textarea')?.focus()};
  outline.append(button);
 });
}
const observer=new MutationObserver(makeOutline);
observer.observe(sections,{childList:true});makeOutline();
E('editmode').onclick=()=>{document.body.classList.remove('reading-mode');E('editmode').setAttribute('aria-pressed','true');E('readmode').setAttribute('aria-pressed','false')};
E('readmode').onclick=async()=>{
 E('preview').click();
 await new Promise(resolve=>setTimeout(resolve,250));
 if(!E('previewbox').innerHTML.trim())return;
 document.body.classList.add('reading-mode');
 E('editmode').setAttribute('aria-pressed','false');E('readmode').setAttribute('aria-pressed','true');
 E('previewbox').scrollIntoView({behavior:'smooth',block:'start'});
};
})();
</script>"""
def canvas_page():
    page=authenticated_page()
    assert page.startswith("<!doctype html>") and "</head>" in page
    assert page.count('<article><h2>Manuscript editor</h2>')==1
    assert page.rstrip().endswith("</html>") && "</body>" in page
    page=page.replace("</head>",STYLE+"</head>",1)
    page=page.replace('<article><h2>Manuscript editor</h2>','<article><h2>Scientific document canvas</h2>'+TOOLS,1)
    before, marker, after = page.rpartition('</body>')
    assert marker and after.strip() == '</html>'
    page=before+SCRIPT+marker+after
    return page
def status():
    return {"ok":True,"extensionVersion":"1.3.0",
      "scientificDocumentCanvas":True,"documentOutline":True,
      "editAndPreviewModes":True,"snapshotPersistence":"existing-v1.2.0",
      "projectScopedAuthentication":"existing-v1.2.2",
      "pdfSourceUpload":False,"harvardReferences":False,
      "nativeDocxExport":False,"nativePdfExport":False,
      "publicationEnabled":False,"verifiedCDR":False}
@router.get("/erw/v1.3.0/status")
def status_route():return status()
@router.get("/erw/v1.3.0/report",response_class=HTMLResponse)
def report_route():return HTMLResponse(canvas_page())
