'use strict';
// Each binary has its own process. Timings include JS -> Wasm call overhead.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),os=require('node:os'),crypto=require('node:crypto');
const median=a=>[...a].sort((x,y)=>x-y)[Math.floor(a.length/2)];
if(process.argv[2]==='--worker'){
 const bytes=fs.readFileSync(process.argv[3]);
 const rssBefore=process.memoryUsage().rss,started=performance.now();
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 const compileInstantiateMs=performance.now()-started,rssAfterInstantiate=process.memoryUsage().rss;
 const inputs=[];let state=20261018;
 const rand=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;};
 for(let i=0;i<4096;i++)inputs.push([rand(),rand(),8+(rand()&15)]);
 let sink=0;
 function batch(){for(let rep=0;rep<4;rep++)for(const [x,y,n]of inputs)sink=(Math.imul(sink,1664525)+e.run(x,y,n)+1013904223)|0;}
 for(let w=0;w<5;w++)batch();
 const ns=[];for(let r=0;r<7;r++){const t=performance.now();batch();ns.push((performance.now()-t)*1e6/16384);}
 console.log(JSON.stringify({sha256:crypto.createHash('sha256').update(bytes).digest('hex'),nsPerCall:ns,medianNs:median(ns),minNs:Math.min(...ns),maxNs:Math.max(...ns),compileInstantiateMs,
  rssBefore,rssAfterInstantiate,rssAfterRun:process.memoryUsage().rss,processPeakRssKiB:process.resourceUsage().maxRSS,sink}));
}else{
 const d=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(d,'manifest.json'),'utf8'));
 const output=path.join(d,'performance.json');if(fs.existsSync(output))throw Error('Refuse overwrite');
 const order=[...m.artifacts];let state=20261018;
 function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
 for(let i=order.length-1;i>0;i--){const j=rand()%(i+1);[order[i],order[j]]=[order[j],order[i]];}
 const rows=[];
 for(const a of order){
  const r=cp.spawnSync(process.execPath,[__filename,'--worker',path.join(d,a.file)],{encoding:'utf8',timeout:30000});
  if(r.status!==0){rows.push({...a,status:r.error?.code==='ETIMEDOUT'?'timeout':'process-failed',stderr:r.stderr,error:String(r.error||'')});continue;}
  const v=JSON.parse(r.stdout);if(v.sha256!==a.sha256)throw Error('hash mismatch');rows.push({...a,status:'measured',...v});
 }
 for(const r of rows){const base=rows.find(a=>a.kernel===r.kernel&&a.level===r.level&&a.mode==='plain');if(r.status==='measured'&&base.status==='measured')r.ratioOfMediansToPlain=r.medianNs/base.medianNs;}
 fs.writeFileSync(output,JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,flags:process.execArgv,seed:20261018,
  warmupCalls:81920,rounds:7,callsPerRound:16384,iterationRange:[8,23],rows,
  limitations:'One fresh process per condition in shuffled order. JS host crossing included. RSS is whole Node process, not isolated Wasm allocation. Ratios of medians are not paired measurements or confidence intervals. No linear memory in modules.'},null,2),{flag:'wx'});
 fs.copyFileSync(__filename,path.join(d,'measure.cjs'));
 console.log(JSON.stringify({conditions:rows.length,measured:rows.filter(r=>r.status==='measured').length}));
}
