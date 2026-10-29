import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const [source,variant,output]=process.argv.slice(2),meta=JSON.parse(fs.readFileSync(path.join(source,'manifest.json')));
const raw=fs.readFileSync(path.join(source,`observed-${variant}.wasm`)),started=performance.now(),module=new WebAssembly.Module(raw),compileMs=performance.now()-started;
let importCalls=0;const imports={},memories=[];
for(const imp of meta.imports){imports[imp.module]??={};if(imp.kind==='memory'){
 const m=new WebAssembly.Memory({initial:imp.initial,maximum:imp.maximum,shared:imp.shared});memories.push(m);imports[imp.module][imp.name]=m;
}else imports[imp.module][imp.name]=()=>{importCalls++;throw Error(`unexpected import ${imp.module}.${imp.name}`);};}
const begin=performance.now(),instance=new WebAssembly.Instance(module,imports),instantiateMs=performance.now()-begin;assert.equal(importCalls,0);assert.equal(memories.length,1);
const hash=()=>crypto.createHash('sha256').update(new Uint8Array(memories[0].buffer)).digest('hex');
const before=hash(),outcomes=[],pure=[];for(const item of meta.pureConstantExports){const value=instance.exports[item.name]();assert.equal(value,item.value);pure.push({name:item.name,value});}
for(let n=0;n<meta.dataLengths.length;n++){
 try{assert.equal(instance.exports[meta.probePrefix+n](),1);outcomes.push('live');}
 catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcomes.push('trap');}
}
const after=hash();assert.equal(before,after);assert.ok(outcomes.every(x=>x===(variant==='original'?'trap':'live')));assert.equal(importCalls,0);
const tables=Object.entries(instance.exports).filter(([,v])=>v instanceof WebAssembly.Table).map(([name,v])=>({name,length:v.length}));
const result={variant,engine:'Node',version:process.version,wasmSha256:crypto.createHash('sha256').update(raw).digest('hex'),compileMs,instantiateMs,memoryBytes:memories[0].buffer.byteLength,
 memoryBefore:before,memoryAfter:after,tableSizes:tables,pureConstantExports:pure,originalApiCalls:pure.length,probeCalls:outcomes.length,live:outcomes.filter(x=>x==='live').length,traps:outcomes.filter(x=>x==='trap').length,importCalls,resourceUsage:process.resourceUsage(),outcomes};
fs.writeFileSync(output,JSON.stringify(result,null,2));console.log(JSON.stringify({engine:result.engine,variant,live:result.live,traps:result.traps,originalApiCalls:result.originalApiCalls,memoryBefore:before}));
