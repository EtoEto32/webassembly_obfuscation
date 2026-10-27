'use strict';
// These are intentionally violated host contracts, not claimed vulnerabilities
// of an external engine. Each negative must produce a concrete discrepancy.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const [source,output]=process.argv.slice(2),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
async function moduleOf(file){return(await WebAssembly.instantiate(fs.readFileSync(path.join(source,file)),{host:{before(){},mutate(){}}})).instance;}
function begin(instance,args){const v=new Uint8Array(instance.exports.memory.buffer);v.fill(13);const before=v.slice(0,1024);
 const address=((args[0]>>>0)+4)>>>0;const kept=new Map([[address,v[address]]]);
 return{before,kept,view(){const now=new Uint8Array(instance.exports.memory.buffer);return before.map((_,i)=>kept.has(i)?kept.get(i):now[i]);}};}
(async()=>{
 const instance=await moduleOf('transitive-raw.wasm'),rows=[];
 // Positive matching args, one callback, then immediate consume.
 let view=begin(instance,[512,255,0]);instance.exports.callback(512,255,0);assert.deepEqual(view.view(),view.before);
 rows.push({name:'matching-contract',expectedMismatch:false});
 // Second entry writes a byte outside the first callback's saved set.
 instance.exports.callback(600,255,0);assert.notDeepEqual(view.view(),view.before);
 rows.push({name:'second-writer-before-consumption',expectedMismatch:true,firstBadByte:604});
 // Saving for one argument tuple cannot justify executing another.
 view=begin(instance,[512,255,0]);instance.exports.callback(600,255,0);assert.notDeepEqual(view.view(),view.before);
 rows.push({name:'arguments-rebound',expectedMismatch:true,firstBadByte:604});
 const other=await moduleOf('descriptor-change-raw.wasm');view=begin(other,[512,255,0]);
 other.exports.callback(512,255,0);assert.notDeepEqual(view.view(),view.before);
 const hashA=hash(fs.readFileSync(path.join(source,'transitive-raw.wasm'))),hashB=hash(fs.readFileSync(path.join(source,'descriptor-change-raw.wasm')));
 assert.notEqual(hashA,hashB);rows.push({name:'different-binary-summary',expectedMismatch:true,digestMismatch:true});
 fs.writeFileSync(output,JSON.stringify({positive:1,contractCounterexamples:3,rows},null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
