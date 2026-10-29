'use strict';
function load(bytes){
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
  const now=1700000000500;view.setInt32(ptr,Math.floor(now/1000),true);view.setUint16(ptr+4,now%1000,true);
  view.setInt16(ptr+6,0,true);view.setInt16(ptr+8,0,true);return 0;
 }),
 _gmtime:track('_gmtime',ptr=>{
  const d=new Date(view.getInt32(ptr,true)*1000),jan=Date.UTC(d.getUTCFullYear(),0,1);
  const values=[d.getUTCSeconds(),d.getUTCMinutes(),d.getUTCHours(),d.getUTCDate(),d.getUTCMonth(),
   d.getUTCFullYear()-1900,d.getUTCDay(),Math.floor((Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate())-jan)/86400000),0,0,0];
  values.forEach((v,i)=>view.setInt32(tm+i*4,v,true));return tm;
 })};

const exports=new WebAssembly.Instance(new WebAssembly.Module(bytes),{env}).exports;
view.setUint32(dynamicPtr,heapTop,true);
const ctx=exports._cryptonight_create(),input=exports._malloc(256),output=exports._malloc(32);
if(!ctx||!input||!output)throw Error('Allocation failed');
return {calls,layout:{dynamicPtr,stackTop,heapTop,tm,ctx,input,output},
 hash(v){const b=Buffer.from(v.hex,'hex');new Uint8Array(memory.buffer).set(b,input);
 exports._cryptonight_hash_variant_0(ctx,input,output,b.length);},
 output(){return Buffer.from(memory.buffer,output,32).toString('hex');},
 close(){exports._cryptonight_destroy(ctx);}};
}
module.exports={load};
