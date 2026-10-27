const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const packed=Array.from({length:256},(_,x)=>BigInt.asIntN(64,BigInt(x)*0x0101010101010101n));
function unpack(x){x=BigInt.asUintN(64,x);return Array.from({length:8},(_,i)=>Number((x>>BigInt(8*i))&255n))}
function pack(a){let x=0n;for(let i=0;i<8;i++)x|=BigInt(a[i])<<BigInt(8*i);return BigInt.asIntN(64,x)}
function oracle(f,x,y){const cap=f.bits.map(b=>(1<<b)-1),s=unpack(x).map((v,i)=>Math.min(v,cap[i])),d=unpack(y).map((v,i)=>Math.min(v,cap[i]));for(const op of f.ops)for(let i=0;i<8;i++)s[i]=op.sign==='+'?Math.min(cap[i],s[i]+(d[i]&op.mask[i])):Math.max(0,s[i]-(d[i]&op.mask[i]));return pack(s)}
let random=0x102221;function rng(){random^=random<<13;random^=random>>>17;random^=random<<5;return random>>>0}
const extra=Array.from({length:512},()=>[BigInt.asIntN(64,(BigInt(rng())<<32n)|BigInt(rng())),BigInt.asIntN(64,(BigInt(rng())<<32n)|BigInt(rng()))]);
const rows=[];
for(const [name,f] of Object.entries(m.fixtures)){
 const expected=[];for(let x=0;x<256;x++)for(let y=0;y<256;y++)expected.push(oracle(f,packed[x],packed[y]));
 const extraExpected=extra.map(([x,y])=>oracle(f,x,y));
 for(const t of m.targets.filter(t=>t.name===name)){
  const bytes=fs.readFileSync(path.join(root,t.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+t.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;let bad=0,first=null,calls=0;
  for(let x=0;x<256;x++)for(let y=0;y<256;y++){const actual=run(packed[x],packed[y]),want=expected[x*256+y];calls++;if(actual!==want){bad++;first??={x,y,actual:String(actual),expected:String(want)}}}
  extra.forEach(([x,y],i)=>{const actual=run(x,y),want=extraExpected[i];calls++;if(actual!==want){bad++;first??={x:String(x),y:String(y),actual:String(actual),expected:String(want)}}});
  rows.push({file:t.file,mode:t.mode,calls,mismatches:bad,first});
  if(t.mode==='bad'?bad===0:bad!==0)throw Error(JSON.stringify(rows.at(-1)));
 }
}
fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify({node:process.version,v8:process.versions.v8,rows,positiveCalls:rows.filter(x=>x.mode!=='bad').reduce((a,x)=>a+x.calls,0)},null,2));
