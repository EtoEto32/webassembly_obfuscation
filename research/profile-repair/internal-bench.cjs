'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),replicate=+process.argv[3];
let seed=(2026102423+replicate)>>>0;
const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
const shuffle=a=>{for(let i=a.length-1;i>0;i--){const j=rand()%(i+1);[a[i],a[j]]=[a[j],a[i]];}return a;};
const median=a=>{const s=[...a].sort((x,y)=>x-y);return s[Math.floor(s.length/2)];};
const rows=[];let sink=0;
for(const row of shuffle([...input.rows])){
  const modes=['all','aware','manual','allCopy'],run={},samples={};
  for(const mode of modes){run[mode]=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(input.directory,row.files[mode])))).exports.bench;samples[mode]=[];}
  for(const n of [1,31,1024]){const expected=run.all(n);for(const mode of modes)if(run[mode](n)!==expected)throw Error('benchmark mismatch '+row.name+' '+mode);}
  for(const mode of shuffle([...modes])){sink^=run[mode](200000);sink^=run[mode](200000);}
  for(let round=0;round<15;round++)for(const mode of shuffle([...modes])){
    const begin=process.hrtime.bigint();sink^=run[mode](200000);samples[mode].push(Number(process.hrtime.bigint()-begin)/200000);
  }
  rows.push({name:row.name,samples,medians:Object.fromEntries(modes.map(m=>[m,median(samples[m])]))});
}
process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,flags:process.execArgv,replicate,rows,sink,memory:process.memoryUsage(),resource:process.resourceUsage()}));
