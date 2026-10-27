'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const source=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),replicate=Number(process.argv[3]);
let seed=(2026102427+replicate)>>>0;
function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;}
function shuffle(list){list=list.slice();for(let i=list.length-1;i>0;i--){const j=random()%(i+1);[list[i],list[j]]=[list[j],list[i]];}return list;}
function median(a){a=a.slice().sort((x,y)=>x-y);return a[a.length>>1];}
const names=['adaptive-native','first-native','alternating-native','all_mask-native','strict-native','scalar-native','dispatch-native','adaptive-0','strict-0','scalar-0','dispatch-0'];
const modes=names.map(name=>{const row=source.rows.find(r=>r.mode===name);return {name,file:row.optimized};});
modes.push({name:'adaptiveCopy-native',file:modes[0].file});
const table=Uint8Array.from({length:256},(_,i)=>(Math.imul(i,73)+51)&255),entries=new Map();
for(const m of modes){
 const bytes=fs.readFileSync(path.join(source.directory,m.file));const begin=process.hrtime.bigint();
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;const compileNs=Number(process.hrtime.bigint()-begin);
 const memory=new Uint8Array(e.memory.buffer);memory.set(table);for(let i=0;i<65536;i++)memory[1024+i]=(Math.imul(i,151)+Math.floor(i/256)*37)&255;
 const profile=e.init();for(const n of [16,256,4096,65536]){e.run(n);for(let i=0;i<n;i++)if(memory[131072+i]!==table[memory[1024+i]])throw new Error('benchmark check '+m.name);}
 entries.set(m.name,{e,compileNs,bytes:bytes.length,profile});
}
const rows=[];
for(const n of shuffle([16,256,4096,65536])){
 const iterations=Math.max(16,Math.floor(1048576/n));const samples=Object.fromEntries(modes.map(m=>[m.name,[]]));
 const sample=name=>{const e=entries.get(name).e;const start=process.hrtime.bigint();for(let i=0;i<iterations;i++)e.run(n);return Number(process.hrtime.bigint()-start)/(iterations*n);};
 for(let warm=0;warm<2;warm++)for(const name of shuffle(names.concat('adaptiveCopy-native')))sample(name);
 for(let round=0;round<15;round++)for(const name of shuffle(names.concat('adaptiveCopy-native')))samples[name].push(sample(name));
 for(const name of Object.keys(samples))rows.push({name,n,iterations,samplesNsPerByte:samples[name],medianNsPerByte:median(samples[name])});
}
const initSamples=Object.fromEntries(modes.map(m=>[m.name,[]]));
for(const {name} of modes)for(let i=0;i<1000;i++)entries.get(name).e.init();
for(let round=0;round<15;round++)for(const {name} of shuffle(modes)){
 const e=entries.get(name).e;const start=process.hrtime.bigint();for(let i=0;i<5000;i++)e.init();initSamples[name].push(Number(process.hrtime.bigint()-start)/5000);
}
process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,replicate,seed:2026102427+replicate,rows,
 init: Object.fromEntries(Object.entries(initSamples).map(([k,v])=>[k,{samplesNs:v,medianNs:median(v)}])),
 metadata:Object.fromEntries([...entries].map(([k,v])=>[k,{bytes:v.bytes,profile:v.profile,compileNs:v.compileNs}])),memoryUsage:process.memoryUsage(),resourceUsage:process.resourceUsage()}));
