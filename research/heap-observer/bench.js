const fs=require('fs'),{heapSnapshot}=require('./observe.js');
const [binary,observer,metadata,mode,n]=process.argv.slice(2);
const target=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(binary))).exports;
const helper=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(observer))).exports;
const meta=JSON.parse(fs.readFileSync(metadata,'utf8'));const root=target.get(),N=Number(n),repeats=100;
function operation(){
  if(mode==='boundary'){
    const ids=new Map(),roots=[root,root].map(x=>{if(!ids.has(x))ids.set(x,ids.size);return {ref:ids.get(x)};});
    return JSON.stringify({roots});
  }
  if(mode.startsWith('manual')){
    const length=helper.len_0(root),limit=mode==='manualcap8'?8:Math.max(N,8),fields=[];
    for(let i=0;i<Math.min(length,limit);i++)fields.push(helper.get_0_0(root,i));
    const rec={id:0,type:0,kind:'array',fields,length};if(length>limit)rec.truncated=length-limit;
    return JSON.stringify({roots:[{ref:0},{ref:0}],objects:[rec],truncations:length>limit?1:0});
  }
  return JSON.stringify(heapSnapshot([root,root],helper,meta,{nodes:32,elements:mode==='cap8'?8:Math.max(N,8)}));
}
if(mode.startsWith('manual')){
  const expected=JSON.stringify(heapSnapshot([root,root],helper,meta,{nodes:32,elements:mode==='manualcap8'?8:Math.max(N,8)}));
  if(operation()!==expected)throw new Error('manual baseline differs');
}
let sink=0;
function sample(){const t=process.hrtime.bigint();for(let i=0;i<repeats;i++)sink+=operation().length;return Number(process.hrtime.bigint()-t)/repeats;}
for(let i=0;i<3;i++)sample();
global.gc();const before=process.memoryUsage();const samples=[];for(let i=0;i<9;i++)samples.push(sample());const after=process.memoryUsage();
console.log(JSON.stringify({mode,n:N,warmups:3,samples,repeats,output_bytes:operation().length,heap_delta:after.heapUsed-before.heapUsed,rss:after.rss,sink,node:process.version,v8:process.versions.v8}));
