const fs=require('fs');const ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
function once(n){const t=process.hrtime.bigint(),sum=ex.bench(n);return [Number(process.hrtime.bigint()-t),sum];}
ex.bench(128);let n=64;while(n<1048576&&once(n)[0]<5000000)n*=2;
const ns=[],checksums=[];for(let k=0;k<9;k++){const [t,s]=once(n);ns.push(t/n);checksums.push(s);}
console.log(JSON.stringify({iterations:n,ns,checksums,checksum257:ex.bench(257),rssBytes:process.memoryUsage().rss,maxRSSKiB:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
