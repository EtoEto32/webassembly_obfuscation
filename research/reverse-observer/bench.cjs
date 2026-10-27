const fs=require('node:fs'),os=require('node:os');
const target=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[3])),{target}).exports;
let word=123,expected=0;
for(let i=0;i<11;i++){word=(Math.imul(word,1664525)+1013904223)>>>0;expected=((expected<<1)^target.run(word,32))>>>0;}
const observed=e.bench(11,123)>>>0;if(observed!==expected)throw Error('benchmark checksum mismatch');
let sink=0;
function sample(n){const t=process.hrtime.bigint();sink^=e.bench(n,123);return Number(process.hrtime.bigint()-t);}
sample(1024);let n=256;
while(sample(n)<15e6&&n<2**20)n*=2;
const batches=Array.from({length:7},()=>{const ns=sample(n);return {n,ns,ns_per_word:ns/n};});
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,flags:process.execArgv,
 warmup:1024,input_bits:32,initial_seed:123,batches,sink,verification:{expected,observed},linear_memory_bytes:0,max_rss_kib:process.resourceUsage().maxRSS}));
