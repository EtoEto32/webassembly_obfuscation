const fs=require('fs');const file=process.argv[2];
const w=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
const verification=String(w.bench(513));w.bench(16384);
let n=1024,elapsed=0;while(true){const t=process.hrtime.bigint();w.bench(n);elapsed=Number(process.hrtime.bigint()-t);if(elapsed>=10000000||n>=2**20)break;n*=2;}
const batches=[];for(let i=0;i<9;i++){const t=process.hrtime.bigint(),checksum=String(w.bench(n)),ns=Number(process.hrtime.bigint()-t);batches.push({n,ns,checksum});}
const values=batches.map(x=>x.ns/x.n).sort((a,b)=>a-b);
console.log(JSON.stringify({file,verification,warmup:16384,batches,medianNs:values[4],node:process.version,v8:process.versions.v8,maxRssKiB:process.resourceUsage().maxRSS,rssBytes:process.memoryUsage().rss}));
