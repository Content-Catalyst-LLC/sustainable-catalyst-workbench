const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v580.js'),'utf8');
for(const marker of ["VERSION='5.8.0'","'/v580/resistor-network'","'/v580/rlc'","'/v580/adc-dac'","'/v580/pwm-timer'","'/v580/sampling'","'/v580/bus-plan'","'/v580/sensor-model'","'/v580/gpio-plan'","'/v580/prototype-scaffold'",'data-scwb-v580-mode','data-scwb-v580-run']){
  assert(js.includes(marker),`Missing v5.8.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.8.0 electronics/embedded runtime: ${forbidden}`);
}
console.log('Workbench v5.8.0 electronics and embedded browser regression passed.');
