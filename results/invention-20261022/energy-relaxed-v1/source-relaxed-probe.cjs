'use strict';
const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
function oracle(model,x){
  const vals=[],get=a=>a[0]==='input'?(x>>>a[1])&1:vals[a[1]];
  for(const [op,a,b] of model.gates){const u=get(a),v=get(b);vals.push(op==='and'?u&v:op==='or'?u|v:u^v);}
  return vals.at(-1);
}
const rows=[];
for(const p of m.probes){
  const bytes=fs.readFileSync(path.join(root,p.file));if(!WebAssembly.validate(bytes))throw Error('Invalid '+p.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run,model=m.models[p.name];
  let calls=0;
  for(let x=0;x<(1<<model.inputs);x++){
    const expected=oracle(model,x);
    for(let state=0;state<(1<<p.n);state++){
      const actual=run(x,state);calls++;
      if(actual!==expected)throw Error(JSON.stringify({p,x,state,actual,expected}));
    }
  }
  rows.push({...p,calls,mismatches:0});
}
process.stdout.write(JSON.stringify({rows,node:process.version,v8:process.versions.v8},null,2));
