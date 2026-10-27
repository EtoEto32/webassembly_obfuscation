const fs=require('fs'),path=require('path');
const dir=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function evaluate(coeff,x){let value=0;for(let k=coeff.length-1;k>=0;k--)value=(Math.imul(value,x)+coeff[k])>>>0;return value;}
const inputs=Array.from({length:4096},(_,i)=>i);
inputs.push(0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa,0x55555555);
for(let i=0;i<32;i++)inputs.push((2**i)>>>0,((2**i)-1)>>>0);
let seed=0x221015;
for(let i=0;i<4096;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;inputs.push(seed>>>0);}
const rows=[],negative=[];
for(const t of manifest.targets){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,t.file)))).exports;
 let wrong=0,traps=0,first=null,checksum=0;
 for(const x of inputs){const want=evaluate(manifest.fixtures[t.name],x);let got=null;try{got=e.run(x)>>>0;}catch(err){traps++;}
  if(got!==want){wrong++;first??={x,want,got};}checksum=(checksum^(got??0))>>>0;
 }
 const row={file:t.file,calls:inputs.length,mismatches:wrong,traps,first,checksum};
 if(t.mode==='bad'){if(!wrong)throw Error('missing counterexample');negative.push(row);}
 else{if(wrong||traps)throw Error(JSON.stringify(row));rows.push(row);}
}
const result={node:process.version,v8:process.versions.v8,input_cases:inputs.length,exhaustive_low_words:4096,random_words:4096,random_seed:0x221015,rows,negative,calls:rows.reduce((n,r)=>n+r.calls,0),traps:rows.reduce((n,r)=>n+r.traps,0)};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({positive:rows.length,calls:result.calls,negative:negative.length,traps:result.traps}));
