const fs=require('fs');
const bytes=fs.readFileSync(process.argv[2]);
const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const samples=[];for(let x=0;x<34;x++)samples.push({x,y:e.run(x)>>>0});
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,queries:34,samples}));
