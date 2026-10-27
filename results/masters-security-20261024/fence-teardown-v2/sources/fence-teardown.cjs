'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost}=require('./fence-runtime.cjs');
const out=path.resolve(process.argv[2]),{project}=require(path.join(out,'project.cjs'));
const dispose=Symbol.dispose||Symbol.for('dispose');
async function instance(optimization){const dir=path.join(out,optimization),h=createHost(project);
 const api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
 const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':h.imports});return{h,c};}
const cases=[['normal'],['cancel'],['bad-tag'],['oversize'],['open-fails'],
 ['prepare-trap',1,0],['prepare-trap',2,0],['prepare-trap',3,8],['prepare-trap',4,1],['prepare-trap',5,0],
 ['pending'],['drop-pending'],['double-drop'],['multiple-pending'],['shutdown-after-admission']];
(async()=>{
 const rows=[],bounds=[],isolation=[];let fdChecks=0;
 fs.mkdirSync(path.join(out,'io'));
 for(const optimization of ['raw','optimized'])for(const alias of[false,true])for(const[kind,mode,count]of cases){
  const{h,c}=await instance(optimization),files=Array.from({length:3},(_,i)=>path.join(out,'io',rows.length+'-'+i+'.txt'));
  const fds=files.map(f=>fs.openSync(f,'wx+'));let error=null,effects=0,before,shutdown;
  const ids=[];const effect=()=>{fs.writeSync(fds[0],Buffer.from('accepted'));effects++;};
  try{
   try{
    c.setup(0,kind==='open-fails'?99:alias?0:1);
    if(kind==='bad-tag')c.request(6,0);
    else if(kind==='oversize')c.request(3,65);
    else if(kind==='prepare-trap')c.requestThenTrap(mode,count);
    else if(kind==='normal'){const id=c.request(1,0);ids.push(id);assert(h.admit(id,effect));c.release();}
    else if(kind==='cancel'){const id=c.request(2,0);ids.push(id);assert(h.cancel(id));assert.equal(h.cancel(id),false);c.release();}
    else if(kind==='double-drop'){c.release();c.release();}
    else if(kind==='multiple-pending'){ids.push(c.request(2,0),c.request(1,0),c.request(5,0));}
    else if(kind==='shutdown-after-admission'){const id=c.request(1,0);ids.push(id);assert(h.admit(id,effect));}
    else{ids.push(c.request(2,0));if(kind==='drop-pending')c.release();}
   }catch(e){error=String(e);}
   const shouldThrow=['bad-tag','oversize','open-fails','prepare-trap','double-drop'].includes(kind);
   assert.equal(!!error,shouldThrow,kind);
   for(const id of h.tickets.keys())if(!ids.includes(id))ids.push(id);
   const distinct=alias?1:2;
   let owned=['normal','cancel','double-drop','drop-pending'].includes(kind)?0:kind==='open-fails'?1:2;
   let pending=0,retained=0;
   if(['pending','drop-pending'].includes(kind)){pending=1;retained=distinct;}
   if(kind==='multiple-pending'){pending=3;retained=distinct+1;}
   if(kind==='prepare-trap'){pending=1;retained=mode===5?0:mode===1?1:distinct;}
   before=h.stats();assert.equal(before.logicalPins,owned+retained,kind);assert.equal(before.liveTickets,pending,kind);
   shutdown=h.shutdown();assert.deepEqual(shutdown,{closedResources:owned,cancelledTickets:pending});
   assert.equal(h.stats().logicalPins,0);assert.equal(h.stats().liveTickets,0);assert(h.stats().closed);
   assert.deepEqual(h.shutdown(),{closedResources:0,cancelledTickets:0});
   const priorEffects=effects;for(const id of[0,1,0xffffffff,...ids])assert.equal(h.admit(id,effect),false);assert.equal(effects,priorEffects);
   assert.throws(()=>h.imports.open(0),/closed/);assert.throws(()=>h.imports.prepare({tag:'idle'}),/closed/);
   assert.throws(()=>h.update(0,'write'),/closed/);
   const expected=effects?['accepted','','']:['','',''];assert.deepEqual(files.map(f=>fs.readFileSync(f,'utf8')),expected);
  }finally{h.shutdown();for(const fd of fds)fs.closeSync(fd);}
  for(const fd of fds){assert.throws(()=>fs.readSync(fd,Buffer.alloc(1),0,1,0),e=>e.code==='EBADF');fdChecks++;}
  rows.push({optimization,alias,kind,mode,count,error,before,shutdown,after:h.stats(),effects,closedFDs:3});
 }
 // Independent instance ledgers and FD ownership; no shared backend is implied.
 for(const optimization of ['raw','optimized']){
  const a=await instance(optimization),b=await instance(optimization);a.c.setup(0,1);b.c.setup(0,1);
  const at=a.c.request(1,0),bt=b.c.request(1,0);a.h.shutdown();let effects=0;
  assert.equal(a.h.admit(at,()=>effects++),false);assert(b.h.admit(bt,()=>effects++));assert.equal(effects,1);b.c.release();b.h.shutdown();
  isolation.push({optimization,otherInstanceAdmitted:true,a:a.h.stats(),b:b.h.stats()});
 }
 for(const kind of['slot-reuse','slot-invalidate','permission','object-epoch','reentrant-shutdown','late-drop']){
  const h=createHost(project),file=h.imports.open(0),rec=h.slots[0];let error=null;
  if(kind==='slot-reuse'){file[dispose]();rec.generation=Number.MAX_SAFE_INTEGER;assert.throws(()=>h.imports.open(0),/generation exhausted/);}
  if(kind==='slot-invalidate'){rec.generation=Number.MAX_SAFE_INTEGER;assert.throws(()=>h.invalidate(0),/generation exhausted/);}
  if(kind==='permission'){h.objects[0].epoch.write=Number.MAX_SAFE_INTEGER;assert.throws(()=>h.update(0,'write'),/generation exhausted/);assert(h.objects[0].allowed.write);assert.equal(h.objects[0].objectEpoch,0);}
  if(kind==='object-epoch'){h.objects[0].objectEpoch=Number.MAX_SAFE_INTEGER;assert.throws(()=>h.update(0,'write'),/generation exhausted/);assert.equal(h.objects[0].epoch.write,0);}
  if(kind==='reentrant-shutdown'){const id=h.imports.prepare({tag:'write',val:file});try{h.admit(id,()=>h.shutdown());}catch(e){error=String(e);}assert.match(error,/reentrant/);assert.equal(h.stats().liveTickets,0);}
  h.shutdown();if(kind==='late-drop'){file[dispose]();file[dispose]();}assert.equal(h.stats().logicalPins,0);
  bounds.push({kind,error,stats:h.stats()});
 }
 const result={summary:{scenarios:rows.length,mismatches:0,observedExceptions:rows.filter(r=>r.error).length,
  closedFDChecks:fdChecks,isolatedInstancePairs:isolation.length,boundaryChecks:bounds.length},rows,isolation,bounds,
  scope:'one host ledger per component instance; fresh instance-owned local FDs; synchronous effects; no multi-threaded or shared-backend reclamation claim'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
