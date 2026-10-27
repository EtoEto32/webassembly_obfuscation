const fs=require('node:fs'),path=require('node:path');
const folder=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(folder,'manifest.json')));
let state=0x51a93c27;
function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state|0;}
function evalTree(t,a){switch(t[0]){case 'var':return a[t[1]]|0;case 'const':return t[1]|0;case 'and':return evalTree(t[1],a)&evalTree(t[2],a);case 'or':return evalTree(t[1],a)|evalTree(t[2],a);case 'xor':return evalTree(t[1],a)^evalTree(t[2],a);default:throw Error(t[0]);}}
const rows={};
for(const [name,f] of Object.entries(m.fixtures)){
 const n=f.n,a=[];
 for(const v of [0,-1,1,-2147483648,0x55555555,0xaaaaaaaa,0x7fffffff])a.push(Array(n).fill(v|0));
 for(let j=0;j<n;j++)for(let k=0;k<32;k++){const z=Array(n).fill(0);z[j]=1<<k;a.push(z);const o=Array(n).fill(-1);o[j]=~(1<<k);a.push(o);}
 for(let k=0;k<2048;k++)a.push(Array.from({length:n},rand));
 if(n<=12)for(let b=0;b<(1<<n);b+=32){const z=Array(n).fill(0);for(let lane=0;lane<32;lane++)for(let j=0;j<n;j++)if(((b+lane)>>j)&1)z[j]|=1<<lane;a.push(z);}
 rows[name]=a;
}
let checks=[];
for(const t of m.targets){
 const bytes=fs.readFileSync(path.join(folder,t.file));
 if(!WebAssembly.validate(bytes))throw Error('Invalid '+t.file);
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 let mismatch=0;
 for(const a of rows[t.fixture])if((e.run(...a)|0)!==evalTree(m.fixtures[t.fixture].tree,a))mismatch++;
 const r={...t,calls:rows[t.fixture].length,mismatches:mismatch};checks.push(r);
 if(mismatch)throw Error(JSON.stringify(r));
}
let negatives=[];
for(const t of m.negative){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(folder,t.file)))).exports;
 let first=null,mismatch=0;
 for(const a of rows[t.fixture]){const got=e.run(...a)|0,want=evalTree(m.fixtures[t.fixture].tree,a);if(got!==want){mismatch++;if(!first)first={input:a,got,want};}}
 if(!mismatch)throw Error('Negative had no witness '+t.file);
 negatives.push({...t,mismatches:mismatch,first});
}
fs.writeFileSync(path.join(folder,'inputs.json'),JSON.stringify(rows));
fs.writeFileSync(path.join(folder,'checks.json'),JSON.stringify({seed:'xorshift32 0x51a93c27',targets:checks,calls:checks.reduce((a,b)=>a+b.calls,0),mismatches:0,negatives},null,2));
console.log(JSON.stringify({targets:checks.length,calls:checks.reduce((a,b)=>a+b.calls,0),mismatches:0,negative:negatives.length}));
