import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import observer from './observer.cjs';const {call,snapshot,difference}=observer;
const dir=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
for(const c of m.cases){
 const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,c.file)));
 for(const target of c.segments){
  const a=new WebAssembly.Instance(module),b=new WebAssembly.Instance(module),seg=target.segment;
  b.exports[`__ctx_drop_${seg.kind}_${seg.index}`]();
  assert.deepEqual(difference(snapshot(a,c.observer),snapshot(b,c.observer)),['segments']);
  const trace=[];let witness=null,skipped=0;
  for(const command of c.commands){
   const action=command.action;
   if(!action||action.type!=='invoke'||action.module||(action.args??[]).some(a=>!['i32','i64'].includes(a.type))){skipped++;continue;}
   const args=action.args.map(x=>x.type==='i64'?BigInt.asIntN(64,BigInt(x.value)):Number(BigInt.asIntN(32,BigInt(x.value))));
   const ao=call(a.exports[action.field],args),bo=call(b.exports[action.field],args);
   trace.push({line:command.line,api:action.field,args:action.args,baseline:ao,changed:bo});
   if(JSON.stringify(ao)!==JSON.stringify(bo)){witness={length:trace.length,line:command.line,api:action.field};break;}
  }
  const certified=target.certificate.status==='certified-no-segment-effect';assert(!(certified&&witness));
  rows.push({source:c.source,sourceSha256:c.sourceSha256,file:c.file,segment:{kind:seg.kind,index:seg.index},
   certificate:target.certificate,status:witness?'api-witness':certified?'certified-no-segment-effect':'unresolved',
   witness,skippedCommands:skipped,trace,finalStateDifferences:difference(snapshot(a,c.observer),snapshot(b,c.observer))});
 }
}
const summary={modules:m.cases.length,uniqueBinaries:new Set(m.cases.map(x=>x.sourceSha256)).size,pairs:rows.length,
 apiWitnesses:rows.filter(r=>r.witness).length,certified:rows.filter(r=>r.status==='certified-no-segment-effect').length,
 unresolved:rows.filter(r=>r.status==='unresolved').length,apiCalls:rows.reduce((n,r)=>n+2*r.trace.length,0),
 skippedCommands:rows.reduce((n,r)=>n+r.skippedCommands,0)};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,summary,rows},null,2));console.log(JSON.stringify(summary));
