'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createEngine}=require('./effect-engine.cjs'),source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const{build}=require(path.join(out,'builder.cjs'));
const names=[['read',0,0],['write',1,0],['copy',2,0],['batch0',3,0],['batch1',3,1],['batch8',3,8],['optional0',4,0],['optional1',4,1],['idle',5,0]];
const events=[{kind:'none'},...[[0,'read'],[0,'write'],[1,'read'],[1,'write'],[2,'write']].map(([id,p])=>({kind:'revoke',id,p})),{kind:'release'},{kind:'after'}];
const payload='admitted-payload\n';
function meaning(mode,count,b){switch(mode){case 0:return[[0,'read']];case 1:return[[0,'write']];case 2:return[[0,'read'],[b,'write']];
 case 3:return Array.from({length:count},(_,i)=>[i%2?b:0,'write']);case 4:return[[0,'write'],...(count?[[b,'write']]:[])];case 5:return[];}}
(async()=>{
 const rows=[],checks=[];fs.mkdirSync(path.join(out,'io'));const files=[0,1,2].map(i=>path.join(out,'io',i+'.txt')),fds=files.map(f=>fs.openSync(f,'wx+'));
 try{
 for(const optimization of['raw','optimized']){
  const engine=createEngine(build,fds),dir=path.join(source,optimization),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':engine.imports});
  for(const alias of[false,true])for(const[name,mode,count]of names)for(const event of events){
   engine.reset();const initial=files.map((f,i)=>'initial-'+rows.length+'-'+i+'\n');files.forEach((f,i)=>fs.writeFileSync(f,initial[i]));
   const b=alias?0:1;c.setup(0,b);const id=c.request(mode,count),ops=meaning(mode,count,b),observed=engine.describe(id);
   assert.deepEqual(observed.map(o=>[o.objectId,o.op]),ops);
   // The observation is a copy; changes cannot change the internal plan.
   for(const op of observed)op.objectId=2;
   if(event.kind==='revoke')engine.revoke(event.id,event.p);if(event.kind==='release')c.release();
   await Promise.resolve();const before=engine.stats(),got=engine.admit(id),after=engine.stats();
   const want=!ops.some(([id,p])=>event.kind==='release'||event.kind==='revoke'&&event.id===id&&event.p===p);
   assert.equal(got.admitted,want);
   const expected=initial.slice(),readValues=[];
   if(want){if(mode===0)readValues.push(initial[0]);if(mode===1)expected[0]=payload;
    if(mode===2){readValues.push(initial[0]);expected[b]=initial[0];}
    if(mode===3)for(let i=0;i<count;i++)expected[i%2?b:0]=payload;
    if(mode===4){expected[0]=payload;if(count)expected[b]=payload;}}
   assert.deepEqual(files.map(f=>fs.readFileSync(f,'utf8')),expected);assert.deepEqual(got.readValues,readValues);
   if(event.kind==='after')engine.revoke(0,'write');
   assert.deepEqual(engine.admit(id),{admitted:false,readValues:[]});assert.equal(engine.stats().reads,after.reads);assert.equal(engine.stats().writes,after.writes);
   if(event.kind!=='release')c.release();engine.reset();
   rows.push({optimization,name,alias,event,admitted:want,reads:after.reads-before.reads,writes:after.writes-before.writes});
  }
  c.setup(0,1);const id=c.request(1,0);let called=false;
  assert.throws(()=>engine.admit(id,async()=>{called=true;}),/external executor forbidden/);assert.equal(called,false);
  engine.revoke(0,'write');assert.equal(engine.admit(id).admitted,false);c.release();engine.reset();
  checks.push({optimization,externalExecutorRejected:true,callbackInvoked:called,pendingRejectedAfterRevocation:true});engine.shutdown();
 }
 }finally{for(const fd of fds)fs.closeSync(fd);}
 const result={summary:{conditions:rows.length,mismatches:0,rejected:rows.filter(r=>!r.admitted).length,
  reads:rows.reduce((n,r)=>n+r.reads,0),writes:rows.reduce((n,r)=>n+r.writes,0),externalCallbackChecks:checks.length},rows,checks,
  scope:'one typed finite read/write recipe; same concrete plan drives dependencies and synchronous local-file execution; trusted backend opcode table; no new general authorization theorem'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
