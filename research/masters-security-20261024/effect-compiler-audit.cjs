'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const{createFileExecutor}=require('./effect-engine.cjs');
const out=path.resolve(process.argv[2]),cases=JSON.parse(fs.readFileSync(path.join(out,'cases.json')));
const io=path.join(out,'io');fs.mkdirSync(io);const files=[0,1,2].map(n=>path.join(io,n+'.bin')),fds=files.map(f=>fs.openSync(f,'wx+'));
// JSON null stands for nullable Jco-host option undefined in this unit fixture.
function lifted(v){if(v===null)return undefined;if(Array.isArray(v))return v.map(lifted);if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,lifted(x)]));return v;}
let checked=0,reads=0,writes=0;const rows=[];
try{
 for(const c of cases){
  files.forEach((f,i)=>fs.writeFileSync(f,Buffer.from(c.initial[i],'hex')));
  const {build}=require(path.join(out,c.module)),ops=build(lifted(c.value));
  const concrete=ops.map(op=>({...op,objectId:op.file}));const executor=createFileExecutor(fds);executor.execute(concrete);
  const actual={files:files.map(f=>fs.readFileSync(f).toString('hex')),...executor.stats()};assert.deepEqual(actual,c.expected,JSON.stringify({module:c.module,value:c.value}));
  checked++;reads+=actual.reads;writes+=actual.writes;rows.push({module:c.module,tag:c.value.tag,operations:ops.length,matched:true});
 }
 const{build}=require(path.join(out,cases[0].module));let bounds=0;
 for(const n of[4097,8193]){const value={tag:'matrix',val:n===4097?[Array(4097).fill({sourceFile:0,targetFile:1})]:[Array(4096).fill({sourceFile:0,targetFile:1}),[{sourceFile:0,targetFile:1}]]};
  assert.throws(()=>build(value),/bound/);bounds++;}
 const result={cases:checked,recipes:new Set(cases.map(x=>x.module)).size,reads,writes,mismatches:0,boundsRejected:bounds,rows,
  scope:'unit-level generated JS builder plus real local-file executor; WIT validated, not real Component calls; independent Python byte oracle'};
 fs.writeFileSync(path.join(out,'audit.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,rows:undefined}));
}finally{for(const fd of fds)fs.closeSync(fd);}
