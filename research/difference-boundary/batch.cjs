const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const kinds=['near','far','tail','digest','paired'];let sink=0,rows=[];
for(let kind=0;kind<5;kind++){
 const warmup=2000,count=kind===3||kind===4?1000:2000;
 sink^=e.bench(kind,warmup);let samples=[];
 for(let r=0;r<11;r++){let t=process.hrtime.bigint();sink^=e.bench(kind,count);samples.push(Number(process.hrtime.bigint()-t)/count);}
 rows.push({scenario:kinds[kind],warmup,calls_per_sample:count,samples_ns:samples,median_ns:[...samples].sort((a,b)=>a-b)[5]});
}
console.log(JSON.stringify({rows,sink,maxRSS_KiB:process.resourceUsage().maxRSS}));
