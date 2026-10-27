const fs=require('fs');
const run=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.run;
let sink=0;
for(let i=0;i<50000;i++)sink=(Math.imul(sink,33)+run(i*71717,i*13331))|0;
const samples=[];
for(let r=0;r<11;r++){
 const begin=process.hrtime.bigint();
 for(let i=0;i<20000;i++)sink=(Math.imul(sink,33)+run((i+r*20000)*71717,(i+r*20000)*13331))|0;
 samples.push(Number(process.hrtime.bigint()-begin)/20000);
}
const sorted=[...samples].sort((a,b)=>a-b);
console.log(JSON.stringify({median_ns:sorted[5],samples_ns:samples,maxRSS_KiB:process.resourceUsage().maxRSS,warmup:50000,calls_per_sample:20000,repetitions:11,sink}));
