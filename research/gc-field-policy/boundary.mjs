import fs from 'node:fs';
const spec=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rows=[];
for(const c of spec) {
  const lib=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(c.library)));
  const client=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(c.consumer)),{lib:lib.exports});
  let actual;try{actual={type:'return',value:client.exports.run()}}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;actual={type:'trap'}}
  rows.push({name:c.name,actual,expected:c.expected});
}
console.log(JSON.stringify({node:process.version,rows}));
