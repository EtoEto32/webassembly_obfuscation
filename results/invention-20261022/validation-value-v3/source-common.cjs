'use strict';
const fs=require('node:fs'),path=require('node:path');
function save(out,name,x){const f=path.join(out,name);if(fs.existsSync(f))throw Error('refuse overwrite');fs.writeFileSync(f,JSON.stringify(x,null,2));}
function recognize(b){
 if(b.length<8||[0,97,115,109,1,0,0,0].some((v,i)=>v!==b[i]))return false;
 let pos=8;const varint=()=>{let v=0,s=0;for(;;){if(pos>=b.length||s>28)throw Error('bad LEB');const c=b[pos++];v|=(c&127)<<s;if(!(c&128))return v>>>0;s+=7;}};
 try{
  let code=-1,end=-1;while(pos<b.length){const id=b[pos++],len=varint(),start=pos;if(pos+len>b.length)return false;if(id===10){code=start;end=start+len;}pos+=len;}
  if(code<0)return false;pos=code;if(varint()!==1)return false;const size=varint();if(pos+size!==end||b[pos++]!==0)return false;
  let all=true;while(pos<end-1){if(b[pos++]!==2||b[pos++]!==64)return false;let found=false;
   while(b[pos]===0||b[pos]===1){found ||= b[pos]===0;pos++;}
   if(b[pos++]!==0x6a||b[pos++]!==0x1a||b[pos++]!==0x0b)return false;all&&=found;
  }return all&&pos===end-1&&b[pos]===0x0b;
 }catch{return false;}
}
function instantiate(file,adapter='validator'){
 const module=new WebAssembly.Module(fs.readFileSync(file));let instance;let calls=0;
 const env={validate:(ptr,len)=>{calls++;const bytes=new Uint8Array(instance.exports.memory.buffer,ptr>>>0,len>>>0);return (adapter==='recognizer'?recognize(bytes):WebAssembly.validate(bytes))?1:0;}};
 instance=new WebAssembly.Instance(module,{env});return{module,api:instance.exports,hostCalls:()=>calls};
}
function evaluate(clauses,a,b){return clauses.every(c=>c.some(([word,bit,neg])=>(((word?b:a)>>>bit)&1)^neg))?1:0;}
function rng(seed){return()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;}
module.exports={save,recognize,instantiate,evaluate,rng};
