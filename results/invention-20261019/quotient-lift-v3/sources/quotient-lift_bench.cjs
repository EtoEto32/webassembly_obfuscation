const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const b=new Uint8Array(e.memory.buffer);let rng=20261019;
for(let i=0;i<1024;i++){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;b[i]=rng&255;}
let sink=0;for(let i=0;i<10000;i++)sink^=e.run(i%512,64);
const ns=[];for(let r=0;r<11;r++){const begin=process.hrtime.bigint();for(let i=0;i<3000;i++)sink^=e.run(i%512,64);ns.push(Number(process.hrtime.bigint()-begin)/3000);}
ns.sort((a,b)=>a-b);
console.log(JSON.stringify({median_ns:ns[5],samples_ns:ns,warmup:10000,repetitions:11,calls_per_sample:3000,length:64,maxRSS_KiB:process.resourceUsage().maxRSS,sink,node:process.version,v8:process.versions.v8}));
