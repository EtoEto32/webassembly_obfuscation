'use strict';
const h=require('./common.cjs');
(async()=>{
 const kind=process.argv[2],file=process.argv[3],start=performance.now();
 const unit=kind==='core'?await h.core(file):await h.component(file),setup_ms=performance.now()-start;
 let x=123456789,checksum=0;
 const run=n=>{for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)|0;checksum=(checksum+unit.run(x>>>0,(checksum^x)>>>0))|0;}};
 const warmup=50000,batch=kind==='core'?200000:10000,repeats=9;run(warmup);if(global.gc)global.gc();const before=process.memoryUsage(),ns=[];
 for(let i=0;i<repeats;i++){const t=performance.now();run(batch);ns.push((performance.now()-t)*1e6/batch);}
 if(global.gc)global.gc();const after=process.memoryUsage();
 console.log(JSON.stringify({kind,setup_ms,ns,checksum,warmup,batch,repeats,before,after,peak_rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
})().catch(e=>{console.error(e);process.exitCode=1;});
