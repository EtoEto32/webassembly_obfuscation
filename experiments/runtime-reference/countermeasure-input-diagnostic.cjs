'use strict';
// Bounded baseline-only diagnostic for input length/order, after confirmed permission.
const fs=require('fs'),crypto=require('crypto');
function read(p){const fd=fs.openSync(p,'r'),chunks=[];try{for(;;){const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length);if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}return Buffer.concat(chunks);}
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=read('/inputs/plan.json'),plan=JSON.parse(raw);
const permission=JSON.parse(read('/inputs/permission.json'));
if(!permission.confirmed||permission.plan_sha256!==digest(raw))throw Error('Permission missing');
if(process.platform!=='linux'||process.version!==plan.environment.intended_node)throw Error('Runtime mismatch');
const bytes=read('/inputs/'+plan.baseline_sha256+'.wasm');
if(digest(bytes)!==plan.baseline_sha256||digest(read('/inputs/swamped-host.cjs'))!==plan.host.sha256)throw Error('Digest mismatch');
const {load}=require('/inputs/swamped-host.cjs');
const vectors=[...plan.public_vectors,...plan.additional_vectors];
const results=[];
for(const v of vectors){
 const outputs=[];
 for(let i=0;i<2;i++){const h=load(bytes);try{h.hash(v);outputs.push(h.output());}finally{h.close();}}
 results.push({id:v.id,mode:'fresh-context-each-input',outputs});
}
for(const reverse of [false,true]){
 const h=load(bytes);
 try{for(const v of reverse?[...vectors].reverse():vectors){h.hash(v);results.push({id:v.id,mode:reverse?'reused-reverse':'reused-forward',output:h.output()});}}finally{h.close();}
}
console.log(JSON.stringify({baseline_sha256:plan.baseline_sha256,node:process.version,v8:process.versions.v8,results}));
