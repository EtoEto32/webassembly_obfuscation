import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import observer from './observer.cjs';const {call,snapshot,difference}=observer;
const [audit,original,normalized,name,out]=process.argv.slice(2),r=JSON.parse(fs.readFileSync(path.join(audit,name+'.json')));
const meta=r.manifest,memoryExport=meta.originalExports.find(e=>e[2][0]==='memory'&&e[2][1]==='0');assert(memoryExport);
const memoryName=JSON.parse(memoryExport[1]),rows=[];let reference=null,referenceOutcome=null;
for(const [kind,file] of [['original',path.join(original,'wasm-r3-bench',name+'.wasm')],['normalized',path.join(normalized,'wasm-r3-bench',name+'.wasm')],['observed',path.join(audit,name+'.wasm')]]){
 const bytes=fs.readFileSync(file),start=performance.now(),module=new WebAssembly.Module(bytes),instance=new WebAssembly.Instance(module);let probeChecks=0;
 assert.equal(instance.exports._start.length,0);
 if(kind==='observed'){assert.deepEqual(difference(snapshot(instance,meta),snapshot(instance,meta)),[]);probeChecks++;}
 const beforeCall=performance.now(),result=call(instance.exports._start),executionMs=performance.now()-beforeCall;
 const memory=Buffer.from(instance.exports[memoryName].buffer);
 if(kind==='observed'){assert.deepEqual(difference(snapshot(instance,meta),snapshot(instance,meta)),[]);probeChecks++;}
 if(reference===null){reference=memory;referenceOutcome=result;}else{assert(reference.equals(memory),'exported memory mismatch');assert.deepEqual(result,referenceOutcome,'entry outcome mismatch');}
 rows.push({kind,status:result.trap?'guest-trap':'completed',outcome:result,memoryBytes:memory.length,memorySha256:createHash('sha256').update(memory).digest('hex'),
   inputSha256:createHash('sha256').update(bytes).digest('hex'),executionMs,totalMs:performance.now()-start,probeChecks});
 fs.writeFileSync(out,JSON.stringify({node:process.version,v8:process.versions.v8,name,rows,status:'in-progress',note:'Single run, no warmup; resource-limited correctness check, not a performance comparison.'},null,2));
}
fs.writeFileSync(out,JSON.stringify({node:process.version,v8:process.versions.v8,name,rows,status:'compared',rss:process.memoryUsage().rss,note:'API outcomes and exported memory compared byte-for-byte; original private globals/table not fully compared.'},null,2));
console.log(JSON.stringify({name,status:'compared',outcome:referenceOutcome,memoryBytes:reference.length}));
