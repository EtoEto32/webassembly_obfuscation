import fs from 'node:fs';
const files=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,rows:files.map(path=>{
  const bytes=fs.readFileSync(path);
  return {path,valid:WebAssembly.validate(bytes)};
})}));
