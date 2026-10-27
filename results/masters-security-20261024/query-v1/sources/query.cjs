'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),os=require('os');
const [source,mode,output]=process.argv.slice(2);
const manifest=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))).filter(e=>e.rustOpt==='2'&&!e.binaryenO3);
function val(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;const a=val(e[1],args),b=val(e[2],args);
 if(e[0]==='add')return(a+b)>>>0;if(e[0]==='sub')return(a-b)>>>0;if(e[0]==='and')return(a&b)>>>0;throw Error('expression');}
function union(xs){const out=[];for(const [l,h]of xs.filter(([l,h])=>l<h).sort((a,b)=>a[0]-b[0])){
 const p=out.at(-1);if(p&&p[1]>=l)p[1]=Math.max(p[1],h);else out.push([l,h]);}return out;}
function manual(name,args,base){const[i,v,n]=args;let a,length=1;
 if(name==='fixed')a=16;else if(name==='indexed')a=i&4095;else if(name==='branch')a=(n&1)?i&4095:24;
 else if(name==='metadata')a=4096;else if(name==='helper')a=(i&4095)+4;
 else if(['loop','copy','fill'].includes(name)){a=i&2047;length=n&255;}else throw Error('fixture');
 return length?[[base+a,base+a+length]]:[];}
async function run(e){
 const bytes=fs.readFileSync(path.join(source,e.file));assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),e.sha256);
 let instance,args,base,querySeed=1,answer,oracle,savedBytes,postBytes;
 const nextQueries=()=>{const result=[];for(let j=0;j<16;j++){querySeed^=querySeed<<13;querySeed^=querySeed>>>17;querySeed^=querySeed<<5;result.push((querySeed>>>0)%8192);}return result;};
 instance=(await WebAssembly.instantiate(bytes,{host:{before(){
  const mem=instance.exports.memory,v=new Uint8Array(mem.buffer);let S;
  if(mode==='full'||(mode!=='manual'&&e.summary.kind==='full'))S=[[base,base+8192]];
  else if(mode==='manual')S=manual(e.fixture,args,base);
  else S=union(e.summary.writes.map(w=>{const l=val(w.addr,args)+w.offset;return[Math.max(base,l),Math.min(base+8192,l+val(w.length,args))];}));
  const kept=S.map(([l,h])=>[l,v.slice(l,h)]);savedBytes=kept.reduce((s,x)=>s+x[1].length,0);postBytes=0;
  instance.exports.callback(...args);
  // This caller-side request is obtained only after the callback. The API
  // cannot substitute a precomputed scalar for arbitrary individual bytes.
  const queries=nextQueries(),after=new Uint8Array(mem.buffer);let materialized;
  if(mode==='full')materialized=kept[0][1];
  else if(mode==='materialize'){materialized=after.slice(base,base+8192);for(const[l,b]of kept)materialized.set(b,l-base);postBytes=8192;}
  answer=queries.map(q=>{if(materialized)return materialized[q];const address=base+q;
   for(const[l,b]of kept)if(l<=address&&address<l+b.length)return b[address-l];return after[address];});
  if(oracle)assert.deepEqual(answer,queries.map(q=>oracle[q]));
 }}})).instance;base=instance.exports.buffer_ptr()>>>0;
 function reset(){const v=new Uint8Array(instance.exports.memory.buffer);for(let i=0;i<8192;i++)v[base+i]=(i*7+17)&255;querySeed=20261024;}
 let seed=20261024;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const inputs=[[0,0,0],[0,255,1],[4095,255,255],[4096,1,256],[8191,128,511],[0xffffffff,255,0xffffffff],[0,0xffffffff,32],[2047,15,128]];
 for(let i=0;i<128;i++)inputs.push([rand(),rand(),rand()]);let retained=0,post=0;
 reset();for(args of inputs){oracle=new Uint8Array(instance.exports.memory.buffer).slice(base,base+8192);instance.exports.drive();retained+=savedBytes;post+=postBytes;}oracle=null;
 reset();for(let i=0;i<100;i++){args=inputs[i%136];instance.exports.drive();}
 const samples=[],checksums=[];
 for(let batch=0;batch<9;batch++){reset();let check=0;const begin=process.hrtime.bigint();
  for(let i=0;i<300;i++){args=inputs[i%136];instance.exports.drive();for(const x of answer)check=(Math.imul(check,33)+x)>>>0;}
  samples.push(Number(process.hrtime.bigint()-begin)/300/1000);checksums.push(check);}
 return{fixture:e.fixture,file:e.file,samples_us:samples,checksums,inputCount:136,retainedPayloadBytes:retained,postCallbackPayloadBytes:post};
}
(async()=>{
 assert(['full','materialize','segments','manual'].includes(mode));
 const a=Uint8Array.from([1,2]),b=Uint8Array.from([2,1]);
 assert.equal(a.reduce((s,v)=>s+v,0),b.reduce((s,v)=>s+v,0));assert.notEqual(a[0],b[0]);
 const entries=[];for(const e of manifest)entries.push(await run(e));
 fs.writeFileSync(output,JSON.stringify({mode,node:process.version,platform:process.platform,cpu:os.cpus()[0].model,
  warmup:100,callsPerBatch:300,batches:9,queryCount:16,scalarChecksumCounterexample:{a:[...a],b:[...b],query:0},
  memoryUsage:process.memoryUsage(),resourceUsage:process.resourceUsage(),entries},null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
