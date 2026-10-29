// Encode pre-existing real GC references. This measures host oracle cost only.
const fs=require('fs');
const [dir,nText,pattern,mode]=process.argv.slice(2),n=Number(nText);
const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(dir+'/struct-fresh-base-O0.wasm')),{env:{log:()=>{}}});
const values=Array.from({length:n},()=>inst.exports.seed());
const stream=Array.from({length:n},(_,i)=>values[pattern==='shared'?0:pattern==='eight'?i%8:i]);
const source=fs.readFileSync(dir+'/upstream-printed.js','utf8');
const printed=new Function(source+'\nreturn printed;')();
function encode(){
 const result=[],unique=[],map=new WeakMap();let next=0;
 for(const x of stream){
  if(mode==='printed')result.push(printed(x));
  else if(mode==='weak'){
   if(!map.has(x))map.set(x,next++);result.push(map.get(x));
  }else if(mode==='linear'){
   let index=unique.indexOf(x);if(index<0){index=unique.length;unique.push(x);}result.push(index);
  }else throw Error('mode');
 }
 return result;
}
for(let i=0;i<3;i++)encode();
const samples=[];let retained;
for(let i=0;i<9;i++){
 global.gc();const before=process.memoryUsage();const start=process.hrtime.bigint();
 retained=encode();const ns=Number(process.hrtime.bigint()-start);const after=process.memoryUsage();
 samples.push({ns,ns_per_event:ns/n,heap_delta_bytes:after.heapUsed-before.heapUsed,rss_after_bytes:after.rss});
}
console.log(JSON.stringify({node:process.versions,n,pattern,mode,warmup:3,repetitions:9,samples,output_items:retained.length,checksum:retained.reduce((s,x)=>s+(typeof x==='number'?x:x.length),0),process_max_rss_kib:process.resourceUsage().maxRSS}));
