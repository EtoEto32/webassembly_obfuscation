'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{spawnSync}=require('node:child_process'),c=require('./common.cjs');
const median=a=>a.slice().sort((a,b)=>a-b)[Math.floor(a.length/2)];
if(process.argv[2]==='child'){
 const o=c.instantiate(process.argv[3],process.argv[4]);let x=1234567,y=7654321,checksum=0;
 function batch(n){let s=0;for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)>>>0;y=(Math.imul(y,22695477)+1)>>>0;s+=o.api.run(x,y);}return s;}
 batch(1024);let n=256;for(;;){const t=performance.now();checksum^=batch(n);if(performance.now()-t>=15||n>=2**22)break;n*=2;}
 const samples=[];for(let k=0;k<7;k++){const t=performance.now(),sum=batch(n),ms=performance.now()-t;samples.push({n,elapsed_ms:ms,ns_per_call:ms*1e6/n,checksum:sum});checksum^=sum;}
 console.log(JSON.stringify({samples,checksum,median_ns:median(samples.map(x=>x.ns_per_call)),max_rss_kib:process.resourceUsage().maxRSS,memory_bytes:o.api.memory?.buffer.byteLength??0}));
}else{
 const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))).filter(r=>r.version==='O3'),runtime=[];
 for(let rep=0;rep<3;rep++)for(const row of [...rows.slice(rep*3),...rows.slice(0,rep*3)])for(const adapter of row.mode==='validator'?['validator','recognizer']:['native']){
  const r=spawnSync(process.execPath,['--no-liftoff','--no-wasm-lazy-compilation',__filename,'child',path.join(out,row.file),adapter],{encoding:'utf8',timeout:60000});if(r.status!==0)throw Error(r.stderr);
  runtime.push({file:row.file,name:row.name,mode:row.mode,adapter,repeat:rep,...JSON.parse(r.stdout)});
 }
 const summaries=[];for(const row of rows)for(const adapter of row.mode==='validator'?['validator','recognizer']:['native']){
  const a=runtime.filter(x=>x.file===row.file&&x.adapter===adapter).map(x=>x.median_ns);summaries.push({file:row.file,adapter,median_ns:median(a),range_ns:[Math.min(...a),Math.max(...a)]});
 }
 c.save(out,'runtime.json',{cpu:os.cpus()[0].model,logical_cpus:os.cpus().length,flags:['--no-liftoff','--no-wasm-lazy-compilation'],warmup:1024,host_call_included:true,js_input_generation_included:true,runtime,summaries});
 console.log(JSON.stringify({kind:'performance',processes:runtime.length,batches:runtime.reduce((s,x)=>s+x.samples.length,0),short_batches:runtime.flatMap(x=>x.samples).filter(s=>s.elapsed_ms<10).length,passed:true}));
}
