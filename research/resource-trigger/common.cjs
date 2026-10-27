'use strict';
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
async function core(file){return (await WebAssembly.instantiate(fs.readFileSync(file))).instance.exports;}
async function component(dir){
  const api=await import(pathToFileURL(path.resolve(dir,'unit.js')).href);
  return api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{});
}
function evaluate(e,x,y){
  if(e[0]==='i32.const')return Number(e[1])|0;
  if(e[0]==='local.get')return Number(e[1])===0?x|0:y|0;
  const a=evaluate(e[1],x,y),b=evaluate(e[2],x,y),k=b&31;
  switch(e[0]){
    case 'i32.add':return (a+b)|0;case 'i32.sub':return (a-b)|0;case 'i32.mul':return Math.imul(a,b);
    case 'i32.xor':return a^b;case 'i32.and':return a&b;case 'i32.or':return a|b;
    case 'i32.shl':return a<<k;case 'i32.shr_u':return (a>>>k)|0;case 'i32.shr_s':return a>>k;
    case 'i32.rotl':return (a<<k)|(a>>>((32-k)&31));case 'i32.rotr':return (a>>>k)|(a<<((32-k)&31));
    default:throw Error('oracle unsupported '+e[0]);
  }
}
function inputs(n=1024){
  const edge=[0,1,-1,2,-2,31,32,2147483647,-2147483648],out=[];
  for(const x of edge)for(const y of edge)out.push([x,y]);
  let state=191019;const random=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state|0;};
  for(let i=0;i<n;i++)out.push([random(),random()]);return out;
}
module.exports={core,component,evaluate,inputs};
