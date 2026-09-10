const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v590.js'),'utf8');
for(const marker of ["VERSION='5.9.0'",'truthTable','minimize','karnaugh','fsm','timing','hdlScaffold','resourceEstimate','pynqOverlay','data-scwb-v590-mode','data-scwb-v590-run']){
  assert(js.includes(marker),`Missing v5.9.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.9.0 digital logic runtime: ${forbidden}`);
}
console.log('Workbench v5.9.0 FPGA and digital logic browser regression passed.');
