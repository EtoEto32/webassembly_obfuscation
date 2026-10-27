'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process'),c=require('./common.cjs');
const median=x=>{const a=x.slice().sort((a,b)=>a-b);return a[Math.floor(a.length/2)];};
if(process.argv[2]==='child'){
 const file=process.argv[3],o=c.instantiate(file),samples=[];o.api.bench(32768,0);
 let n=32768;for(;;){const t=performance.now();o.api.bench(n,0);if(performance.now()-t>=12||n>=2**22)break;n*=2;}
 for(let k=0;k<9;k++){o.physical.fill(0);const t=performance.now(),checksum=o.api.bench(n,0),elapsed=performance.now()-t;samples.push({n,elapsed_ms:elapsed,ns_per_update:elapsed*1e6/n,checksum});}
 console.log(JSON.stringify({samples,median_ns:median(samples.map(s=>s.ns_per_update)),max_rss_kib:process.resourceUsage().maxRSS,memory_bytes:o.memory.buffer.byteLength,node:process.version,v8:process.versions.v8}));
}else{
 const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))).filter(r=>r.version==='O3'),runtime=[],analyses=[];
 for(let rep=0;rep<3;rep++)for(const row of [...rows.slice(rep*3),...rows.slice(0,rep*3)]){
  const r=spawnSync(process.execPath,['--no-liftoff','--no-wasm-lazy-compilation',__filename,'child',path.join(out,row.file)],{encoding:'utf8',timeout:30000});if(r.status!==0)throw Error(r.stderr);runtime.push({file:row.file,repeat:rep,...JSON.parse(r.stdout)});
 }
 for(const row of rows){const probes=[];for(let k=0;k<7;k++)probes.push(c.identify(path.join(out,row.file)));assert(probes.every(p=>p.codec===(row.codec==='both'?'identity':row.codec)));
  analyses.push({file:row.file,probes,median_ms:median(probes.map(p=>p.elapsed_ms)),store_calls:4});
 }
 const summaries=rows.map(row=>{const r=runtime.filter(x=>x.file===row.file);return{file:row.file,profile:row.profile,mode:row.mode,median_ns:median(r.map(x=>x.median_ns)),process_range_ns:[Math.min(...r.map(x=>x.median_ns)),Math.max(...r.map(x=>x.median_ns))],bytes:row.bytes,memory_bytes:65536,transform_ms:row.transform_ms};});
 c.save(out,'performance.json',{cpu:os.cpus()[0].model,logical_cpus:os.cpus().length,flags:['--no-liftoff','--no-wasm-lazy-compilation'],warmup:32768,repetitions:3,batches:9,affinity_controlled:false,runtime,analyses,summaries});
 console.log(JSON.stringify({kind:'performance',processes:runtime.length,batches:runtime.reduce((s,x)=>s+x.samples.length,0),short_batches:runtime.flatMap(x=>x.samples).filter(s=>s.elapsed_ms<10).length,analysis_probes:analyses.length*7,passed:true}));
}
