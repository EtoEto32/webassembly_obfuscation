const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let rng=0x621021e1;function next(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
function positions(rows){return rows.map(r=>{let v=BigInt(r),a=[];for(let i=0;v;i++,v>>=1n)if(v&1n)a.push(i);return a;});}
function apply(rows,x){return Uint8Array.from(rows,row=>row.reduce((a,i)=>a^x[i],0));}
function digest(x){let h=2166136261;for(const b of x)h=Math.imul(h^b,16777619)>>>0;return h;}
function invoke(e,x,ops,fail){
 const expectedTrap=(fail>>>0)<ops.length;
 for(let j=0;j<ops.length;j++){
  if((fail>>>0)===j)break;
  const [d,s,n]=ops[j];x.copyWithin(d,s,s+n);
 }
 let trap=false;try{e.run(fail);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;}
 return {trap,expectedTrap};
}
const rows=[],negative=[];
for(const target of manifest.targets){
 const bytes=fs.readFileSync(path.join(dir,target.probe));if(!WebAssembly.validate(bytes))throw Error('invalid');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 const n=target.meta.n,b=positions(target.meta.matrix),ops=target.meta.ops,initial=[];
 for(const byte of [0,1,127,128,254,255])initial.push(new Uint8Array(n).fill(byte));
 for(let i=0;i<n;i++){const x=new Uint8Array(n);x[i]=255;initial.push(x);}
 for(let j=0;j<64;j++)initial.push(Uint8Array.from({length:n},()=>next()&255));
 let calls=0,traps=0,mismatches=0,first=null;
 for(let caseIndex=0;caseIndex<initial.length;caseIndex++){
  const x=initial[caseIndex].slice(),memory=new Uint8Array(e.memory.buffer);memory.fill(0);memory.set(apply(b,x));
  const actions=[0xffffffff,...ops.map((_,j)=>j),ops.length,0x80000000,0xffffffff];
  for(const fail of actions){
   const status=invoke(e,x,ops,fail);calls++;traps+=Number(status.trap);
   const physical=apply(b,x),observed=e.digest()>>>0;
   let at=-1;for(let i=0;i<65536;i++)if(memory[i]!== (i<n?physical[i]:0)){at=i;break;}
   const mismatch=at>=0||observed!==digest(x)||status.trap!==status.expectedTrap;
   if(mismatch){mismatches++;if(!first)first={caseIndex,fail,at,observed,expectedDigest:digest(x),status};}
   if(target.mode!=='bad'&&mismatch)throw Error(JSON.stringify({target:target.file,first}));
  }
 }
 const row={file:target.file,initialStates:initial.length,calls,traps,mismatches,first};
 if(target.mode==='bad'){if(!mismatches)throw Error('negative did not fail '+target.file);negative.push(row);}else rows.push(row);
}
const result={node:process.version,v8:process.versions.v8,seed:'0x621021e1',rows,negative,
 calls:rows.reduce((a,r)=>a+r.calls,0),traps:rows.reduce((a,r)=>a+r.traps,0),negativeConditions:negative.length,
 note:'Full 64KiB physical image checked against B*logical state after every call. Diagnostic memory export is not part of the source ABI.'};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({calls:result.calls,traps:result.traps,negativeConditions:result.negativeConditions,mismatches:0}));
