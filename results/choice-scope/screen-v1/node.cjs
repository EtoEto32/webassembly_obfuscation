'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const q=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rows=[];
for(const file of q.files){
  let instance;try {instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(q.directory,file))));}
  catch(e){rows.push({file,status:'compile-error',error:String(e)});continue;}
  for(const inputs of q.inputs){
    const start=performance.now();
    try {let r=instance.exports.run(...inputs);r=Array.isArray(r)?r:[r];rows.push({file,inputs,status:'ok',outputs:r.map(x=>x>>>0),milliseconds:performance.now()-start});}
    catch(e){rows.push({file,inputs,status:'trap',error:String(e)});}
  }
}
console.log(JSON.stringify({engine:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,peakRssKb:process.resourceUsage().maxRSS,rows}));
