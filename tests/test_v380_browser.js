const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const storage=new Map();
const document={
  readyState:'complete',
  body:{appendChild(){}},
  querySelectorAll(){return[]},
  addEventListener(){},
  createElement(){return{click(){},remove(){}}},
};
const localStorage={
  setItem(k,v){storage.set(k,v)},
  getItem(k){return storage.has(k)?storage.get(k):null},
  removeItem(k){storage.delete(k)}
};
const URLObject={createObjectURL(){return'blob:test'},revokeObjectURL(){}};
const windowObject={SCWBV380Config:{authenticated:false,restUrl:'/wp-json/scwb/v1'},setTimeout,clearTimeout,URL:URLObject,addEventListener(){}};
const context={
  window:windowObject,document,localStorage,Blob:class Blob{},URL:URLObject,navigator:{},
  console,Promise,Date,JSON,Set,Map,Array,String,Number,Object,Math,Error,fetch(){return Promise.reject(new Error('not used'))}
};
Object.assign(windowObject,{window:windowObject,document,localStorage});
const source=fs.readFileSync(path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js','sc-workbench-v380.js'),'utf8');
for(const marker of [
  'sc-workbench-offline-install-plan/1.0',
  'sc-workbench-offline-runtime-audit/1.0',
  'sc-workbench-offline-dependency-plan/1.0',
  'sc-workbench-offline-sync-bundle/1.0',
  'sc-workbench-offline-update-plan/1.0',
  'sc-workbench-offline-recovery-plan/1.0',
  "localServiceHost: '127.0.0.1'",
  'renderRequired: false',
  'paidServiceRequired: false',
  'remoteShell: false',
  'automaticCloudUpload: false'
]) assert(source.includes(marker),`Missing marker: ${marker}`);
vm.runInNewContext(source,context,{filename:'sc-workbench-v380.js'});
const api=windowObject.SCWBOfflineInstallable;
assert(api,'API not exported');
assert.strictEqual(api.version,'3.8.0');
assert.deepStrictEqual(Array.from(api.platforms),['macos','linux','raspberry-pi']);
assert.strictEqual(api.localServiceHost,'127.0.0.1');
assert.strictEqual(api.localServicePort,8787);
assert.strictEqual(api.renderRequired,false);
assert.strictEqual(api.remoteShell,false);
console.log('Workbench v3.8.0 browser offline regression passed.');
