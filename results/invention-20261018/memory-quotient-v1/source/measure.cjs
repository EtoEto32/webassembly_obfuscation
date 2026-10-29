const fs=require('fs');const file=process.argv[2],inputCount=Number(process.argv[3]);
const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports.run;
let checksum=0;
for(let i=0;i<10000;i++)checksum=(checksum+f(i%inputCount))>>>0;
const samples=[];
for(let k=0;k<9;k++){
  const begin=process.hrtime.bigint();
  for(let i=0;i<20000;i++)checksum=(checksum+f(i%inputCount))>>>0;
  samples.push(Number(process.hrtime.bigint()-begin)/20000);
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,warmup:10000,repetitions:9,
  calls_per_repetition:20000,ns_per_call:samples,maxRSS_KiB:process.resourceUsage().maxRSS,
  linear_memory_bytes:65536,checksum}));
