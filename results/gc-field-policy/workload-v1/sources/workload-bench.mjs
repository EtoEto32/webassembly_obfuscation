import fs from 'node:fs';
import {performance} from 'node:perf_hooks';
import {admit} from './loader.mjs';
const spec=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const start=performance.now();
const result=admit(spec.checkerPath,fs.readFileSync(spec.library),JSON.parse(fs.readFileSync(spec.policy,'utf8')),fs.readFileSync(spec.consumer),spec.allowedImports);
if(result.status!=='accepted')throw Error(JSON.stringify(result));
const setupMs=performance.now()-start,lib=result.library.exports,f=result.client.exports.run;
const init=performance.now();lib.init(spec.n,77123);const initMs=performance.now()-init;
for(let k=0;k<12;k++)f(spec.n,spec.passes,spec.stride,123456+k);
const samples=[],checks=[];
for(let k=0;k<11;k++){
  const t=performance.now();checks.push(f(spec.n,spec.passes,spec.stride,123456+k));samples.push(performance.now()-t);
}
console.log(JSON.stringify({engine:'Node',version:process.version,v8:process.versions.v8,setupMs,initMs,samples,checks,
  peakBytes:process.resourceUsage().maxRSS*1024,privateAfter:lib['private-at'](0)}));
