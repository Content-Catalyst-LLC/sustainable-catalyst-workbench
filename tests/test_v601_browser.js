const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const primary=fs.readFileSync(path.join(root,'scwb-primary-repair.js'),'utf8');
const graph=fs.readFileSync(path.join(root,'sc-workbench-v540.js'),'utf8');
const exp=fs.readFileSync(path.join(root,'sc-workbench-v601.js'),'utf8');
for(const marker of ["VERSION = '6.0.1'",'favoritesKey','recentsKey','data-scwb-studio-filter','scwb:studio-activated','scwb:visual-resize']) assert(primary.includes(marker),`Missing v6.0.1 primary marker: ${marker}`);
for(const marker of ['ResizeObserver','redrawStable','fullscreenchange','visibilitychange']) assert(graph.includes(marker),`Missing graph hardening marker: ${marker}`);
for(const marker of ["'6.0.1'",'/v601/status','redrawGraphs']) assert(exp.includes(marker),`Missing v6.0.1 experience marker: ${marker}`);
for(const forbidden of ['window.scrollTo(','scrollIntoView(','new Function(']){assert(!primary.includes(forbidden));assert(!graph.includes(forbidden));assert(!exp.includes(forbidden));}
console.log('Workbench v6.0.1 unified experience browser regression passed.');
