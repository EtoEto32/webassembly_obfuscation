'use strict';
const fs=require('fs'),path=require('path');
const mask=(1n<<64n)-1n;
async function load(f){return (await WebAssembly.instantiate(fs.readFileSync(f))).instance.exports.run;}
function oracle(n,steps,x){const cells=Array.from({length:n},(_,i)=>Number((x>>BigInt(2*i))&3n));for(const s of steps){const i=s.cell;cells[i]=s.table[16*cells[(i+n-1)%n]+4*cells[i]+cells[(i+1)%n]];}return cells.reduce((a,v,i)=>a|(BigInt(v)<<BigInt(2*i)),0n);}
function inputs(n){
 const xs=[0n,1n,mask,1n<<63n,(1n<<63n)-1n,0x5555555555555555n,0xaaaaaaaaaaaaaaaan];
 for(let i=0;i<64;i++)xs.push(1n<<BigInt(i),mask^(1n<<BigInt(i)));
 let r=191019;const rand=()=>{r^=r<<13;r^=r>>>17;r^=r<<5;return r>>>0;};
 for(let i=0;i<2048;i++)xs.push((BigInt(rand())<<32n)|BigInt(rand()));
 if(n===4)for(let i=0;i<256;i++)xs.push(BigInt(i));return xs;
}
(async()=>{const mpath=path.resolve(process.argv[2]),dir=path.dirname(mpath),m=JSON.parse(fs.readFileSync(mpath)),rows=[];
 for(const row of m.rows){const r={id:row.id,status:'passed',calls:0,mismatches:0,traps:0};
  try{const fs_=[['original',await load(path.join(dir,row.source))],['target',await load(path.join(dir,row.file))]];if(row.recovered)fs_.push(['recovered',await load(path.join(dir,row.recovered))]);const tests=inputs(row.n);r.inputs=tests.length;
   for(const x of tests){const expected=oracle(row.n,row.rules,x);for(const [name,f] of fs_){try{const got=f(BigInt.asIntN(64,x))&mask;r.calls++;if(got!==expected){r.mismatches++;if(!r.witness)r.witness={name,x:String(x),expected:String(expected),got:String(got)};}}catch(e){r.traps++;r.status='trap';r.error=String(e);}}}
   if(r.mismatches)r.status='mismatch';
  }catch(e){r.status='setup_error';r.error=String(e);}rows.push(r);
 }
 const negative=[];for(const r of m.negative){const f=await load(path.join(dir,r.file));const expected=oracle(r.n,r.rules,0n),got=f(0n)&mask;negative.push({file:r.file,expected:String(expected),got:String(got),detected:got!==expected});}
 const summary={conditions:rows.length,calls:rows.reduce((a,r)=>a+r.calls,0),mismatches:rows.reduce((a,r)=>a+r.mismatches,0),traps:rows.reduce((a,r)=>a+r.traps,0),negative:negative.length,passed:rows.every(r=>r.status==='passed')&&negative.every(r=>r.detected)};
 fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({summary,rows,negative},null,2));console.log(summary);
})().catch(e=>{console.error(e);process.exitCode=1;});
