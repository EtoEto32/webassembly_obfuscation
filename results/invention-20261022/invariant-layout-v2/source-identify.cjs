const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const mem=new Uint32Array(e.__physical.buffer);let rng=0x4bd2371;
function rand(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
const h=x=>(x^(x>>>13))&3;
const phase=a=>a.reduce((s,x)=>s+h(x),0)&3;
function encode(x,kind){const s=kind==='fixed'?1:phase(x);return x.map((_,j)=>x[(j-s+4)%4]);}
const records=[];
for(const kind of ['fixed','dynamic']){
 let mismatch=0,calls=0,first=null;
 for(let k=0;k<256;k++){
  const x=Array.from({length:4},()=>rand()),i=k%4,value=rand(),encoded=encode(x,kind);
  mem.set(encoded);const got=e.__load(BigInt(i*4))>>>0;calls++;
  e.__store(BigInt(i*4),value);calls++;
  const want=x.slice();want[i]=value;const exp=encode(want,kind),actual=Array.from(mem.slice(0,4));
  if(got!==x[i]||actual.some((v,j)=>v!==exp[j])){mismatch++;if(!first)first={x,i,value,got,expectedLoad:x[i],actual,expected:exp};}
 }
 records.push({kind,mismatch,calls,first});
}
console.log(JSON.stringify({records,kind:records.find(x=>x.mismatch===0)?.kind??null,scope:'Finite behavioral identification in a known representation family; not arbitrary binary equivalence proof.'}));
