const fs=require('fs'),path=require('path'),cp=require('child_process'),assert=require('assert/strict'),crypto=require('crypto');
const source=process.env.TRAP_FUSION_ARTIFACTS||'C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/trap-prefix-fusion/artifacts-v2';
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:false});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
let seed=0x70ba3921;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const values=[0,1,2,3,127,128,255,256,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];while(values.length<64)values.push(rand());
const inputs=values.map(x=>[0,0,0,x,0x81234567,1]);
fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs));
fs.copyFileSync(path.join(source,'initial-memory.bin'),path.join(out,'initial-memory.bin'));
const programs=JSON.parse(fs.readFileSync(path.join(source,'programs.json'))).filter(p=>p.name==='prefix-div'||/^generated-/.test(p.name));
const results=[];
for(const p of programs){
 // Independent verifier knows source coefficients; observer process receives none.
 const coefficient=p.name==='prefix-div'?1n:BigInt(p.ops[0].args[1]>>>0);
 const expected=values.map(x=>Number(BigInt.asUintN(32,BigInt(x)*coefficient)));
 for(const kind of ['native','deferred-coalesced'])for(const mode of ['raw','O2']){
  const file=p.name+'-'+kind+'-'+mode+'.wasm',binary=path.join(source,file),bytes=fs.readFileSync(binary);
  fs.copyFileSync(binary,path.join(out,file));
  const rows=JSON.parse(cp.execFileSync(process.execPath,[path.join(__dirname,'observe.cjs'),path.join(out,file),path.join(out,'inputs.json'),path.join(out,'initial-memory.bin')],{encoding:'utf8'}));
  for(let i=0;i<rows.length;i++){assert.match(rows[i].error,/divide by zero/);assert.equal(rows[i].word0,expected[i]);assert.equal(rows[i].output,null);}
  fs.writeFileSync(path.join(out,file+'.observations.json'),JSON.stringify(rows,null,2));
  results.push({file,sha256:hash(bytes),cases:rows.length,firstStoreValuesRecovered:rows.length,mismatches:0});
 }
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,seed:'0x70ba3921',initialMemorySha256:hash(fs.readFileSync(path.join(out,'initial-memory.bin'))),programs:programs.length,results},null,2));
console.log(JSON.stringify({programs:programs.length,binaries:results.length,executions:results.reduce((n,r)=>n+r.cases,0),mismatches:0}));
