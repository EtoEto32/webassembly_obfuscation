import fs from 'node:fs';
const spec=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rows=[];
for(const c of spec.cases){
  const lib=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(spec.library)));
  const client=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(c.path)),{lib:lib.exports});
  let result;try{result={type:'return',value:client.exports.run()};}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;result={type:'trap'};}
  rows.push({name:c.name,expected:c.expected,result});
}
console.log(JSON.stringify({engine:'Node',version:process.version,v8:process.versions.v8,experimentalCustomDescriptors:true,rows}));
