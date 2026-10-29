const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
let seed=20261019,inputs=new Int32Array(3072),sink=0;
for(let i=0;i<inputs.length;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;inputs[i]=seed;}
function call(i){const j=(i%1024)*3;return e.run(inputs[j],inputs[j+1],inputs[j+2]);}
for(let i=0;i<10000;i++)sink^=call(i);
const ns=[];for(let r=0;r<11;r++){const t=process.hrtime.bigint();for(let i=0;i<3000;i++)sink^=call(i);ns.push(Number(process.hrtime.bigint()-t)/3000);}
ns.sort((a,b)=>a-b);
console.log(JSON.stringify({median_ns:ns[5],samples_ns:ns,maxRSS_KiB:process.resourceUsage().maxRSS,warmup:10000,repetitions:11,calls_per_sample:3000,sink}));
