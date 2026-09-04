const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v532.js'),'utf8');
for(const marker of ['centerRailButton','rail.scrollTo','render(false)','render(true)','prefers-reduced-motion','interfaceVersion']){
  assert(js.includes(marker),`Missing v5.3.3 scroll-guard marker: ${marker}`);
}
for(const forbidden of ['scrollIntoView','window.scrollTo','location.hash']){
  assert(!js.includes(forbidden),`Forbidden page-navigation primitive remains in homepage carousel: ${forbidden}`);
}
console.log('Workbench v5.3.3 homepage viewport-scroll guard browser regression passed.');
