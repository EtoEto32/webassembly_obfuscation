import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let apiCalls=0,hostCalls=0,pureTagCalls=0,preparationCalls=0;
for(const row of manifest.runtime){const traces=[];for(let side=0;side<2;side++){
 let ex,hostTrace=[];const touch=()=>{hostCalls++;const f=ex.public.get(0);let read=null;if(row.reads==='public'){read=f?.()??null;if(f)pureTagCalls++;}hostTrace.push({name:'touch',read});ex.public.set(0,null);};
 ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),{env:{touch}}).exports;ex[side===0?'retire':'release_b']();preparationCalls++;const outputs=[];
 for(const api of ['seed',...Array(row.length).fill('step')]){hostTrace=[];let outcome='return';try{ex[api]();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcome='trap';}apiCalls++;
  const f=ex.public.get(0),pub=f?.()??null;if(f)pureTagCalls++;outputs.push({api,outcome,hostTrace,public:pub});
 }traces.push(outputs);
}assert.deepEqual(traces,row.traces,row.name);}
for(const [key,value]of Object.entries({apiCalls,hostCalls,pureTagCalls,preparationCalls}))assert.equal(value,manifest.runtime.reduce((s,r)=>s+r[key],0),key);
const result={contracts:manifest.rows.length,apiCalls,hostCalls,pureTagCalls,preparationCalls,node:process.version};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
