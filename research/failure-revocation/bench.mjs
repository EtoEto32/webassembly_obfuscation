import fs from 'node:fs';
import {performance} from 'node:perf_hooks';
const [file,nText]=process.argv.slice(2), n=Number(nText);
const gate=new WebAssembly.Global({value:'i32',mutable:true},1);
const begin=performance.now();
const module=new WebAssembly.Module(fs.readFileSync(file));
const instance=new WebAssembly.Instance(module,{__failure_gate:{alive:gate}});
const setupMs=performance.now()-begin;
for(let k=0;k<12;k++)instance.exports.run(n,123456+k);
const samples=[],checks=[];
for(let k=0;k<11;k++) {
  const t=performance.now();checks.push(instance.exports.run(n,123456+k));samples.push(performance.now()-t);
}
console.log(JSON.stringify({engine:'Node',version:process.version,v8:process.versions.v8,n,setupMs,samples,checks,peakBytes:process.resourceUsage().maxRSS*1024}));
