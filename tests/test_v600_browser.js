const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v600.js'),'utf8');
for(const marker of ["VERSION='6.0.1'",'projectBuild','variablesResolve','linksValidate','historyBuild','exportBuild','handoffBuild','localStorage','data-scwb-v600-action']){
  assert(js.includes(marker),`Missing v6.0.1 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v6.0.1 unified runtime: ${forbidden}`);
}
console.log('Workbench v6.0.1 unified computational browser regression passed.');
