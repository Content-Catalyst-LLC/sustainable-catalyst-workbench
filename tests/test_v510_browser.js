const assert=require('assert'),fs=require('fs'),path=require('path'),vm=require('vm');
const document={readyState:'complete',querySelectorAll(){return[];},addEventListener(){}};
const windowObject={document,location:{origin:'https://sustainablecatalyst.com'},SCWBV510Config:{version:'5.1.0',backendUrl:'https://workbench.example'}};
const context={window:windowObject,document,console,Promise,Date,JSON,Array,String,Number,Object,Math,Error,fetch(){throw new Error('unexpected fetch');}};Object.assign(windowObject,{window:windowObject});
const source=fs.readFileSync(path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js','sc-workbench-v510.js'),'utf8');
for(const marker of ["var VERSION='5.1.0'",'/v510/','CAS backend unavailable','SCWBMathematics'])assert(source.includes(marker),`Missing marker: ${marker}`);
vm.runInNewContext(source,context,{filename:'sc-workbench-v510.js'});const api=windowObject.SCWBMathematics;assert(api,'Mathematics browser API not exported');assert.strictEqual(api.version,'5.1.0');assert.strictEqual(api.endpoint('status'),'https://workbench.example/v510/status');console.log('Workbench v5.1.0 browser mathematics regression passed.');
