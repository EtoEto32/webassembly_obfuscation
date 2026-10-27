import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {WeaveInstance} from './weave.mjs';import observer from './observer.cjs';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
const {call}=observer;
const value=x=>new DataView(x.ex().memory.buffer).getInt32(0,true);
const make=async bytes=>new WeaveInstance(bytes,new Map(),{yieldMs:1e9}).instantiate();
async function execute(x,entry){
  try{return await x.drive(entry,[],()=> 'hold');}
  catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e;}
}
for(const r of manifest.rows){
  if(r.status!=='valid'){rows.push({name:r.name,kind:r.kind,status:r.status});continue;}
  const raw=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.source))));
  const original=call(raw.exports._start),expectedValue=raw.exports.value();
  const expected=original.trap?{trap:true}:{status:'done',results:[]};
  const bytes=fs.readFileSync(path.join(dir,r.output)),continuous=await make(bytes);continuous.init();
  continuous.pollMode={afterPolls:1e9};const continuousResult=await execute(continuous,'_start');
  assert.deepEqual(continuousResult,expected);assert.equal(value(continuous),expectedValue);
  const scenarios=[];
  for(let stop=0;stop<=continuous.pollCount;stop++){
    const first=await make(bytes);first.init();first.pollMode={afterPolls:stop};
    const firstResult=await execute(first,'_start');
    if(firstResult.status!=='held'){scenarios.push({stopAt:stop,status:'checkpoint-not-reached',outcome:firstResult});continue;}
    // Snapshot BEFORE invoking any observer. Export wrappers mutate Weave metadata.
    const snapshot=first.checkpoint();
    let probe=null;
    if(r.kind==='observed'){
      const inspect=await make(bytes);inspect.restore(snapshot);
      probe={source:call(first.ex().__sw_data_0),restored:call(inspect.ex().__sw_data_0)};
      assert.deepEqual(probe.source,probe.restored);
      // Neither inspected instance is ever resumed.
    }
    const second=await make(bytes);second.restore(snapshot);second.pollMode={afterPolls:1e9};
    const resumed=await execute(second,null);const resumedValue=value(second);
    const matches=JSON.stringify(expected)===JSON.stringify(resumed)&&expectedValue===resumedValue;
    assert(matches);
    scenarios.push({stopAt:stop,status:'restored',resumed,resumedValue,probe,matches});
  }
  rows.push({name:r.name,kind:r.kind,status:'executed',expected,expectedValue,
    continuous:continuousResult,continuousValue:value(continuous),polls:continuous.pollCount,scenarios});
}
const result={node:process.version,v8:process.versions.v8,rows,
  scope:'Public adapter; snapshot precedes observer; disposable inspection clones are never resumed.'};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({rows:rows.length,restored:rows.flatMap(x=>x.scenarios??[]).filter(x=>x.status==='restored').length}));
