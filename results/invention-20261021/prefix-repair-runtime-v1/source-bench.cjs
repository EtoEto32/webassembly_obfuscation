const fs=require('node:fs');
const file=process.argv[2];
const b=fs.readFileSync(file),e=new WebAssembly.Instance(new WebAssembly.Module(b)).exports;
const initial=e.digest()>>>0,verification=e.bench(17)>>>0;
e.bench(65536);
function measure(n){const t=process.hrtime.bigint();const checksum=e.bench(n)>>>0;return {n,ns:Number(process.hrtime.bigint()-t),checksum};}
let n=1024,calibration;
while(true){calibration=measure(n);if(calibration.ns>=5e6||n>=2**22)break;n*=2;}
const batches=Array.from({length:9},()=>measure(n)),sorted=batches.map(x=>x.ns/x.n).sort((a,b)=>a-b);
console.log(JSON.stringify({file,node:process.version,v8:process.versions.v8,initial,verification,warmup:65536,targetNs:5e6,cap:2**22,
 batches,medianNs:sorted[4],rangeNs:[sorted[0],sorted[8]],maxRssKiB:process.resourceUsage().maxRSS,rssBytes:process.memoryUsage().rss,
 note:'Normal path only. Repeated copy region, one digest at batch end. Memory evolves across batches; checksum need not be constant.'}));
