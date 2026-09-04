const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const v532=fs.readFileSync(path.join(root,'sc-workbench-v532.js'),'utf8');
for(const marker of ['GRAPH MATHEMATICS','SYMBOLIC CALCULUS','SOUND & MATHEMATICS','MATHEMATICS & FORM','PHYSICAL PROTOTYPING','5200','prefers-reduced-motion','backend()'])assert(v532.includes(marker),`Missing v532 marker: ${marker}`);
const graph=fs.readFileSync(path.join(root,'sc-workbench-v520.js'),'utf8');
for(const marker of ['sampledMarkers','drawTrace','requestFullscreen','surfaceState','is-dragging'])assert(graph.includes(marker),`Missing graph marker: ${marker}`);
console.log('Workbench v5.3.2 compact showcase and advanced graph browser regression passed.');
