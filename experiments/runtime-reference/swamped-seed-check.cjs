'use strict';
// Recovered old Emscripten host ABI. No website, demo main, or network is used.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {performance}=require('perf_hooks');
const {read,save}=require('./proof-glue-controls.cjs');
const benchmark=process.argv.includes('--benchmark');
const root='/work', out=path.join(root,'results/runtime-mining/cross-dataset/swamped/046dc081-'+(benchmark?'repeated-throughput':'public-vector-check')+'.json');
const sha='046dc081076d9cea6831967619b862cc80fa8c2381346406ec639c899cda640f';
const bytes=read(path.join(root,'data/objects/'+sha+'.bin'));
if(crypto.createHash('sha256').update(bytes).digest('hex')!==sha)throw Error('Digest mismatch');
const vectors=JSON.parse(read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'))).vectors;
const memory=new WebAssembly.Memory({initial:256,maximum:256});
const table=new WebAssembly.Table({element:'anyfunc',initial:8,maximum:8});
const view=new DataView(memory.buffer), tm=0x21000, dynamicPtr=0x20000, stackTop=0x100000, heapTop=0x600000;
const calls={};
const track=(name,fn)=>(...args)=>{calls[name]=(calls[name]||0)+1;return fn(...args);};
const fail=name=>track(name,()=>{throw Error('Unsupported or failing host call: '+name);});
const env={memory,table,tableBase:0,DYNAMICTOP_PTR:dynamicPtr,STACKTOP:stackTop,
 abort:fail('abort'),enlargeMemory:fail('enlargeMemory'),abortOnCannotGrowMemory:fail('abortOnCannotGrowMemory'),
 getTotalMemory:track('getTotalMemory',()=>memory.buffer.byteLength),
 ___setErrNo:fail('___setErrNo'),
 ___syscall20:track('___syscall20',which=>{if(which!==20)throw Error('Unexpected syscall');return process.pid;}),
 _emscripten_memcpy_big:track('_emscripten_memcpy_big',(dst,src,n)=>{
  if(Math.min(dst,src,n)<0||Math.max(dst+n,src+n)>memory.buffer.byteLength)throw Error('Memcpy bounds');
  new Uint8Array(memory.buffer).copyWithin(dst,src,src+n);return dst;
 }),
 _ftime:track('_ftime',ptr=>{
  const now=Date.now();view.setInt32(ptr,Math.floor(now/1000),true);view.setUint16(ptr+4,now%1000,true);
  view.setInt16(ptr+6,0,true);view.setInt16(ptr+8,0,true);return 0;
 }),
 _gmtime:track('_gmtime',ptr=>{
  const d=new Date(view.getInt32(ptr,true)*1000),jan=Date.UTC(d.getUTCFullYear(),0,1);
  const values=[d.getUTCSeconds(),d.getUTCMinutes(),d.getUTCHours(),d.getUTCDate(),d.getUTCMonth(),
   d.getUTCFullYear()-1900,d.getUTCDay(),Math.floor((Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate())-jan)/86400000),0,0,0];
  values.forEach((v,i)=>view.setInt32(tm+i*4,v,true));return tm;
 })};
const report={sha256:sha,algorithm:'cn/0',node:process.version,v8:process.versions.v8,
 image_id:process.env.EXPERIMENT_IMAGE_ID||null,
 script_sha256:crypto.createHash('sha256').update(read(__filename)).digest('hex'),
 host:'Recovered Emscripten imports; source-generated JS was not supplied with this seed',
 reference:'XMRig v6.18.0 CryptoNight_test.h',
 memory_layout:{pages:256,dynamicPtr,stackTop,heapTop,tm},results:[],calls,
 limitations:['Finite public vectors only.','Host layout differs from missing original JavaScript.',
 'Not an obfuscation pair or proof of malware provenance.']};
try{
 const module=new WebAssembly.Module(bytes), exports=new WebAssembly.Instance(module,{env}).exports;
 view.setUint32(dynamicPtr,heapTop,true);
 const ctx=exports._cryptonight_create(),input=exports._malloc(256),output=exports._malloc(32);
 if(!ctx||!input||!output)throw Error('Allocation failed');
 report.context=ctx;report.input=input;report.output=output;
 for(const v of vectors){
  const b=Buffer.from(v.hex,'hex');new Uint8Array(memory.buffer).set(b,input);
  exports._cryptonight_hash_variant_0(ctx,input,output,b.length);
  const actual=Buffer.from(memory.buffer,output,32).toString('hex');
  report.results.push({id:v.id,expected:v.expected,actual,matches:actual===v.expected});
 }
 report.status=report.results.every(r=>r.matches)?'all public vectors matched':'output mismatch';
 if(benchmark){
  if(report.status!=='all public vectors matched')throw Error('Cannot benchmark unvalidated output');
  report.benchmark={warmup_seconds:3,seconds_per_block:30,repetitions:3,workers:1,samples:[]};
  const hash=v=>{const b=Buffer.from(v.hex,'hex');new Uint8Array(memory.buffer).set(b,input);
   exports._cryptonight_hash_variant_0(ctx,input,output,b.length);};
  for(let repetition=1;repetition<=3;repetition++){
   let n=0,t=performance.now();while(performance.now()-t<3000)hash(vectors[n++%vectors.length]);
   n=0;t=performance.now();do{hash(vectors[n++%vectors.length]);}while(performance.now()-t<30000);
   const elapsed=performance.now()-t,last=vectors[(n-1)%vectors.length];
   const matches=Buffer.from(memory.buffer,output,32).toString('hex')===last.expected;
   const sample={repetition,count:n,elapsed_ms:elapsed,hashes_per_second:1000*n/elapsed,
    final_output_matches:matches,finished_utc:new Date().toISOString()};
   report.benchmark.samples.push(sample);save(out,report);console.log(JSON.stringify(sample));
   if(!matches)throw Error('Measured hash mismatch');
  }
 }
 exports._cryptonight_destroy(ctx);
}catch(e){report.status='failed';report.error=String(e.stack||e);}
report.finished_utc=new Date().toISOString();save(out,report);console.log(JSON.stringify(report));
