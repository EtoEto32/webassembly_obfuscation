const fs=require('fs'),path=require('path'),os=require('os');
const m=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rep=Number(process.argv[3]);
let seed=20261024+rep;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
function median(a){return [...a].sort((x,y)=>x-y)[Math.floor(a.length/2)];}
const rows=[];let sink=0;
function job(e,kind,n){if(kind==='grow-drop'){e.grow(1);e.tgrow(3);e.init(0,0,3);e.tinit(0,0,3);e.ddrop();e.edrop();}return e.work(n);}
for(const fixture of ['small','medium']){
 for(const kind of ['work-only','grow-drop'])for(const n of [0,64,4096,65536]){
  const specs=m.rows.filter(r=>r.fixture===fixture&&r.pipeline==='O3'&&(!r.job||r.job===kind));
  const mods=Object.fromEntries(specs.filter(r=>['source','full','plain'].includes(r.mode)).map(r=>[r.mode,new WebAssembly.Module(fs.readFileSync(path.join(m.directory,r.file)))]));
  const inst={full:new WebAssembly.Instance(mods.full).exports,fullCopy:new WebAssembly.Instance(mods.full).exports,plain:new WebAssembly.Instance(mods.plain).exports};
  const names=kind==='work-only'?['fresh','full','fullCopy','plain']:['fresh','full','fullCopy'];
  const expected=job(new WebAssembly.Instance(mods.source).exports,kind,n);
  const samples=Object.fromEntries(names.map(n=>[n,[]]));const repetitions=n===65536?30:150;
  for(let round=-2;round<15;round++){
   const order=[...names];for(let i=order.length-1;i>0;i--){const j=rand()%(i+1);[order[i],order[j]]=[order[j],order[i]];}
   for(const mode of order){
    const begin=process.hrtime.bigint();
    for(let i=0;i<repetitions;i++){
     let e;if(mode==='fresh')e=new WebAssembly.Instance(mods.source).exports;else{e=inst[mode];e.__lr_reset();}
     const v=job(e,kind,n);if(v!==expected)throw Error(`mismatch ${fixture} ${kind} ${mode}`);sink^=v;
    }
    const ns=Number(process.hrtime.bigint()-begin)/repetitions;if(round>=0)samples[mode].push(ns);
   }
  }
  for(const mode of names)rows.push({fixture,kind,n,mode,repetitions,samplesNs:samples[mode],medianNs:median(samples[mode])});
 }
}
console.log(JSON.stringify({rows,sink,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,memoryUsage:process.memoryUsage(),resourceUsage:process.resourceUsage(),warmupRounds:2,rounds:15}));
