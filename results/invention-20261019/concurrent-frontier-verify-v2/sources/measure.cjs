'use strict';
const fs=require('node:fs'),h=require('./harness.cjs');
const file=process.argv[2],kind=process.argv[3],workers=Number(process.argv[4]);
async function main(){
 let times=[],checksum=0,checks=0,start=process.hrtime.bigint(),setup_ns,heapbytes=0;
 if(kind==='local'){
  const vm=workers===16;const memory=vm?new WebAssembly.Memory({initial:1,maximum:1,shared:true}):null;
  const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file)),vm?{env:{memory}}:{});
  setup_ns=Number(process.hrtime.bigint()-start);heapbytes=vm?65536:0;
  inst.exports.bench(2048);const expected=inst.exports.bench(512);
  for(let i=0;i<7;i++){const t=process.hrtime.bigint();const got=inst.exports.bench(512);times.push(Number(process.hrtime.bigint()-t)/512);checksum^=got;if(got!==expected)throw new Error('unstable checksum');checks++;}
 }else{
  const p=await h.pool(file,workers);setup_ns=Number(process.hrtime.bigint()-start);heapbytes=65536;
  const input=h.inputs().slice(0,32),expected=input.map(a=>p.instance.exports.run(...a));
  try {
   for(let i=0;i<16;i++)await p.run(input[i]);
   for(let rep=0;rep<7;rep++){
    const t=process.hrtime.bigint();
    for(let i=0;i<input.length;i++){const got=await p.run(input[i]);checksum^=got;if(got!==expected[i])throw new Error('worker mismatch');checks++;}
    times.push(Number(process.hrtime.bigint()-t)/input.length);
   }
  }finally{await p.close();}
 }
 console.log(JSON.stringify({kind,workers,samples_ns:times,median_ns:[...times].sort((a,b)=>a-b)[3],setup_ns,checksum,checks,heapbytes,maxRSS_kib:process.resourceUsage().maxRSS}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
