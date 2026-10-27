'use strict';
const fs=require('fs'),path=require('path');const {call}=require('./observer.cjs');
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
const moduleFor=f=>new WebAssembly.Module(fs.readFileSync(path.join(dir,f)));
function host(module,stopAt,saved){
  let instance,count=0,restores=0,stopRequested=false;
  const imports={host:{should_migrate:()=>{const stop=count++===stopAt;stopRequested||=stop;return Number(stop);},restore_memory:()=>{
    restores++;if(!saved)return;
    for(const name of ['memory','checkpoint_memory']){
      const dest=new Uint8Array(instance.exports[name].buffer),bytes=saved[name];
      if(dest.length<bytes.length)throw Error('Host restore destination too short');dest.set(bytes);
    }
  }}};
  instance=new WebAssembly.Instance(module,imports);
  return {instance,run:()=>call(instance.exports._start),stats:()=>({polls:count,restores,stopRequested}),
    capture:()=>Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(instance.exports[n].buffer)]))};
}
for(const r of m.rows){
  if(r.status!=='valid'){rows.push({name:r.name,kind:r.kind,status:r.status});continue;}
  const original=new WebAssembly.Instance(moduleFor(r.source)),expected=call(original.exports._start);
  const transformed=moduleFor(r.output),continuous=host(transformed,-1),continuousOutcome=continuous.run();
  const scenarios=[];
  for(const stopAt of [0,1,2]){
    const first=host(transformed,stopAt),firstOutcome=first.run();
    if(!first.stats().stopRequested){scenarios.push({stopAt,status:'requested-checkpoint-not-reached',firstOutcome,firstStats:first.stats()});continue;}
    const saved=first.capture();
    const second=host(transformed,-1,saved),secondOutcome=second.run();
    const probe=r.kind==='observed'?{source:call(first.instance.exports.__sw_data_0),resumed:call(second.instance.exports.__sw_data_0)}:null;
    scenarios.push({stopAt,status:'checkpoint-restored',firstOutcome,firstStats:first.stats(),sourceValue:first.instance.exports.value(),
      secondOutcome,secondStats:second.stats(),resumedValue:second.instance.exports.value(),probe,
      matches:JSON.stringify(expected)===JSON.stringify(secondOutcome)&&original.exports.value()===second.instance.exports.value()});
  }
  rows.push({name:r.name,kind:r.kind,status:'executed',expected,expectedValue:original.exports.value(),
    continuous:continuousOutcome,continuousValue:continuous.instance.exports.value(),continuousStats:continuous.stats(),scenarios});
}
const result={node:process.version,v8:process.versions.v8,rows,note:'Local host adapter; not a reproduction of the complete published evaluation. Inspect continuous control before interpreting migration differences.'};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
