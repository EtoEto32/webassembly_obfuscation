const fs=require('fs'),os=require('os');
const target=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2])));
const wrapper=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[3])),{target:target.exports});
function expected(n){target.exports.reset();let x=123,c=0;for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)>>>0;c=((c<<1)^target.exports.step(x))>>>0;}return c;}
const want=expected(17);target.exports.reset();const got=wrapper.exports.bench(17,123)>>>0;if(want!==got)throw Error('wrapper mismatch');
target.exports.reset();let sink=wrapper.exports.bench(16384,123),n=256;
function measure(){target.exports.reset();const t=process.hrtime.bigint();sink^=wrapper.exports.bench(n,123);return Number(process.hrtime.bigint()-t);}
while(n<2**24){if(measure()>=15e6)break;n*=2;}
const batches=[];for(let i=0;i<7;i++){const ns=measure();batches.push({n,ns,ns_per_step:ns/n});}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,flags:process.execArgv,warmup:16384,seed:123,batches,sink,reset_excluded_from_timing:true,verification:{want,got},max_rss_kib:process.resourceUsage().maxRSS}));
