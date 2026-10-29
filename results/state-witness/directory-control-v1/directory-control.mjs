// Adversarial observer-metadata control; these are artificial corruptions.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import observer from './observer.cjs';import directory from './directory-observer.cjs';
const [source,out]=process.argv.slice(2),manifest=JSON.parse(fs.readFileSync(path.join(source,'manifest.json')));
const row=manifest.rows.find(x=>x.mode==='directory'),bytes=fs.readFileSync(path.join(source,row.source));
const module=new WebAssembly.Module(bytes),make=()=>new WebAssembly.Instance(module);
const expected=directory.snapshot(make().exports,row.manifest),rows=[];
for(const mode of ['table-only','table-and-directory']){
  const x=make(),e=x.exports,a=e.__sw_directory.get(0),b=e.__sw_directory.get(1);
  for(const [i,ref] of [[0,b],[1,a],[2,b]])e.__sw_table.set(i,ref);
  if(mode==='table-and-directory'){e.__sw_directory.set(0,b);e.__sw_directory.set(1,a);}
  const differences=observer.difference(expected,directory.snapshot(e,row.manifest));
  const value=observer.call(e.value,[0]);assert.deepEqual(value,{value:29});
  assert.deepEqual(differences,mode==='table-only'?['tables']:[]);
  rows.push({mode,differences,originalApiValue:{value:17},changedApiValue:value,
    meaning:mode==='table-only'?'detected-corruption':'correlated-observer-metadata-corruption-not-detected'});
}
fs.writeFileSync(out,JSON.stringify({node:process.version,rows,
  scope:'Synthetic host writes, not an observed Weave defect; directory validity is an oracle premise.'},null,2));
console.log(JSON.stringify(rows));
