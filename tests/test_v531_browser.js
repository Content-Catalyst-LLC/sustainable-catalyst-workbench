const assert=require('assert'),fs=require('fs'),path=require('path');
const admin=fs.readFileSync(path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js','sc-workbench-v531-admin.js'),'utf8');
for(const marker of ['scwb_v531_test_backend','Test connection','canonicalBackend','backendUrl','cas'])assert(admin.includes(marker),`Missing admin marker: ${marker}`);
const front=fs.readFileSync(path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js','sc-workbench-v530.js'),'utf8');
for(const marker of ['interfaceVersion','backend offline','MATHEMATICS → SOUND','4200'])assert(front.includes(marker),`Missing homepage refinement marker: ${marker}`);
console.log('Workbench v5.3.1 browser settings/homepage regression passed.');
