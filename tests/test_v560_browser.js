const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v560.js'),'utf8');
for(const marker of ["VERSION='5.6.0'","'/v560/root'","'/v560/integrate'","'/v560/differentiate'","'/v560/interpolate'","'/v560/ode'","'/v560/linear-algebra'","'/v560/optimize'",'data-scwb-v560-mode','data-scwb-v560-run']){
  assert(js.includes(marker),`Missing v5.6.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.6.0 numerical runtime: ${forbidden}`);
}
console.log('Workbench v5.6.0 numerical methods browser regression passed.');
