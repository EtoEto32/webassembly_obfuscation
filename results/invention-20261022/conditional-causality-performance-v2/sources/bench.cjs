const fs=require('node:fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const elapsed=count=>{const t=process.hrtime.bigint();const checksum=e.bench(count,123,987)|0;return {ms:Number(process.hrtime.bigint()-t)/1e6,checksum};};
e.bench(16384,123,987);
let count=1024,pilot=[];
while(true){const t=elapsed(count);pilot.push({count,...t});if(t.ms>=20||count>=67108864)break;count*=2;}
const batches=Array.from({length:7},()=>elapsed(count));
if(new Set(batches.map(b=>b.checksum)).size!==1)throw Error('Nondeterministic benchmark checksum');
console.log(JSON.stringify({warmup:16384,count,pilot,batches,ns_per_call:batches.map(b=>b.ms*1e6/count),max_rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
