const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));let rows=[];
function s8(x){return (x<<24)>>24}
function oracle(f,x,y){x=BigInt(s8(x));y=BigInt(s8(y));let s=0n;for(let i=0;i<4;i++){let [a,b,c]=f.rows[i].map(BigInt),z=a*x+b*y+c;if(z>0n)s+=BigInt(f.weights[i])*z;}return Number(BigInt.asIntN(32,s));}
for(const [name,f] of Object.entries(m.fixtures)){
 const expect=new Int32Array(65536);for(let x=0;x<256;x++)for(let y=0;y<256;y++)expect[x*256+y]=oracle(f,x,y);
 for(const t of m.targets.filter(t=>t.name===name)){
  const bytes=fs.readFileSync(path.join(root,t.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+t.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;let bad=0,first=null,calls=0;
  for(let x=0;x<256;x++)for(let y=0;y<256;y++){const actual=run(x,y),expected=expect[x*256+y];calls++;if(actual!==expected){bad++;first??={x,y,actual,expected}}}
  for(let i=0;i<512;i++){const x=(Math.imul(i,0x9e3779b1)^0x80000000)|0,y=(Math.imul(i+7,0x85ebca6b)^0x7fffffff)|0;calls++;if(run(x,y)!==expect[(x&255)*256+(y&255)])bad++;}
  rows.push({file:t.file,mode:t.mode,calls,mismatches:bad,first});
  if(t.mode==='bad'?bad===0:bad!==0)throw Error(JSON.stringify(rows.at(-1)));
 }
}
fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify({node:process.version,v8:process.versions.v8,rows,positiveCalls:rows.filter(x=>x.mode!=='bad').reduce((a,x)=>a+x.calls,0)},null,2));
