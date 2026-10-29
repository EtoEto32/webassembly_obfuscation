const fs=require('fs'),path=require('path'),dir=process.argv[2];
let seed=221122;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const inputs=[];
for(const p of [0,4,12,16,65520,65532,65536,0xfffffff0])for(const x of [0,1,3,0x80000000,0xffffffff,0xdeadbeef])for(const n of [0,1,3,17])inputs.push({fn:'run',args:[p,x,n]});
for(let i=0;i<256;i++)inputs.push({fn:'run',args:[i%5===0?rand():rand()%65536,rand(),rand()]});
for(const p of [0,4,12,65532,0xfffffffc])for(const x of [0,1,0x80000000,0xffffffff])inputs.push({fn:'edge',args:[p,x,0]});
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(inputs));
const mask=0xffffffffn,rot=x=>((x<<7n)|(x>>25n))&mask;
function oracle(mem,name,fn,args){
 const [p,x,n]=args.map(v=>v>>>0),base=(p&0xfffffff0)>>>0;
 const get=a=>{if(a+4>mem.byteLength)throw new Error('bounds');return BigInt(mem[a/4]);};
 const put=(a,v)=>{if(a+4>mem.byteLength)throw new Error('bounds');mem[a/4]=Number(v&mask);};
 if(fn==='edge'){put(0,BigInt(x));put(((p&0xfffffffc)>>>0)+4294967292,BigInt(x));return 0;}
 for(let i=0;i<(n&31);i++){
  const j=name==='coupled'?(i+x)&3:i&3,a=base+j*4,b=base+((j+1)&3)*4,u=get(a),v=get(b);
  const z=name==='mix'?rot((u+v+BigInt(x))&mask)^2654435769n:name==='coupled'?u*1664525n+(v^BigInt(x)):u^v^((BigInt(x)+BigInt(i))&mask);
  put(name==='coupled'?b:a,z);
 }
 return Number(get(base)^get(base+12))>>>0;
}
function phase(a,b,c,d){return ((a^(a>>>13))+(b^(b>>>13))+(c^(c>>>13))+(d^(d>>>13)))&3;}
function compare(physical,logical,mode){
 for(let i=0;i<physical.length;i+=4){
  const s=mode==='fixed'?1:(mode==='plain'||mode==='recovered'?0:phase(...physical.subarray(i,i+4)));
  for(let j=0;j<4;j++)if(physical[i+((j+s)&3)]!==logical[i+j])return {index:i+j,physical:physical[i+((j+s)&3)],expected:logical[i+j]};
 }
 return null;
}
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
for(const row of manifest){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.probe)))).exports,mem=new Uint32Array(e.__physical.buffer),ref=new Uint32Array(16384);
 for(let i=0;i<16;i++)ref[i]=Number(BigInt(i+1)*0x9e3779b1n&mask);
 let mismatch=0,traps=0,first=null;
 for(const input of inputs){
  let want,got,t1=false,t2=false;
  try{want=oracle(ref,row.name,input.fn,input.args);}catch(err){t1=true;}
  try{got=e[input.fn](...input.args)>>>0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;t2=true;}
  if(t2)traps++;
  const diff=compare(mem,ref,row.mode);
  if(t1!==t2||(!t1&&want!==got)||diff){mismatch++;if(!first)first={input,want,got,expectedTrap:t1,trap:t2,memory:diff};}
 }
 rows.push({...row,calls:inputs.length,mismatch,traps,first});
 if(!row.negative&&mismatch)throw new Error(JSON.stringify(rows.at(-1)));
 if(row.negative&&!mismatch)throw new Error('negative not detected');
}
const result={inputs:inputs.length,positiveConditions:rows.filter(x=>!x.negative).length,positiveCalls:rows.filter(x=>!x.negative).reduce((s,x)=>s+x.calls,0),results:rows};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({inputs:result.inputs,positiveConditions:result.positiveConditions,positiveCalls:result.positiveCalls,negativeConditions:rows.filter(x=>x.negative).length}));
