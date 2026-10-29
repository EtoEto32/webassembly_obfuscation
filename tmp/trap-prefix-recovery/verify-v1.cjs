'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const source=process.env.TRAP_FUSION_ARTIFACTS||'C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/trap-prefix-fusion/artifacts-v2';
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
const inputs=JSON.parse(fs.readFileSync(path.join(source,'inputs.json'))),programs=JSON.parse(fs.readFileSync(path.join(source,'programs.json'))),initial=fs.readFileSync(path.join(source,'initial-memory.bin'));
const publicInputs=path.join(out,'public-inputs.json');fs.writeFileSync(publicInputs,JSON.stringify(inputs.cases));
// Independent reference logs actual prefix stores, rather than simulating the candidate's log.
function expected(program,args){
 const mem=Buffer.from(initial),view=new DataView(mem.buffer,mem.byteOffset,mem.byteLength),r=Object.fromEntries(inputs.params.map((p,i)=>[p,BigInt(args[i])])),stores=[];
 for(const ins of program.ops){const a=ins.args.map(v=>typeof v==='number'?BigInt(v>>>0):r[v]);let value;
  if(['load','store'].includes(ins.op)&&a[0]+4n>65536n)break;
  if(ins.op==='div'&&a[1]===0n)break;
  switch(ins.op){case'add':value=a[0]+a[1];break;case'mul':value=a[0]*a[1];break;case'xor':value=a[0]^a[1];break;case'div':value=a[0]/a[1];break;case'load':value=BigInt(view.getUint32(Number(a[0]),true));break;case'store':view.setUint32(Number(a[0]),Number(a[1]),true);stores.push({address:Number(a[0]),value:Number(a[1])});break;default:throw Error('Unknown IR');}
  if(ins.out)r[ins.out]=BigInt.asUintN(32,value);
 }
 return stores;
}
const results=[];
for(const program of programs)for(const mode of ['raw','O2']){
 const file=program.name+'-deferred-coalesced-'+mode+'.wasm',target=path.join(out,file);
 cp.execFileSync(process.execPath,[path.join(__dirname,'recover.cjs'),path.join(source,file),publicInputs,path.join(source,'initial-memory.bin'),target]);
 const rows=JSON.parse(fs.readFileSync(path.join(target,'observations.json'))),original=JSON.parse(fs.readFileSync(path.join(source,file+'.observations.json')));let events=0,nonempty=0;
 for(let i=0;i<inputs.cases.length;i++){
  const log=expected(program,inputs.cases[i]);assert.deepEqual(rows[i].recoveredStores,log);events+=log.length;if(log.length)nonempty++;
  assert.equal(rows[i].output,original[i].output);assert.equal(rows[i].memorySha256,original[i].memorySha256);
  const trap=rows[i].trap===null?null:/divide by zero/.test(rows[i].trap)?'divide':/memory access out of bounds/.test(rows[i].trap)?'memory':'unexpected';assert.equal(trap,original[i].trap);
 }
 results.push({file,...JSON.parse(fs.readFileSync(path.join(target,'extraction.json'))),exactOrderedLogs:rows.length,nonemptyLogs:nonempty,events,mismatches:0,instrumentationBehaviorMismatches:0});
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,results},null,2));
console.log(JSON.stringify({binaries:results.length,logs:results.reduce((s,r)=>s+r.exactOrderedLogs,0),nonemptyLogs:results.reduce((s,r)=>s+r.nonemptyLogs,0),events:results.reduce((s,r)=>s+r.events,0),mismatches:0,selectedGroupCounts:[...new Set(results.map(r=>r.selected.calls))]},null,2));
