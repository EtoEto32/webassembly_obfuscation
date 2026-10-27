'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),dir=process.argv[2];
const read=n=>JSON.parse(fs.readFileSync(path.join(dir,n))),fixtures=read('fixtures.json'),manifest=read('manifest.json'),records=[];
let seed=211031;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
let calls=0,booleanPatterns=0;
for(const [name,f] of Object.entries(fixtures)){
 const n=f.n,inputs=[];
 for(let base=0;base<(1<<n);base+=128){
  const words=[];for(let v=0;v<n;v++)for(let w=0;w<4;w++){
   let x=0;for(let b=0;b<32;b++)x|=(((base+w*32+b)>>>v)&1)<<b;words.push(x>>>0);
  }inputs.push(words);
 }
 const exhaustive=inputs.length;booleanPatterns+=1<<n;
 for(const value of [0,0xffffffff,0x80000000,0x7fffffff,0xaaaaaaaa,0x55555555])inputs.push(Array(n*4).fill(value));
 for(let j=0;j<256;j++)inputs.push(Array.from({length:n*4},rand));
 const expected=inputs.map(words=>{
  const values=Array.from({length:n},(_,i)=>words.slice(4*i,4*i+4));
  for(const [op,a,b] of f.ops)values.push(values[a].map((x,i)=>(op==='and'?x&values[b][i]:op==='or'?x|values[b][i]:op==='xor'?x^values[b][i]:~x)>>>0));
  return values.at(-1);
 });
 for(const row of manifest.filter(r=>r.kernel===name)){
  const bytes=fs.readFileSync(path.join(dir,row.file));assert(WebAssembly.validate(bytes));
  const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,words=new Uint32Array(e.memory.buffer),memory=new Uint8Array(e.memory.buffer);
  for(let i=0;i<inputs.length;i++){
   memory.fill(0xa5);words.set(inputs[i]);const want=memory.slice();new Uint32Array(want.buffer).set(expected[i],n*4);
   e.run();assert.deepStrictEqual(memory,want,row.file+' case '+i);calls++;
  }
  records.push({file:row.file,vector_calls:inputs.length,exhaustive_vector_calls:exhaustive,exhaustive_boolean_patterns:1<<n,random_vector_calls:256,constant_vector_calls:6,mismatches:0,unexpected_traps:0,linear_memory_bytes:memory.length});
 }
}
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({targets:records.length,calls,distinct_boolean_patterns_across_fixtures:booleanPatterns,records,node:process.version,v8:process.versions.v8},null,2),{flag:'wx'});
console.log(JSON.stringify({targets:records.length,calls,distinct_boolean_patterns_across_fixtures:booleanPatterns}));
