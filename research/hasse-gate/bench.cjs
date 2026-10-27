const fs=require('node:fs');
const file=process.argv[2];
const b=fs.readFileSync(file);
const run=new WebAssembly.Instance(new WebAssembly.Module(b)).exports.bench;
const seed=0x621021a7;
const verification=run(4096,seed)>>>0;
run(65536,seed);
function measure(n){const t=process.hrtime.bigint();const checksum=run(n,seed)>>>0;return {n,ns:Number(process.hrtime.bigint()-t),checksum};}
let n=1024,calibration;
while(true){calibration=measure(n);if(calibration.ns>=5e6||n>=2**23)break;n*=2;}
const batches=Array.from({length:9},()=>measure(n));
if(batches.some(x=>x.checksum!==calibration.checksum))throw Error('unstable checksum');
const sorted=batches.map(x=>x.ns/x.n).sort((a,b)=>a-b);
console.log(JSON.stringify({file,node:process.version,v8:process.versions.v8,verification,warmup:65536,targetNs:5e6,cap:2**23,
 batches,medianNs:sorted[4],rangeNs:[sorted[0],sorted[8]],rssBytes:process.memoryUsage().rss,maxRssKiB:process.resourceUsage().maxRSS,
 note:'Wasm loop includes input updates, checksum and calls. One JS call per batch. Compilation excluded.'}));
