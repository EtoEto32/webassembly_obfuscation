import fs from 'node:fs';
import {performance} from 'node:perf_hooks';
const [file,passesText]=process.argv.slice(2),passes=Number(passesText),t=performance.now();
const lib=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
const setupMs=performance.now()-t;lib.init(65536,77123);
for(let k=0;k<12;k++)lib.run(65536,passes,1,123456+k);
const samples=[],checks=[];
for(let k=0;k<11;k++){const t=performance.now();checks.push(lib.run(65536,passes,1,123456+k));samples.push(performance.now()-t);}
console.log(JSON.stringify({engine:'Node',version:process.version,v8:process.versions.v8,setupMs,samples,checks,privateAfter:lib['private-at'](0),peakBytes:process.resourceUsage().maxRSS*1024}));
