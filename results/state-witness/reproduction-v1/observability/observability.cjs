'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');const {call,snapshot,difference}=require('./observer.cjs');
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
for(const r of m.rows){
  const raw=new WebAssembly.Module(fs.readFileSync(path.join(dir,r.source)));
  const observed=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.observed))));
  const before=snapshot(observed,r.manifest);observed.exports.drop();const after=snapshot(observed,r.manifest);
  assert.deepStrictEqual(difference(before,after),['segments']);
  const names=WebAssembly.Module.exports(raw).map(x=>x.name);let queue=[[]],checked=0,witness=null;
  for(let depth=0;depth<=6&&!witness;depth++){
    const next=[];
    for(const suffix of queue){
      const a=new WebAssembly.Instance(raw),b=new WebAssembly.Instance(raw);b.exports.drop();
      const x=suffix.map(n=>call(a.exports[n])),y=suffix.map(n=>call(b.exports[n]));checked++;
      if(JSON.stringify(x)!==JSON.stringify(y)){witness={suffix,baseline:x,changed:y};break;}
      if(depth<6)for(const n of names)next.push([...suffix,n]);
    }
    queue=next;
  }
  assert.strictEqual(Boolean(witness),r.name==='reachable');
  rows.push({name:r.name,diagnosticDifference:['segments'],checkedSuffixes:checked,depthLimit:6,witness,
    interpretation:witness?'Confirmed original-interface difference':'No bounded witness; here source inspection additionally shows only drop and constant-return exports'});
}
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({rows},null,2));console.log(JSON.stringify(rows));
