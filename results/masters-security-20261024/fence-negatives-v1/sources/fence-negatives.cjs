'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost}=require('./fence-runtime.cjs'),source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const right=require(path.join(source,'project.cjs')).project,wrong=require(path.join(out,'wrong-project.cjs')).project;
(async()=>{
 const rows=[];fs.mkdirSync(path.join(out,'io'));
 for(const optimization of['raw','optimized'])for(const kind of['wrong-contract','mutable-destination','async-executor'])for(const corrected of[false,true]){
  const h=createHost(kind==='wrong-contract'&&!corrected?wrong:right),dir=path.join(source,optimization);
  const api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':h.imports});
  const files=Array.from({length:3},(_,i)=>path.join(out,'io',rows.length+'-'+i+'.txt')),fds=files.map(f=>fs.openSync(f,'wx+'));
  const order=[];let admitted=false,effects=0,pending;
  const write=id=>{order.push('physical-write-'+id);assert.equal(fs.writeSync(fds[id],Buffer.from('effect')),6);effects++;};
  try{
   c.setup(0,1);
   if(kind==='wrong-contract'){
    const id=c.request(2,0);h.update(1,'write');order.push('revoke-1-write');admitted=h.admit(id,()=>write(1));
    assert.equal(admitted,!corrected);assert.equal(effects,corrected?0:1);
   }else if(kind==='mutable-destination'){
    const request={destination:0},frozen=Object.freeze({...request}),id=c.request(1,0);
    request.destination=2;h.update(2,'write');order.push('revoke-2-write');
    admitted=h.admit(id,()=>write(corrected?frozen.destination:request.destination));assert(admitted);
   }else{
    const id=c.request(1,0);order.push('logical-admission');
    admitted=h.admit(id,corrected?()=>write(0):()=>{pending=(async()=>{await Promise.resolve();write(0);})();return pending;});
    h.update(0,'write');order.push('revoke-0-write');if(pending)await pending;assert(admitted);
    const physical=order.indexOf('physical-write-0'),revoked=order.indexOf('revoke-0-write');assert.equal(physical<revoked,corrected);
   }
   const contents=files.map(f=>fs.readFileSync(f,'utf8'));
   if(kind==='wrong-contract')assert.deepEqual(contents,['',corrected?'':'effect','']);
   else if(kind==='mutable-destination')assert.deepEqual(contents,corrected?['effect','','']:['','','effect']);
   else assert.deepEqual(contents,['effect','','']);
   c.release();h.shutdown();rows.push({optimization,kind,corrected,admitted,effects,order,contents});
  }finally{h.shutdown();for(const fd of fds)fs.closeSync(fd);}
 }
 const result={summary:{hostContractNegativeCases:6,correctedControls:6,mismatches:0},rows,
  scope:'deliberately trusted-host contract violations; not attacks inside the declared threat model; async case distinguishes logical admission from OS invocation, not reversal of a previously admitted effect'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
