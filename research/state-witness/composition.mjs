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
  const scenarios=[];
  if(r.mode==='directory'){
    assert.deepEqual(actual,expected);
    const rawResult=observer.call(raw.exports._start);assert.deepEqual(rawResult,{value:null});
    const expectedFinal=references(raw.exports,r.manifest,r.mode);
    const plain=await make();plain.init();plain.pollMode={afterPolls:1e9};
    const done=await plain.drive('_start',[],()=> 'hold');assert.equal(done.status,'done');
    assert.deepEqual(references(plain.ex(),r.manifest,r.mode),expectedFinal);
    for(let stop=0;stop<=plain.pollCount;stop++){
      const first=await make();first.init();first.pollMode={afterPolls:stop};
      const held=await first.drive('_start',[],()=> 'hold');
      if(held.status!=='held'){scenarios.push({stop,status:'checkpoint-not-reached'});continue;}
      const saved=first.checkpoint();const second=await make();second.restore(saved);second.pollMode={afterPolls:1e9};
      // Do not inspect tables before resume materializes their shadow state.
      const resumed=await second.drive(null,[],()=> 'hold');assert.deepEqual(resumed,done);
      const final=references(second.ex(),r.manifest,r.mode);assert.deepEqual(final,expectedFinal);
      const memory=Buffer.from(new Uint8Array(second.ex().__sw_memory.buffer,0,65536));
      assert(memory.equals(Buffer.from(raw.exports.__sw_memory.buffer)));
      const segment=observer.call(second.ex().__sw_elem_1);assert.deepEqual(segment,{trap:true});
      const repeat=references(second.ex(),r.manifest,r.mode);assert.deepEqual(repeat,final);
      scenarios.push({stop,status:'restored',resumed,final,segment,memoryEqual:true});
    }
  }
  rows.push({mode:r.mode,expected,actual,value,scenarios});
}
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,rows},null,2));
console.log(JSON.stringify(rows));
