'use strict';
// Deliberately violates the documented exclusive-offset precondition, locally.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto'),{Worker}=require('worker_threads'),{partition}=require('./partition.cjs');
const out=process.argv[2],hash=m=>crypto.createHash('sha256').update(new Uint8Array(m.buffer)).digest('hex');
async function main(){
  fs.mkdirSync(out,{recursive:false});fs.mkdirSync(path.join(out,'sources'));for(const f of ['interference.cjs','partition.cjs'])fs.copyFileSync(path.join(__dirname,f),path.join(out,'sources',f));const rows=[];
  try{
    const worker=new Worker(`const {parentPort}=require('worker_threads');parentPort.on('message',m=>{parentPort.postMessage(Atomics.notify(new Int32Array(m.buffer),0));});`,{eval:true});
    try{
      await new Promise((resolve,reject)=>{worker.once('online',resolve);worker.once('error',reject);});
      for(let trial=0;trial<5;trial++){
        const a=new WebAssembly.Memory({initial:1,maximum:2,shared:true}),b=new WebAssembly.Memory({initial:1,maximum:2,shared:true}),before=[hash(a),hash(b)];
        const outside=Atomics.waitAsync(new Int32Array(a.buffer),0,0);assert(outside.async);
        // partition synchronously registers both owned waiters and notifies A.
        // Its notify count is 2: one owned waiter plus our unrelated waiter.
        const pending=partition([a,b]);
        const notified=new Promise((resolve,reject)=>{worker.once('message',resolve);worker.once('error',reject);worker.postMessage(b);});
        // The worker supplies the missing owned completion, from the other block.
        const result=await pending;assert.strictEqual(await notified,1);assert.strictEqual(await outside.value,'ok');assert.deepStrictEqual(result.labels,[0,0]);assert.deepStrictEqual([hash(a),hash(b)],before);
        rows.push({trial,truePartition:[0,1],observed:result.labels,status:'false-union',guardEffect:'unnecessary rejection if used only to require non-alias',unchangedBytes:true});
      }
    }finally{await worker.terminate();}
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({rows,node:process.version,conclusion:'Matching notify count and completion count do not establish the exclusivity precondition. No hostile-runtime or external-service exploit was tested.'},null,2));console.log(JSON.stringify({trials:rows.length,rows}));
  }finally{
    const files={};for(const dir of [out,path.join(out,'sources')])for(const name of fs.readdirSync(dir)){const p=path.join(dir,name);if(fs.statSync(p).isFile()&&name!=='sha256.json')files[path.relative(out,p).replaceAll('\\','/')]=crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(files,null,2));
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
