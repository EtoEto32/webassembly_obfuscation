import fs from 'node:fs';import {createHash} from 'node:crypto';
const [file,out]=process.argv.slice(2),bytes=fs.readFileSync(file),m=new WebAssembly.Module(bytes),x=new WebAssembly.Instance(m);let outcome;
try{x.exports._start();outcome={value:null};}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;outcome={trap:true,message:e.message};}
const data=new Uint8Array(x.exports.memory.buffer),result={node:process.version,flags:process.execArgv,inputSha256:createHash('sha256').update(bytes).digest('hex'),outcome,pages:data.length/65536,memorySha256:createHash('sha256').update(data).digest('hex')};
fs.writeFileSync(out,JSON.stringify(result,null,2));console.log(JSON.stringify(result));
