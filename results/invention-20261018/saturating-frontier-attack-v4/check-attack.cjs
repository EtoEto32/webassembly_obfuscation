'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const dir=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),attack=JSON.parse(fs.readFileSync(path.join(out,'attack.json')));
let seed=20261018,cases=0;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
function evaluate(e,a){if(e.term){let v=e.term[e.term.length-1];for(let j=0;j<a.length;j++)v+=e.term[j]*(a[j]&65535);return Math.min(65535,v);}
 if(e.add)return Math.min(65535,e.add.reduce((s,x)=>s+evaluate(x,a),0));return Math.min(...e.min.map(x=>evaluate(x,a)));}
const rows=[];
for(const r of attack.rows){const bytes=fs.readFileSync(path.join(dir,r.file));if(crypto.createHash('sha256').update(bytes).digest('hex')!==r.sha256)throw Error('hash');const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 let mismatches=0;for(let i=0;i<4096;i++){const a=Array.from({length:r.inputs},()=>rnd()%(i%2?1024:0x100000000));if(fn(...a)!==evaluate(r.expression,a))mismatches++;cases++;}
 rows.push({file:r.file,cases:4096,mismatches});}
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({node:process.version,cases,rows},null,2),{flag:'wx'});fs.copyFileSync(__filename,path.join(out,'check-attack.cjs'));
console.log({cases,mismatches:rows.reduce((s,r)=>s+r.mismatches,0)});if(rows.some(r=>r.mismatches))process.exitCode=1;
