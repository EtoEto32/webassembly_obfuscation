const fs=require('fs'),file=process.argv[2],e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
const mem=new Uint8Array(e.__physical.buffer),initial=mem.slice(),reset=()=>mem.set(initial);
reset();const verification=e.__bench(513)>>>0;reset();e.__bench(16384);
let n=256,elapsed=0;while(true){reset();const t=process.hrtime.bigint();e.__bench(n);elapsed=Number(process.hrtime.bigint()-t);if(elapsed>=1e7||n>=2**22)break;n*=2;}
const batches=[];for(let i=0;i<9;i++){reset();const t=process.hrtime.bigint(),checksum=e.__bench(n)>>>0,ns=Number(process.hrtime.bigint()-t);batches.push({n,ns,checksum});}
const sorted=batches.map(x=>x.ns/x.n).sort((a,b)=>a-b);
console.log(JSON.stringify({file,verification,batches,medianNs:sorted[4],warmup:16384,maxRssKiB:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
