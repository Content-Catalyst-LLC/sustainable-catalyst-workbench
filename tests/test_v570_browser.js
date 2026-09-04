const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v570.js'),'utf8');
for(const marker of ["VERSION='5.7.0'","'/v570/spectrum'","'/v570/filter-design'","'/v570/transfer-function'","'/v570/root-locus'","'/v570/state-space'","'/v570/pid'","'/v570/convolve'",'data-scwb-v570-mode','data-scwb-v570-run']){
  assert(js.includes(marker),`Missing v5.7.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.7.0 signals/control runtime: ${forbidden}`);
}
console.log('Workbench v5.7.0 signals, systems, and control browser regression passed.');
