const fs=require('fs'),path=require('path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const rows=[];
for(const r of manifest.rows.filter(x=>x.mode==='projected')){
  const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.wasm)))).exports.run;
  const count=Math.ceil(r.n/(2**r.shift));
  // Only the declared public prefix schema and index domain determine the queries.
  rows.push({wasm:r.wasm,answers:Array.from({length:count},(_,i)=>f(i)>>>0)});
}
fs.writeFileSync(path.join(dir,'public-answers.json'),JSON.stringify({rows}));
console.log(JSON.stringify({conditions:rows.length,queries:rows.reduce((a,r)=>a+r.answers.length,0)}));
