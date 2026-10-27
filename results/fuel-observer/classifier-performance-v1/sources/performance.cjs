'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const {bind}=require('./guard.cjs');
const [root,mode,seedText]=process.argv.slice(2),manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));let sink=0;
const workloadPath=path.join(root,'data','dataset.json'),workload=fs.existsSync(workloadPath)?JSON.parse(fs.readFileSync(workloadPath)).data:null;
const median=a=>[...a].sort((x,y)=>x-y)[Math.floor(a.length/2)];const rows=[];
for(const record of manifest.records){
  const folder=path.join(root,record.kind),contract=JSON.parse(fs.readFileSync(path.join(folder,'target.json')));let run;
  if(mode==='original'||mode==='whole-host'){
    const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(folder,'original-O3.wasm'))),{env:{mark:()=>{}}});
    run=(s,x,budget)=>{if(mode==='whole-host'&&budget<contract.whole)throw new Error('budget');return inst.exports.run(s,x)>>>0;};
  }else{
    const bytes=fs.readFileSync(path.join(folder,'target-O3.wasm'));contract.targetSha256=crypto.createHash('sha256').update(bytes).digest('hex');
    const g=bind(bytes,contract,{mode,capture:false});run=(s,x,budget)=>{const r=g.run(s,x,budget);if(r.status!=='ok')throw new Error('unexpected budget');return r.value;};
  }
  const invoke=(i,rep)=>run(workload?workload[i%workload.length].secret:i&15,workload?0:(Math.imul(i,1013904223)+rep)>>>0,contract.whole+(i&1));
  for(let i=0;i<3000;i++)sink^=invoke(i,Number(seedText));
  const samples=[];for(let rep=0;rep<11;rep++){const begin=process.hrtime.bigint();for(let i=0;i<10000;i++)sink^=invoke(i,rep);samples.push(Number(process.hrtime.bigint()-begin)/10000);}
  const sorted=[...samples].sort((a,b)=>a-b);rows.push({kind:record.kind,nsPerCall:samples,median:median(samples),q1:sorted[2],q3:sorted[8]});
}
console.log(JSON.stringify({mode,seed:Number(seedText),rows,sink,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,platform:process.platform,memory:process.memoryUsage(),resourceUsage:process.resourceUsage(),warmup:3000,callsPerSample:10000,samples:11,workload:workload?'150 Iris records in source order':'16 secret classes, generated x'}));
