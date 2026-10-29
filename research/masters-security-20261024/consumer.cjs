'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),os=require('os');
const [source,mode,output]=process.argv.slice(2);
const manifest=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))).filter(e=>e.rustOpt==='2'&&!e.binaryenO3);
function val(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;
 const a=val(e[1],args),b=val(e[2],args);if(e[0]==='add')return(a+b)>>>0;if(e[0]==='sub')return(a-b)>>>0;if(e[0]==='and')return(a&b)>>>0;throw Error('expression');}
function union(xs){const out=[];for(const [l,h]of xs.filter(([l,h])=>l<h).sort((a,b)=>a[0]-b[0])){
 const p=out.at(-1);if(p&&p[1]>=l)p[1]=Math.max(p[1],h);else out.push([l,h]);}return out;}
function manual(name,args,base){const [i,v,n]=args;let a,length=1;
 if(name==='fixed')a=16;else if(name==='indexed')a=i&4095;else if(name==='branch')a=(n&1)?i&4095:24;
 else if(name==='metadata')a=4096;else if(name==='helper')a=(i&4095)+4;
 else if(['loop','copy','fill'].includes(name)){a=i&2047;length=n&255;}else throw Error('fixture');
 return length?[[base+a,base+a+length]]:[];}
function checksum(v,l=0,h=v.length){let s=0;for(let i=l;i<h;i++)s=(s+v[i])>>>0;return s;}
async function run(e){
 const bytes=fs.readFileSync(path.join(source,e.file));assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),e.sha256);
 let instance,args,base,answer=0,savedBytes=0,materializedBytes=0;
 instance=(await WebAssembly.instantiate(bytes,{host:{before(){
  const memory=instance.exports.memory,v=new Uint8Array(memory.buffer);
  if(mode==='hoisted'){const old=checksum(v,base,base+8192);savedBytes=4;materializedBytes=0;
   instance.exports.callback(...args);answer=old;return;}
  let S;if(mode==='full'||(mode!=='manual'&&e.summary.kind==='full'))S=[[base,base+8192]];
  else if(mode==='manual')S=manual(e.fixture,args,base);
  else S=union(e.summary.writes.map(w=>{const l=val(w.addr,args)+w.offset;return[Math.max(base,l),Math.min(base+8192,l+val(w.length,args))];}));
  const kept=S.map(([l,h])=>[l,v.slice(l,h)]);savedBytes=kept.reduce((s,x)=>s+x[1].length,0);materializedBytes=0;
  instance.exports.callback(...args);
  if(mode==='full'){answer=checksum(kept[0][1]);return;}
  const after=new Uint8Array(memory.buffer);
  if(mode==='materialize'){const view=after.slice(base,base+8192);materializedBytes=view.length;
   for(const [l,b]of kept)view.set(b,l-base);answer=checksum(view);return;}
  let s=0,pos=base;for(const [l,b]of kept){s=(s+checksum(after,pos,l)+checksum(b))>>>0;pos=l+b.length;}
  answer=(s+checksum(after,pos,base+8192))>>>0;
 }}})).instance;
 base=instance.exports.buffer_ptr()>>>0;
 function reset(){const v=new Uint8Array(instance.exports.memory.buffer);for(let i=0;i<8192;i++)v[base+i]=(i*7+17)&255;}
 let seed=20261024;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const inputs=[[0,0,0],[0,255,1],[4095,255,255],[4096,1,256],[8191,128,511],[0xffffffff,255,0xffffffff],[0,0xffffffff,32],[2047,15,128]];
 for(let i=0;i<128;i++)inputs.push([rand(),rand(),rand()]);
 let retained=0,post=0;
 for(args of inputs){reset();const oracle=checksum(new Uint8Array(instance.exports.memory.buffer),base,base+8192);instance.exports.drive();assert.equal(answer,oracle);retained+=savedBytes;post+=materializedBytes;}
 reset();for(let i=0;i<100;i++){args=inputs[i%inputs.length];instance.exports.drive();}
 const samples=[],checksums=[];
 for(let batch=0;batch<9;batch++){
  reset();let check=0;const begin=process.hrtime.bigint();
  for(let i=0;i<300;i++){args=inputs[i%inputs.length];instance.exports.drive();check=(check+answer)>>>0;}
  samples.push(Number(process.hrtime.bigint()-begin)/300/1000);checksums.push(check);
 }
 return{fixture:e.fixture,file:e.file,summaryKind:e.summary.kind,samples_us:samples,checksums,
  inputCount:inputs.length,retainedPayloadBytes:retained,postCallbackPayloadBytes:post};
}
(async()=>{assert(['full','materialize','segments','manual','hoisted'].includes(mode));const entries=[];
 for(const e of manifest)entries.push(await run(e));
 fs.writeFileSync(output,JSON.stringify({mode,node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0].model,warmup:100,callsPerBatch:300,batches:9,
  memoryUsage:process.memoryUsage(),resourceUsage:process.resourceUsage(),entries},null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
