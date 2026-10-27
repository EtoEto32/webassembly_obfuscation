const fs=require('fs');
const file=process.argv[2],out=process.argv[3];
if(fs.existsSync(out))throw Error('output exists');
const bytes=fs.readFileSync(file),w=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
let queries=0;const trace=[];const mask=(1n<<64n)-1n;
function pack(a){let x=0n;for(let i=0;i<8;i++)x|=BigInt(a[i])<<BigInt(8*i);return BigInt.asIntN(64,x)}
function unpack(v){v&=mask;return Array.from({length:8},(_,i)=>Number((v>>BigInt(8*i))&255n))}
function query(xs,d){const result=unpack(w.run(pack(xs),pack(Array(8).fill(d))));queries++;trace.push({x:xs,d,result});return result}
const start=process.hrtime.bigint();const tables=Array.from({length:8},()=>[]);
for(let d=0;d<256;d++){
 const lower=query(Array(8).fill(0),d),upper=query(Array(8).fill(255),d);
 let lo=Array(8).fill(0),hi=Array(8).fill(255);
 while(hi.some((v,i)=>lower[i]!==upper[i]&&v-lo[i]>1)){
  const mid=hi.map((v,i)=>(v+lo[i])>>1),values=query(mid,d);
  for(let i=0;i<8;i++)if(lower[i]!==upper[i]&&hi[i]-lo[i]>1){if(values[i]>lower[i])hi[i]=mid[i];else lo[i]=mid[i]}
 }
 for(let i=0;i<8;i++)tables[i].push({lo:lower[i],hi:upper[i],t:lower[i]===upper[i]?0:lower[i]+1-hi[i]});
}
const elapsedMs=Number(process.hrtime.bigint()-start)/1e6;
fs.writeFileSync(out,JSON.stringify({input:file,node:process.version,v8:process.versions.v8,queries,elapsedMs,tables,trace},null,2));
