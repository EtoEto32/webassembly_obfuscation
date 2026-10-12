const fs=require('fs');
const [binary,inputsFile,initialFile]=process.argv.slice(2);
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(binary))).exports;
const memory=Buffer.from(e.memory.buffer),initial=fs.readFileSync(initialFile);
const rows=JSON.parse(fs.readFileSync(inputsFile)).map(input=>{
 initial.copy(memory);let error=null,output=null;
 try{output=e.run(...input)>>>0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;error=err.message;}
 return {error,output,word0:memory.readUInt32LE(0)};
});
console.log(JSON.stringify(rows));
