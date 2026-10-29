import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {displayYRange} from '../display-range.mjs';
import {renderReportSvg} from '../report-svg-export.mjs';
import {packageGraphRenderForReport, verifyGraphReportPackage} from '../report-render-package.mjs';
const root = fileURLToPath(new URL('../../', import.meta.url));
const cases = JSON.parse(fs.readFileSync(new URL('../../tests/fixtures/uvr-display-range.json', import.meta.url)));
const backend = JSON.parse(execFileSync('python3', ['-c', `
import json,sys
sys.path.insert(0,sys.argv[1]+'/backend')
from app.graph_svg import render_svg,display_y_range
cases=json.load(open(sys.argv[1]+'/tests/fixtures/uvr-display-range.json'))
outputs=[]
for c in cases:
 v=c['values']
 r={'ok':True,'render':{'graph':{'id':'g','projectId':'p','title':'Test','graphObjectHash':'g-hash'},'renderHash':'r-hash','views':[{'series':[{'x':list(range(len(v))),'y':v}]}]}}
 outputs.append({'bounds':display_y_range(min(v),max(v)),'svg':render_svg(r,'p','g')['svg']})
print(json.dumps(outputs))
`, root], {encoding:'utf8'}));
function element(name){return {name,attributes:{},children:[],setAttribute(k,v){this.attributes[k]=v;},appendChild(c){this.children.push(c);}};}
function find(node,name){if(node.name===name)return node;for(const c of node.children){const found=find(c,name);if(found)return found;}}
let source = fs.readFileSync(new URL('../math-renderer.js', import.meta.url),'utf8').replace('./display-range.mjs',new URL('../display-range.mjs',import.meta.url).href);
const {renderViewSpec}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
for(const [i,c] of cases.entries())test(`browser / Python SVG / report SVG parity: ${c.name}`,()=>{
 const series={x:c.values.map((_,i)=>i),y:c.values};
 const bounds=displayYRange(Math.min(...c.values),Math.max(...c.values));
 assert.deepEqual(bounds,backend[i].bounds);
 const before=structuredClone(series);
 const previous=globalThis.document;
 globalThis.document={createElement:element,createElementNS:(_ns,n)=>element(n)};
 let browser;
 try{const host=element('host');renderViewSpec(host,{views:[{kind:'cartesian-function',series:[series]}]});browser=find(host,'polyline').attributes.points;}
 finally{globalThis.document=previous;}
 const response={ok:true,render:{graph:{id:'g',projectId:'p',graphObjectHash:'g-hash'},renderHash:'r-hash',views:[{series:[series]}]}};
 const pkg=packageGraphRenderForReport({response,expectedProjectId:'p',expectedGraphId:'g'});
 const report=renderReportSvg(pkg);
 const points=s=>s.trim().split(/\s+/).map(p=>p.split(',').map(Number));
 const b=points(browser),p=points(backend[i].svg.match(/<polyline[^>]*points="([^"]+)"/)[1]),r=points(report.match(/<polyline[^>]*points="([^"]+)"/)[1]);
 for(let j=0;j<b.length;j++){
   assert.ok(Math.abs((b[j][0]-34)/832-(p[j][0]-74)/800)<0.00002);
   assert.ok(Math.abs((b[j][1]-34)/352-(p[j][1]-75)/410)<0.00002);
   assert.deepEqual(p[j],r[j]);
 }
 const ys=p.map(p=>p[1]);
 assert.ok(c.flat ? Math.max(...ys)-Math.min(...ys)<1e-8 : Math.max(...ys)-Math.min(...ys)>300);
 assert.deepEqual(series,before);
 assert.ok(verifyGraphReportPackage(pkg));
});
