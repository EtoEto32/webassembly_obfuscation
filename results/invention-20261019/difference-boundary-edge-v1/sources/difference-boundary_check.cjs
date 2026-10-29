const fs=require('fs'),path=require('path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function hash(a){let h=2166136261;for(const b of a)h=Math.imul(h^b,16777619)>>>0;return h;}
function inputs(n){
 let b=Math.min(n,8),rows=[[0,0,0],[n,n,0],[n+1,0,0],[0,n+1,0],[0,0,n],[0,1,n-1],[1,0,n-1],[0,n-1,1],[n-1,0,1],[n-1,n-1,1],[n,0,1],[0,n,1],[0,0,n+1],[0xffffffff,1,2],[1,0xffffffff,2],[0x80000000,0,0],[0,0,0xffffffff],[n-b,0,b],[0,n-b,b],[1,2,1],[2,1,1]];
 let seed=0x176293ab;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 for(let i=0;i<512;i++){
  if(i%7===0){rows.push([rnd(),rnd(),rnd()]);continue;}
  let len=rnd()%(n+1),s=rnd()%(n-len+1),d=rnd()%(n-len+1);rows.push([d,s,len]);
 }
 return rows;
}
let copies=0,digests=0,trapCopies=0,byteComparisons=0,rows=[];
for(const q of manifest.files){
 const binary=fs.readFileSync(path.join(dir,q.path)),probe=fs.readFileSync(path.join(dir,q.probe));
 if(!WebAssembly.validate(binary)||!WebAssembly.validate(probe))throw Error('invalid '+q.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(binary)).exports;
 const pe=new WebAssembly.Instance(new WebAssembly.Module(probe)).exports;
 const memory=new Uint8Array(pe.memory.buffer);
 const a=Uint8Array.from(manifest.datasets[q.dataset]);let failures=0;
 function observe(){
  const expected=hash(a);if((e.digest()>>>0)!==expected||(pe.digest()>>>0)!==expected)throw Error('digest '+q.path);digests+=2;
  for(let i=0;i<65536;i++){
   const v=i>=a.length?0:q.mode==='plain'||q.recovered?a[i]:q.mode==='xor'?a[i]^167:a[i]^(i?a[i-1]:0);
   if(memory[i]!==v)throw Error('memory '+q.path+' '+i+' '+memory[i]+' '+v);byteComparisons++;
  }
 }
 observe();
 for(const args of inputs(a.length)){
  const [d,s,n]=args,trap=BigInt(d)+BigInt(n)>BigInt(a.length)||BigInt(s)+BigInt(n)>BigInt(a.length);
  if(!trap){const old=a.slice(s,s+n);a.set(old,d);}
  for(const target of [e,pe]){
   let got=false;try{target.copy(...args);}catch(ex){if(!(ex instanceof WebAssembly.RuntimeError))throw ex;got=true;}
   if(got!==trap)throw Error('trap '+q.path+' '+args);copies++;if(got)trapCopies++;
  }
  if(trap)failures++;observe();
 }
 rows.push({path:q.path,steps:inputs(a.length).length,trappingSteps:failures});
}
console.log(JSON.stringify({binaries:rows.length,copies,digests,calls:copies+digests,trapCopies,byteComparisons,mismatches:0,rows}));
