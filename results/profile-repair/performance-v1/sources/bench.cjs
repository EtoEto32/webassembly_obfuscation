'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),mode=process.argv[3],rows=[];
const median=a=>{const s=[...a].sort((x,y)=>x-y);return s[Math.floor(s.length/2)];};
let sink=0;
for(const row of input.rows){
  const run=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(input.directory,row.files[mode])))).exports.run;
  const inputs=input.inputs;
  const loop=n=>{let sum=0;for(let i=0;i<n;i++){const v=inputs[i%inputs.length];sum=(sum+run(v[0],v[1]))|0;}sink^=sum;};
  loop(20000);const samples=[];
  for(let rep=0;rep<11;rep++){const begin=process.hrtime.bigint();loop(20000);samples.push(Number(process.hrtime.bigint()-begin)/20000);}
  rows.push({name:row.name,medianNs:median(samples),samplesNs:samples});
}
process.stdout.write(JSON.stringify({mode,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,platform:process.platform,arch:process.arch,memory:process.memoryUsage(),resource:process.resourceUsage(),sink,rows}));
