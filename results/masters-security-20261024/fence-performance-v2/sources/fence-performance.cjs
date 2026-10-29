'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost,manualProject}=require('./fence-runtime.cjs');
const source=path.resolve(process.argv[2]),mode=process.argv[3],destination=path.resolve(process.argv[4]);
const{project}=require(path.join(source,'project.cjs'));
const granularity=mode.split('-')[1],extract=mode.startsWith('manual')?manualProject:project;
const cases=[['read',0,0],['copy',2,0],['batch0',3,0],['batch1',3,1],['batch8',3,8],['batch64',3,64],['optional0',4,0],['optional1',4,1],['idle',5,0]];
function meaning(m,n){switch(m){case 0:return[[0,'read']];case 2:return[[0,'read'],[1,'write']];case 3:return Array.from({length:n},(_,i)=>[i%2,'write']);case 4:return[[0,'write'],...(n?[[1,'write']]:[])];case 5:return[];default:throw Error('oracle');}}
(async()=>{
 const dir=path.join(source,'optimized'),module=await import(pathToFileURL(path.join(dir,'unit.js')).href),h=createHost(extract,granularity);
 const c=await module.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':h.imports});
 let unsafe=0,falseRejects=0,decisions=0;const correctness=[];
 for(const[name,m,n]of cases)for(let id=0;id<3;id++)for(const permission of['read','write']){
  h.reset();c.setup(0,1);const ticket=c.request(m,n);h.update(id,permission);await Promise.resolve();
  const shouldAdmit=!meaning(m,n).some(([o,p])=>o===id&&p===permission),actual=h.admit(ticket);
  if(actual&&!shouldAdmit)unsafe++;if(!actual&&shouldAdmit)falseRejects++;decisions++;
  assert.equal(h.admit(ticket),false);correctness.push({name,id,permission,shouldAdmit,actual});c.release();h.reset();
 }
 assert.equal(unsafe,0);if(granularity==='operation')assert.equal(falseRejects,0);
 const rows=[];
 for(const[name,m,n]of cases){
  h.reset();for(let i=0;i<100;i++){c.setup(0,1);const id=c.request(m,n);await Promise.resolve();assert(h.admit(id));c.release();}
  const samples=[];for(let k=0;k<9;k++){h.reset();let accepted=0;const begin=process.hrtime.bigint();
   for(let i=0;i<200;i++){c.setup(0,1);const id=c.request(m,n);await Promise.resolve();accepted+=h.admit(id)?1:0;c.release();}
   const elapsed=Number(process.hrtime.bigint()-begin);assert.equal(accepted,200);h.reset();samples.push(elapsed/200/1000);
  }rows.push({name,mode:m,count:n,samples_us:samples});
 }
 const result={mode,rows,unsafe,falseRejects,decisions,correctness,stats:h.stats(),memory:process.memoryUsage(),maxRSS_kib:process.resourceUsage().maxRSS,
 environment:{node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch},warmup:100,batches:9,callsPerBatch:200,
 scope:'two live host resources; list length may repeat resources; includes setup, component call, JS continuation, admission, release; single process memory includes runtime'};
 fs.writeFileSync(destination,JSON.stringify(result,null,2));console.log(JSON.stringify({mode,unsafe,falseRejects,decisions}));
})().catch(e=>{console.error(e);process.exitCode=1;});
