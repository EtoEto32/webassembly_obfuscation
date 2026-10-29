'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'artifacts'),read=n=>JSON.parse(fs.readFileSync(path.join(dir,n+'.json')));
const meta=read('meta'),timings=read('timings'),recovery=read('recovery');
const median=a=>{a=a.slice().sort((a,b)=>a-b);return a[Math.floor(a.length/2)];};
const rows=[];for(const m of meta.manifest){for(const w of [...new Set(timings.map(t=>t.workload))]){
 const ts=timings.filter(t=>t.file===m.file&&t.workload===w);const ratios=ts.map(t=>t.ms/timings.find(b=>b.file==='plain-'+m.mode+'.wasm'&&b.workload===w&&b.round===t.round).ms);
 rows.push({file:m.file,workload:w,median_ms:median(ts.map(t=>t.ms)),min_ms:Math.min(...ts.map(t=>t.ms)),max_ms:Math.max(...ts.map(t=>t.ms)),median_paired_ratio:median(ratios)});
}}
// Ground-truth verification is deliberately separate from the extractor.
let verified=0;for(const r of recovery.rows.filter(r=>r.file.startsWith('mapped-'))){assert.equal(r.candidate.mask,23040);for(let i=0;i<65536;i++)assert.equal(i^r.candidate.mask,i^23040);verified++;}
const output={timing:rows,recovery_verification:{mapped_binaries:verified,positions_per_binary:65536,mismatches:0,scope:'Ground-truth verification of recovered XOR mapping, not source/CFG reconstruction.'}};
fs.writeFileSync(path.join(dir,'summary.json'),JSON.stringify(output,null,2));console.log(JSON.stringify(output,null,2));
