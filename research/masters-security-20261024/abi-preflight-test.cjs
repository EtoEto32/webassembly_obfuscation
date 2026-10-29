'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const {estimate}=require('./abi-preflight.cjs');
const out=path.resolve(process.argv[2]);
(async()=>{
 const rows=[];let matches=0;
 for(const mode of['late','tree','memo']){
  let calls=0;const cfg={mode,budget:8192,last:null};
  const consume=value=>{calls++;let cost=1+value.length,sum=0;for(const row of value){cost+=1+row.length;for(const bytes of row){cost+=1+bytes.length;sum+=bytes.length;}}
   if(cost>cfg.budget)throw Error('late budget');let checksum=0;for(const row of value)for(const bytes of row)for(const byte of bytes)checksum+=byte;return checksum;};
  const dir=path.join(out,mode),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const instance=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{consume:{default:consume},preflightConfig:cfg});
  for(const shared of[0,1])for(const[w,n,s]of[[0,0,0],[1,0,0],[2,3,0],[1,1,64],[8,8,64],[8,8,128],[16,16,64],...(shared?[[32,32,512]]:[])]){
   const expectedCost=1+w+w*(1+n+n*(1+s)),want=expectedCost<=cfg.budget,before=calls;let got,returned=null,error=null;
   cfg.last=null;try{returned=instance.run(w,n,s,shared);got=true;}catch(e){got=false;error=String(e);assert.match(error,/budget/);}
   assert.equal(got,want);if(got)assert.equal(returned,w*n*s*7);assert.equal(calls-before,mode==='late'||want?1:0);matches++;
   rows.push({mode,shared,width:w,count:n,leafSize:s,expectedCost,accepted:got,hostCalled:calls-before,returned,error,preflight:cfg.last});
  }
 }
 // Independent finite layouts: a fresh memo per call is essential.
 const b=new ArrayBuffer(64),v=new DataView(b);v.setUint32(0,16,true);v.setUint32(4,1,true);
 const before=estimate(b,2,0,1,10);v.setUint32(4,32,true);const after=estimate(b,2,0,1,10);
 assert(before.accepted&&!after.accepted);
 const bad=[];for(const[p,n]of[[1,1],[60,1],[0,0xffffffff]]){assert.throws(()=>estimate(b,2,p,n,10),/bounds/);bad.push({p,n,rejected:true});}
 const result={componentCalls:matches,mismatches:0,rows,invalidLayoutRejected:bad,mutationBetweenCalls:{before,after},
  scope:'fixed list^3<u8>, local one-page nonshared memory; edited Jco trampoline; cost units are not host RSS or Wasmtime fuel; no engine vulnerability claim'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({componentCalls:matches,mismatches:0,invalidLayoutRejected:bad.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
