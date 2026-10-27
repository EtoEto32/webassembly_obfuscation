'use strict';
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const request=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let calls=0;const rows=[];
for(const row of request.rows){
  const exports=new Map(row.files.map(file=>[file,new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(request.directory,file)))).exports.run]));
  const results={};
  for(const [file,run] of exports){results[file]=request.inputs.map(([x,y])=>{calls++;return run(x,y)>>>0;});}
  rows.push({name:row.name,results});
}
process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,calls,rows}));
