'use strict';
const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
function oracle(model,x){
  const vals=[],get=a=>a[0]==='input'?(x>>>a[1])&1:vals[a[1]];
  for(const [op,a,b] of model.gates){const u=get(a),v=get(b);vals.push(op==='and'?u&v:op==='or'?u|v:u^v);}
  return vals.at(-1);
}
const rows=[];
for(const t of m.targets){
  const b=fs.readFileSync(path.join(root,t.file));if(!WebAssembly.validate(b))throw Error('Invalid '+t.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run,model=m.models[t.name];
  const inputs=[];
  // Enumerate every meaningful external input for each small kernel. High bits
  // also vary the initial internal state, and have no source-level effect.
  for(let x=0;x<(1<<model.inputs);x++){inputs.push(x,x|0xffff0000);}
  inputs.push(0,-1,0x80000000,0x7fffffff,0x55555555,0xaaaaaaaa);
  let seed=0x20261022;for(let i=0;i<2048;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;inputs.push(seed);}
  let mismatches=0,traps=0,first=null;
  for(const x of inputs){let actual;try{actual=run(x);}catch(e){traps++;actual='trap';}
    const expected=oracle(model,x);if(actual!==expected){mismatches++;first??={x:x>>>0,actual,expected};}
  }
  if(!t.negative&&(mismatches||traps))throw Error(JSON.stringify({t,mismatches,traps,first}));
  rows.push({...t,calls:inputs.length,mismatches,traps,first});
}
process.stdout.write(JSON.stringify({rows,node:process.version,v8:process.versions.v8},null,2));
