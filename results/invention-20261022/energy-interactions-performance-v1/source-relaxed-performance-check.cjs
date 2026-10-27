'use strict';
const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'performance.json'),'utf8'));
function oracle(model,x){
  const vals=[],get=a=>a[0]==='input'?(x>>>a[1])&1:vals[a[1]];
  for(const [op,a,b] of model.gates){const u=get(a),v=get(b);vals.push(op==='and'?u&v:op==='or'?u|v:u^v);}
  return vals.at(-1);
}
const rows=[];
for(const t of m.targets){
  const opt=fs.readFileSync(path.join(root,t.optimized_file)),wrapped=fs.readFileSync(path.join(root,t.file));
  if(!WebAssembly.validate(opt)||!WebAssembly.validate(wrapped))throw Error('validation '+t.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(opt)).exports.run;
  const bench=new WebAssembly.Instance(new WebAssembly.Module(wrapped)).exports.bench;
  const model=m.models[t.name],inputs=[];
  for(let x=0;x<(1<<model.inputs);x++)inputs.push(x,x|0xffff0000);
  inputs.push(0,-1,0x80000000,0x7fffffff,0x55555555,0xaaaaaaaa);
  let rng=0x20261022;for(let i=0;i<2048;i++){rng=(Math.imul(rng,1664525)+1013904223)>>>0;inputs.push(rng);}
  for(const x of inputs)if(run(x)!==oracle(model,x))throw Error('run '+t.file);
  let checks=0;
  for(const count of [1,3,31,257])for(const seed of [0,1,0xffffffff,0x80000000]){
    let x=seed,sum=0;for(let i=0;i<count;i++){x=(Math.imul(x,1664525)+1013904223)>>>0;sum=(sum+oracle(model,x))|0;}
    if(bench(count,seed)!==sum)throw Error('bench '+t.file);checks++;
  }
  rows.push({name:t.name,mode:t.mode,run_calls:inputs.length,wrapper_checks:checks});
}
process.stdout.write(JSON.stringify({rows,node:process.version,v8:process.versions.v8,cpu:require('os').cpus()[0].model},null,2));
