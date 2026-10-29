'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const dir=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function inst(file){return new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file)))).exports;}
function decoded(mem,encoded){
  const out=Buffer.from(new Uint8Array(mem.buffer));
  if(encoded){
    const steps=[[3,0,1,23],[2,3,0,17],[1,2,3,11],[0,1,2,5]];
    for(let at=0;at<out.length;at+=16){
      const a=[0,1,2,3].map(i=>out.readUInt32LE(at+4*i));
      for(const [i,j,k,n]of steps){const v=(a[j]+a[k])>>>0;a[i]=(a[i]^((v<<n)|(v>>>(32-n))))>>>0;}
      for(let i=0;i<4;i++)out.writeUInt32LE(a[i],at+4*i);
    }
  }
  return out;
}
function call(e,name,args){try{let x=e[name](...args);return {trap:false,value:typeof x==='bigint'?x.toString():x??null};}catch(x){if(!(x instanceof WebAssembly.RuntimeError))throw x;return {trap:true};}}
let rnd=211062;function rand(){rnd=(Math.imul(rnd,1664525)+1013904223)>>>0;return rnd;}
const traces={};
for(const pages of [0,1,2]){
  const n=pages*65536, trace=[];
  const ptr=[0,1,7,8,9,12,13,14,15,16,17,31,32,63,64,65520,65528,65529,65532,65533,65535,65536,n-16,n-8,n-7,n-4,n-3,n-1,n,n+1,0x7fffffff,0xfffffff0,0xfffffffc,0xffffffff].map(x=>x>>>0);
  for(let i=0;i<64;i++)ptr.push(rand()%(Math.max(n,1)+32));
  for(const t of ['i32','i64'])for(const w of [1,2,4,8]){
    const max=Number(t.slice(1))/8;if(w>max)continue;
    for(const a of ptr){
      const x=t==='i32'?rand()|0:BigInt.asIntN(64,(BigInt(rand())<<32n)|BigInt(rand()));
      trace.push([`${t}_st${w}`,[a,x]]);
      for(const sign of w===max?['']:['s','u'])trace.push([`${t}_ld${w}${sign}`,[a]]);
    }
  }
  for(let x=0;x<256;x++){trace.push(['i32_st1',[48,x]],['i32_ld1s',[48]],['i32_ld1u',[48]]);}
  for(const a of [0,1,4,8,0xffffffff,n-3,n-1])for(const name of ['offset_store','offset_load','effects','prefix'])trace.push([name,name==='offset_load'?[a>>>0]:[a>>>0,0x12345678]]);
  if(pages)for(const off of [0,7,13,15])trace.push(['bench',[257,off]]);
  traces[pages]=trace;
}
const reports=[];let calls=0,traps=0,positiveMismatches=0;
for(const row of rows){
  const src=inst(`p${row.pages}.plain.raw.probe.wasm`),target=inst(row.probe),enc=!['plain','lifted'].includes(row.mode),negative=row.mode.startsWith('bad-');
  let mismatches=0,ct=0,initial=decoded(target.__physical,enc).equals(decoded(src.__physical,false)),first=null;
  assert(initial,'initial memory');
  for(const [name,args]of traces[row.pages]){
    const a=call(src,name,args),b=call(target,name,args);ct+=Number(a.trap);
    const sameValue=JSON.stringify(a)===JSON.stringify(b),sameMemory=decoded(src.__physical,false).equals(decoded(target.__physical,enc));
    if(!sameValue||!sameMemory){mismatches++;if(!first)first={name,args:args.map(x=>typeof x==='bigint'?x.toString():x),expected:a,actual:b,sameMemory};}
  }
  reports.push({file:row.file,negative,calls:traces[row.pages].length,expectedTraps:ct,mismatches,first});calls+=traces[row.pages].length;traps+=ct;
  if(!negative)positiveMismatches+=mismatches;
}
const positive=reports.filter(r=>!r.negative),negative=reports.filter(r=>r.negative);
const result={node:process.version,v8:process.versions.v8,seed:211062,targets:reports.length,positiveTargets:positive.length,positiveCalls:positive.reduce((a,b)=>a+b.calls,0),positiveExpectedTraps:positive.reduce((a,b)=>a+b.expectedTraps,0),positiveMismatches,negativeTargets:negative.length,negativeWithWitness:negative.filter(r=>r.mismatches).length,rows:reports};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
fs.writeFileSync(path.join(dir,'traces.json'),JSON.stringify(traces,(_,v)=>typeof v==='bigint'?{i64:v.toString()}:v,2));
assert.equal(positiveMismatches,0);for(const mode of ['bad-partial','bad-wrap'])assert(negative.some(r=>r.file.includes(mode)&&r.mismatches),'negative '+mode);
console.log(JSON.stringify({...result,rows:undefined}));
