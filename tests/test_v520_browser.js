const assert=require('assert'),fs=require('fs'),path=require('path'),vm=require('vm');
const document={readyState:'complete',querySelectorAll(){return[];},addEventListener(){}};
const windowObject={document,location:{origin:'https://sustainablecatalyst.com'},SCWBV520Config:{version:'5.2.0',backendUrl:'https://workbench.example'},addEventListener(){}};
const context={window:windowObject,document,console,Promise,Date,JSON,Array,String,Number,Object,Math,Error,setTimeout,clearTimeout,getComputedStyle(){return{getPropertyValue(){return'';}}},fetch(){throw new Error('unexpected fetch');}};Object.assign(windowObject,{window:windowObject});
const source=fs.readFileSync(path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js','sc-workbench-v520.js'),'utf8');
for(const marker of ["var VERSION='5.2.0'",'/v520/','graphObjectHash','SCWBGraphMathematics','derivativeOverlay','vector-field','surface'])assert(source.includes(marker),`Missing marker: ${marker}`);
vm.runInNewContext(source,context,{filename:'sc-workbench-v520.js'});const api=windowObject.SCWBGraphMathematics;assert(api,'Graph Mathematics browser API not exported');assert.strictEqual(api.version,'5.2.0');assert.strictEqual(api.endpoint('status'),'https://workbench.example/v520/status');console.log('Workbench v5.2.0 browser graph mathematics regression passed.');
