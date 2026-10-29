const fs=require('node:fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const call=n=>{const t=process.hrtime.bigint();const checksum=e.bench(n,0x41b3917)|0;return {ms:Number(process.hrtime.bigint()-t)/1e6,checksum};};
e.bench(32,0x41b3917);
let count=1,pilot=[];
for(;;){const t=call(count);pilot.push({count,...t});if(t.ms>=20||count>=1048576)break;count*=2;}
const batches=Array.from({length:7},()=>call(count));
if(new Set(batches.map(x=>x.checksum)).size!==1)throw Error('Checksum not deterministic');
console.log(JSON.stringify({warmup:32,count,pilot,batches,ns_per_call:batches.map(b=>b.ms*1e6/count),max_rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
