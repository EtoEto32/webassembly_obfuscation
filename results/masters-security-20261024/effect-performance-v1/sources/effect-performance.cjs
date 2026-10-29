'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost,manualProject}=require('./fence-runtime.cjs'),{createEngine,createFileExecutor}=require('./effect-engine.cjs');
const source=path.resolve(process.argv[2]),generated=path.resolve(process.argv[3]),mode=process.argv[4],destination=path.resolve(process.argv[5]);
const{project}=require(path.join(source,'project.cjs')),{build}=require(path.join(generated,'builder.cjs'));
const payload='admitted-payload\n';
function manualOps(v){const read=file=>({op:'read',file}),write=file=>({op:'write',file,literal:payload});
 switch(v.tag){case'read':return[read(v.val)];case'write':return[write(v.val)];case'copy':return[read(v.val.source),{op:'write',file:v.val.destination,from:0}];
 case'batch':return v.val.map(write);case'optional':return[write(v.val.primary),...(v.val.backup===undefined?[]:[write(v.val.backup)])];case'idle':return[];default:throw Error('tag');}}
function baseline(extract,fds){const h=createHost(extract),plans=new Map(),executor=createFileExecutor(fds),prepare=h.imports.prepare;
 h.imports.prepare=v=>{const id=prepare(v),ticket=h.tickets.get(id),ops=manualOps(v);assert.equal(ticket.slots.length,ops.length);
  plans.set(id,Object.freeze(ops.map((op,i)=>Object.freeze({op:op.op,objectId:ticket.slots[i].objectId,
   ...(Object.hasOwn(op,'literal')?{literal:op.literal}:{}),...(Object.hasOwn(op,'from')?{from:op.from}:{})}))));return id;};
 return{imports:h.imports,admit(id){const plan=plans.get(id);if(!plan)return{admitted:false,readValues:[]};plans.delete(id);
  let readValues=[];const admitted=h.admit(id,()=>{readValues=executor.execute(plan);});return{admitted,readValues};},
 revoke:(id,p)=>h.update(id,p),reset(){assert.equal(plans.size,0);h.reset();},shutdown(){plans.clear();h.shutdown();},
 stats(){return{...h.stats(),...executor.stats()};}};}
const cases=[['read',0,0],['write',1,0],['copy',2,0],['batch8',3,8],['optional1',4,1],['idle',5,0]];
function deps(m){return m===0?[[0,'read']]:m===1?[[0,'write']]:m===2?[[0,'read'],[1,'write']]:m===5?[]:[[0,'write'],[1,'write']];}
(async()=>{
 const io=destination+'.io';fs.mkdirSync(io);const files=[0,1,2].map(i=>path.join(io,i+'.txt')),fds=files.map(f=>fs.openSync(f,'wx+'));
 const engine=mode==='plan-generated'?createEngine(build,fds):baseline(mode==='separate-manual'?manualProject:project,fds);
 const initial=['a'.repeat(1024),'b'.repeat(1024),'unused'];const initialize=()=>files.forEach((f,i)=>fs.writeFileSync(f,initial[i]));
 try{
  const dir=path.join(source,'optimized'),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':engine.imports});
  let decisions=0,unsafe=0,falseRejects=0;
  for(const[name,m,n]of cases)for(let id=0;id<3;id++)for(const p of['read','write']){
   engine.reset();initialize();c.setup(0,1);const ticket=c.request(m,n);engine.revoke(id,p);await Promise.resolve();
   const want=!deps(m).some(([o,q])=>o===id&&q===p),got=engine.admit(ticket).admitted;
   if(got&&!want)unsafe++;if(!got&&want)falseRejects++;decisions++;assert.equal(got,want);c.release();engine.reset();
  }
  const rows=[];
  for(const[name,m,n]of cases){
   engine.reset();initialize();for(let i=0;i<30;i++){c.setup(0,1);const id=c.request(m,n);await Promise.resolve();assert(engine.admit(id).admitted);c.release();}
   const samples=[];for(let k=0;k<9;k++){engine.reset();const before=process.hrtime.bigint();
    for(let i=0;i<50;i++){c.setup(0,1);const id=c.request(m,n);await Promise.resolve();if(!engine.admit(id).admitted)throw Error('unexpected denial');c.release();}
    samples.push(Number(process.hrtime.bigint()-before)/50/1000);engine.reset();}
   const expected=initial.slice();if(m===1)expected[0]=payload;if(m===2)expected[1]=initial[0];if(m===3||m===4){expected[0]=payload;expected[1]=payload;}
   assert.deepEqual(files.map(f=>fs.readFileSync(f,'utf8')),expected);rows.push({name,samples_us:samples});
  }
  const result={mode,rows,decisions,unsafe,falseRejects,stats:engine.stats(),memory:process.memoryUsage(),maxRSS_kib:process.resourceUsage().maxRSS,
   environment:{node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch},warmup:30,batches:9,callsPerBatch:50,
   scope:'same synchronous file executor; two resources, warm OS page cache, no fsync; includes real local I/O but not FD open/close'};
  fs.writeFileSync(destination,JSON.stringify(result,null,2));console.log(JSON.stringify({mode,decisions,unsafe,falseRejects}));
 }finally{engine.shutdown();for(const fd of fds)fs.closeSync(fd);}
})().catch(e=>{console.error(e);process.exitCode=1;});
