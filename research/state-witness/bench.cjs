'use strict';
const fs=require('fs'),path=require('path');const {snapshot}=require('./observer.cjs');
const dir=process.argv[2],seed0=Number(process.argv[3]);
let seed=seed0,sink=0;function rnd(n){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;}
const median=a=>[...a].sort((a,b)=>a-b)[a.length>>1];
const input=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
for(const r of input.rows){
  const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.full))));
  for(const state of ['initial','dropped']){
    if(state==='dropped'){instance.exports.ddrop();instance.exports.edrop();}
    const methods={visible:()=>snapshot(instance,r.manifest,{segments:false,bounds:false}),
                   segments:()=>snapshot(instance,r.manifest,{segments:true,bounds:false}),
                   full:()=>snapshot(instance,r.manifest)};
    const samples={visible:[],segments:[],full:[]};
    for(let round=-3;round<15;round++){
      const names=Object.keys(methods);for(let i=names.length-1;i>0;i--){const j=rnd(i+1);[names[i],names[j]]=[names[j],names[i]];}
      for(const mode of names){
        const start=process.hrtime.bigint();
        for(let i=0;i<100;i++){const s=methods[mode]();sink^=s.pages??0;sink^=s.segments.length;}
        const ns=Number(process.hrtime.bigint()-start)/100;if(round>=0)samples[mode].push(ns);
      }
    }
    for(const mode of Object.keys(methods))rows.push({fixture:r.name,state,mode,samples:samples[mode],medianNs:median(samples[mode])});
  }
}
console.log(JSON.stringify({rows,node:process.version,v8:process.versions.v8,platform:process.platform,seed:seed0,
  sink,maxRssKiB:process.resourceUsage().maxRSS,rss:process.memoryUsage().rss,
  note:'RSS is mixed across variants; visible baseline omits segment/bounds correctness checks.'}));
