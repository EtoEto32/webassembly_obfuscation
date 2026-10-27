'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto'),{Worker}=require('worker_threads'),vm=require('vm');
const {partition}=require('./partition.cjs');
const [oldPath,pairPath,out]=process.argv.slice(2),old=require(path.resolve(oldPath)).partition;
const memory=()=>new WebAssembly.Memory({initial:1,maximum:4,shared:true});
const getter=Object.getOwnPropertyDescriptor(WebAssembly.Memory.prototype,'buffer').get,buffer=m=>Reflect.apply(getter,m,[]),hash=m=>crypto.createHash('sha256').update(new Uint8Array(buffer(m))).digest('hex');
async function main(){
  fs.mkdirSync(out,{recursive:false});fs.mkdirSync(path.join(out,'sources'));for(const f of ['boundary-audit.cjs','partition.cjs'])fs.copyFileSync(path.join(__dirname,f),path.join(out,'sources',f));fs.copyFileSync(oldPath,path.join(out,'sources','partition-before.cjs'));fs.copyFileSync(pairPath,path.join(out,'pair.wasm'));
  const rows=[];
  try{
    const a=memory(),b=structuredClone(a);Object.defineProperty(b,'buffer',{value:new SharedArrayBuffer(65536)});
    const previous=await old([a,b]),correct=await partition([a,b]);assert.deepStrictEqual(previous.labels,[0,1]);assert.deepStrictEqual(correct.labels,[0,0]);rows.push({test:'own-buffer-shadow',old:previous.labels,current:correct.labels});
    await assert.rejects(partition([{buffer:new SharedArrayBuffer(65536)}]),TypeError);rows.push({test:'impostor',status:'rejected'});
    const distant=vm.runInNewContext('new WebAssembly.Memory({initial:1,maximum:4,shared:true})');assert.deepStrictEqual((await partition([distant,structuredClone(distant)])).labels,[0,0]);rows.push({test:'cross-realm',status:'ok'});
    const source=memory(),copy=structuredClone(source),oldBuffer=buffer(source);source.grow(1);
    const grown=await partition([source,copy]);assert.deepStrictEqual(grown.labels,[0,0]);rows.push({test:'grow-before-probe',oldBytes:oldBuffer.byteLength,currentBytes:buffer(source).byteLength,cloneBytes:buffer(copy).byteLength});
    const offsetMem=memory();for(const offset of [0,4,65532]){const before=hash(offsetMem);assert.deepStrictEqual((await partition([offsetMem,structuredClone(offsetMem)],{byteOffset:offset})).labels,[0,0]);assert.strictEqual(hash(offsetMem),before);rows.push({test:'offset',offset,status:'ok'});}
    const first=memory(),second=memory(),list=[first,second],pending=partition(list);list[1]=structuredClone(first);const bound=await pending;assert.deepStrictEqual(bound.labels,[0,1]);assert.strictEqual(bound.memories[1],second);assert(Object.isFrozen(bound.memories));
    const mod=new WebAssembly.Module(fs.readFileSync(pairPath));const inst=new WebAssembly.Instance(mod,{env:{a:bound.memories[0],b:bound.memories[1]}});assert.strictEqual(inst.exports.run(31415),0);rows.push({test:'input-list-mutation',status:'captured bindings retained'});
    const worker=new Worker(`const {parentPort}=require('worker_threads');parentPort.on('message',m=>parentPort.postMessage(m));`,{eval:true});
    try{
      for(const p of [[0,0],[0,1],[0,1,0,2,1,2]]){
        const bases=Array.from({length:Math.max(...p)+1},memory),sent=p.map(i=>structuredClone(bases[i])),before=bases.map(hash);
        const received=await new Promise((resolve,reject)=>{worker.once('message',resolve);worker.once('error',reject);worker.postMessage(sent);});
        const result=await partition(received);assert.deepStrictEqual(result.labels,p);assert.deepStrictEqual(bases.map(hash),before);rows.push({test:'worker-roundtrip',partition:p,status:'ok'});
      }
    }finally{await worker.terminate();}
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({rows,node:process.version,note:'Shadowed buffer was a prototype bug, not a runtime vulnerability. Worker is trusted and sends no concurrent notifications.'},null,2));console.log(JSON.stringify({checks:rows.length,rows}));
  }finally{
    const files={};function visit(dir){for(const f of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,f.name);if(f.isDirectory())visit(p);else if(f.name!=='sha256.json')files[path.relative(out,p).replaceAll('\\','/')]=crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}}visit(out);fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(files,null,2));
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
