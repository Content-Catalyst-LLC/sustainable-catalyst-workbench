const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..','wordpress-plugin','sustainable-catalyst-workbench','assets','js');
const js=fs.readFileSync(path.join(root,'sc-workbench-v550.js'),'utf8');
for(const marker of ["VERSION='5.5.0'","post(root,'construction'","post(root,'transform'","post(root,'locus'",'pointerdown','pointermove','pointerup','finalizePolygon','data-scwb-v550-tool','geometryObjectHash','navigator.clipboard']){
  assert(js.includes(marker),`Missing v5.5.0 browser marker: ${marker}`);
}
for(const forbidden of ['eval(','new Function(','window.scrollTo(','scrollIntoView(']){
  assert(!js.includes(forbidden),`Forbidden browser primitive in v5.5.0 geometry runtime: ${forbidden}`);
}
console.log('Workbench v5.5.0 dynamic geometry browser regression passed.');
