const fs=require('fs'),path=require('path');const dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'boundary-input.json')));let checks=0,bad=0,traps=0;
const mem=new Uint8Array(65536);for(let i=0;i<32;i++)mem[i]=i;mem.set([1,2,3,4,5,6,7,8],65528);mem[65535]=165;
const details=[];let st=0x651635;const random=()=>{st^=st<<13;st^=st>>>17;st^=st<<5;return st>>>0;};
for(const r of rows){const limit=Math.floor((65535-Math.max(...r.offsets))/2**r.shift);
 const inputs=[...Array.from({length:33},(_,i)=>i),Math.max(0,limit-1),limit,limit+1,0x7fffffff,0x80000000,0xffffffff,...Array.from({length:128},random)];
 for(const file of [r.original,r.projected]){const bytes=fs.readFileSync(path.join(dir,file));if(!WebAssembly.validate(bytes))throw Error('validate');
 const f=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;let failures=0;
 for(const x of inputs){const base=Number((BigInt(x>>>0)*(1n<<BigInt(r.shift)))&0xffffffffn),a=base+r.offsets[0],b=base+r.offsets[1];
 const expected=a>=65536||b>=65536?'trap':mem[a]^mem[b];let got;
 try{got=f(x)>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError)||!/memory access out of bounds/i.test(e.message))throw e;got='trap';traps++;}
 if(got!==expected)failures++;checks++;}bad+=failures;details.push({file,inputs:inputs.length,mismatches:failures});}}
fs.writeFileSync(path.join(dir,'boundaries.json'),JSON.stringify({checks,bad,traps,details},null,2));console.log(JSON.stringify({checks,bad,traps}));if(bad)process.exitCode=1;