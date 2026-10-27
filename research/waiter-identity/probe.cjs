'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto'),{partition,Inconclusive}=require('./partition.cjs');
const root=process.argv[2],hash=m=>crypto.createHash('sha256').update(new Uint8Array(m.buffer)).digest('hex');
function* partitions(n,p=[0]){if(p.length===n){yield p;return;}for(let v=0;v<=Math.max(...p)+1;v++)yield*partitions(n,[...p,v]);}
function make(p){const base=Array.from({length:Math.max(...p)+1},()=>new WebAssembly.Memory({initial:1,maximum:4,shared:true}));return {base,memories:p.map(i=>structuredClone(base[i]))};}
async function main(){
  let cases=0,hashChecks=0,identityFailures=0,registrations=0,notifications=0;const counts=[];
  for(let n=1;n<=6;n++){
    let count=0;for(const p of partitions(n)){
      const {base,memories}=make(p),before=base.map(hash);const got=await partition(memories);assert.deepStrictEqual(got.labels,p);assert.strictEqual(got.registrations,n);assert.strictEqual(got.notifications,base.length);registrations+=got.registrations;notifications+=got.notifications;
      assert.deepStrictEqual(base.map(hash),before);hashChecks+=base.length;assert(memories.every((m,i)=>memories.indexOf(m)===i));if(base.length<n)identityFailures++;cases++;count++;
    }counts.push({n,partitions:count});
  }
  let state=2026102415;function rand(n){state=(Math.imul(state,1664525)+1013904223)>>>0;return state%n;}
  const larger=[];
  for(const n of [8,16,32,64])for(const k of [1,2,4]){
    const p=[0];for(let i=1;i<n;i++)p.push(rand(Math.min(k,Math.max(...p)+2)));
    const {base,memories}=make(p),before=base.map(hash),got=await partition(memories);assert.deepStrictEqual(got.labels,p);assert.deepStrictEqual(base.map(hash),before);hashChecks+=base.length;cases++;larger.push({n,classes:base.length,registrations:got.registrations,notifications:got.notifications});
  }
  const module=new WebAssembly.Module(fs.readFileSync(path.join(root,'pair.wasm'))),guard=[];
  for(const p of [[0,0],[0,1]])for(const clone of [false,true]){
    const setup=make(p),m=clone?setup.memories:p.map(i=>setup.base[i]),got=await partition(m);const inst=new WebAssembly.Instance(module,{env:{a:m[0],b:m[1]}});const value=inst.exports.run(123456);
    assert.strictEqual(value,p[0]===p[1]?123456:0);guard.push({p,clone,identityAccept:m[0]!==m[1],partitionAccept:got.labels[0]!==got.labels[1],registryAccept:p[0]!==p[1],value});
  }
  const negative=[];
  for(const [name,m,options] of [['unshared',[new WebAssembly.Memory({initial:1})],{}],['zero-length',[new WebAssembly.Memory({initial:0,maximum:1,shared:true})],{}],['unaligned',make([0]).memories,{byteOffset:1}],['outside',make([0]).memories,{byteOffset:65536}]]){
    await assert.rejects(partition(m,options),TypeError);negative.push({name,status:'rejected'});
  }
  const {memories}=make([0]),view=new Int32Array(memories[0].buffer),foreign=Atomics.waitAsync(view,0,0);
  await assert.rejects(partition(memories,{deadlineMs:100}),Inconclusive);assert.strictEqual(await foreign.value,'ok');negative.push({name:'foreign-waiter',status:'inconclusive',note:'Foreign waiter was awakened; exclusivity is essential, not automatically enforced.'});
  const report={cases,hashChecks,identityFailures,registrations,notifications,counts,larger,guard,negative,node:process.version,v8:process.versions.v8,seed:2026102415,memory:process.memoryUsage(),scope:'Fresh private test memories, quiescent synchronization locations. No defense against concurrently malicious peers.'};fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({cases,hashChecks,identityFailures,counts,guard,negative}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
