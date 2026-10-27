'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const out=path.resolve(process.argv[2]);
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
function evaluate(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;
 const a=evaluate(e[1],args),b=evaluate(e[2],args);if(e[0]==='add')return(a+b)>>>0;
 if(e[0]==='sub')return(a-b)>>>0;if(e[0]==='and')return(a&b)>>>0;throw Error('unsupported expression');}
function union(xs){const out=[];for(const [l,h] of xs.filter(([l,h])=>l<h).sort((a,b)=>a[0]-b[0])){
 const p=out.at(-1);if(p&&p[1]>=l)p[1]=Math.max(p[1],h);else out.push([l,h]);}return out;}
async function check(e){
 const bytes=fs.readFileSync(path.join(out,e.file));assert(WebAssembly.validate(bytes));
 assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),e.sha256);
 let instance,args,depth=0,base,rows=[];
 const host={before(){
  assert.equal(depth++,0);const v=new Uint8Array(instance.exports.memory.buffer),oracle=v.slice(base,base+8192);
  const S=e.summary.kind==='full'?[[base,base+8192]]:union(e.summary.writes.map(w=>{
   const l=evaluate(w.addr,args)+w.offset;return[Math.max(base,l),Math.min(base+8192,l+evaluate(w.length,args))];}));
  const saved=S.map(([l,h])=>[l,v.slice(l,h)]);
  instance.exports.callback(...args);
  const after=new Uint8Array(instance.exports.memory.buffer),view=after.slice(base,base+8192);
  let changed=0;for(let j=0;j<8192;j++)if(view[j]!==oracle[j])changed++;
  for(const [l,b]of saved)view.set(b,l-base);assert.deepEqual(view,oracle,e.file);
  rows.push({args,savedBytes:saved.reduce((n,x)=>n+x[1].length,0),changedBytes:changed});depth--;
 }};
 if(e.summary.kind==='reject')return{file:e.file,kind:'reject',reason:e.summary.reason,cases:0};
 instance=(await WebAssembly.instantiate(bytes,{host})).instance;base=instance.exports.buffer_ptr()>>>0;
 assert(base+8192<=instance.exports.memory.buffer.byteLength);
 let seed=20261024;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const inputs=[[0,0,0],[0,255,1],[4095,255,255],[4096,1,256],[8191,128,511],[0xffffffff,255,0xffffffff],[0,0xffffffff,32],[2047,15,128]];
 for(let i=0;i<128;i++)inputs.push([rand(),rand(),rand()]);
 for(args of inputs){const v=new Uint8Array(instance.exports.memory.buffer);for(let j=0;j<8192;j++)v[base+j]=(j*7+17)&255;
  instance.exports.drive();assert.equal(depth,0);}
 return{file:e.file,kind:e.summary.kind,reason:e.summary.reason||null,cases:rows.length,mismatches:0,
   savedBytes:rows.reduce((s,x)=>s+x.savedBytes,0),fullBytes:rows.length*8192,changedBytes:rows.reduce((s,x)=>s+x.changedBytes,0),rows};
}
(async()=>{const entries=[];for(const e of manifest)entries.push(await check(e));
 const result={scope:'self-authored Rust compiler coverage; no third-party application benchmark',entries,
   modules:entries.length,ranges:entries.filter(x=>x.kind==='ranges').length,full:entries.filter(x=>x.kind==='full').length,
   cases:entries.reduce((s,x)=>s+x.cases,0),mismatches:0};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,entries:undefined}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
