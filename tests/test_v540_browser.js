const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v540.js'),'utf8');
for(const marker of ['VERSION=\'5.4.0\'','multi-graph','loadTable','nearestTrace','data-scwb-v540-series-row','domainMin','tangentAt','includeNormal','region','wheel','pointerdown','pointerup','requestFullscreen']){
  assert(js.includes(marker),`Missing v5.4.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.4.0 graph runtime: ${forbidden}`);
}
console.log('Workbench v5.4.0 advanced graph browser regression passed.');
