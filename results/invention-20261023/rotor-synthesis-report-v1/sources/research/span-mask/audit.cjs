const fs=require('node:fs'),path=require('node:path');
const out=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(out,'audit-manifest.json')));
function ev(t,a){switch(t[0]){case 'var':return a[t[1]]|0;case 'const':return t[1]|0;case 'and':return ev(t[1],a)&ev(t[2],a);case 'or':return ev(t[1],a)|ev(t[2],a);case 'xor':return ev(t[1],a)^ev(t[2],a);}}
let state=0xa71c935;function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state|0;}
const checks=[];
for(const t of m.targets){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(t.file))).exports;
 let calls=0;
 for(let k=0;k<1024;k++){const a=Array.from({length:t.n},rand),actual=e.run(...a)|0,expected=ev(t.tree,a);if(actual!==expected)throw Error(t.file);calls++;}
 if(e.bench)for(const count of [0,1,17,255]){
  let s=0x41b3917,check=0;
  for(let j=0;j<count;j++){s=(Math.imul(s,1664525)+1013904223)|0;const a=Array.from({length:t.n},(_,k)=>(((s<<k)|(s>>>(32-k)))^Math.imul(0x9e3779b9,k+1))|0);check^=ev(t.tree,a);}
  if((e.bench(count,0x41b3917)|0)!==check)throw Error('Wrapper checksum '+t.file);
 }
 checks.push({file:t.file,calls,wrapper_counts:e.bench?[0,1,17,255]:[]});
}
const scratch=[];
for(const t of m.probes){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(t.file))).exports;
 const memory=new Uint8Array(e.memory.buffer),original=new Uint8Array(memory);
 let calls=0;
 for(let pattern=0;pattern<4;pattern++){
  for(let i=t.blob_bytes;i<memory.length;i++)memory[i]=pattern===0?0:pattern===1?255:pattern===2?0x55:rand()&255;
  const before=new Uint8Array(memory);
  for(let k=0;k<256;k++){const a=Array.from({length:t.n},rand);if((e.run(...a)|0)!==ev(t.tree,a))throw Error('Initial scratch dependence');calls++;}
  for(let i=0;i<memory.length;i++)if((i<t.scratch_start||i>=t.scratch_end)&&memory[i]!==before[i])throw Error('Unexpected write at '+i);
  for(let i=0;i<t.blob_bytes;i++)if(memory[i]!==original[i])throw Error('Read-only table mutated');
 }
 scratch.push({file:t.file,calls,untouched_outside_scratch:true});
}
const result={targets:checks,calls:checks.reduce((a,b)=>a+b.calls,0),scratch,scratch_calls:scratch.reduce((a,b)=>a+b.calls,0),mismatches:0};
fs.writeFileSync(path.join(out,'audit-node.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({calls:result.calls,scratch_calls:result.scratch_calls,mismatches:0}));
