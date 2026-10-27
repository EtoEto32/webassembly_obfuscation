import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {WeaveInstance} from './weave.mjs';import observer from './observer.cjs';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
export function references(e,m,provider){
  const refs=new Map();
  for(let i=0;i<m.functions;i++){
    const fn=provider==='getter'?e['__sw_identity_'+i]():provider==='directory'?e.__sw_directory.get(i):e['__sw_func_'+i];
    assert.equal(typeof fn,'function');if(!refs.has(fn))refs.set(fn,[]);refs.get(fn).push(i);
  }
  const tables=[];let unknown=0;
  for(let t=0;t<m.tableCount;t++){
    const suffix=t?'_'+t:'',table=[];
    for(let i=0;i<e['__sw_length'+suffix]();i++){
      const r=m.referenceAccess==='host-table'?e['__sw_table'+suffix].get(i):e['__sw_ref'+suffix](i);if(r!==null&&!refs.has(r))unknown++;
      table.push(r===null?null:refs.get(r)??'unmapped');
    }tables.push(table);
  }
  return {tables,unknown,aliases:[...refs.values()].filter(x=>x.length>1)};
}
const rows=[];
for(const r of manifest.rows){
  if(r.status!=='valid'){rows.push(r);continue;}
  const raw=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.source))));
  const expected=references(raw.exports,r.manifest,r.mode);assert.equal(expected.unknown,0);
  const bytes=fs.readFileSync(path.join(dir,r.output));
  const make=async()=>new WeaveInstance(bytes,new Map(),{yieldMs:1e9}).instantiate();
  const woven=await make();woven.init();woven.pollMode={afterPolls:1e9};
  const actual=references(woven.ex(),r.manifest,r.mode);
  const value=[0,1,2,3].map(i=>observer.call(woven.ex().value,[i]));
  assert.deepEqual(value,[0,1,2,3].map(i=>observer.call(raw.exports.value,[i])));
  rows.push({mode:r.mode,expected,actual,value});
}
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,rows},null,2));
console.log(JSON.stringify(rows));
