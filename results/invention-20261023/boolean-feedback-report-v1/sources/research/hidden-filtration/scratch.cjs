const fs=require('fs'),path=require('path');
let seed=0x37251649;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
const rot=(x,r)=>(x<<r)|(x>>>(32-r));
const oracle={
mix8:(x,y)=>{let a=rot(x,3),b=rot(y,27),c=a&b,d=c^x,e=rot(d,5),f=d^y;return(e&f)^x;},
select10:(x,y)=>{let a=rot(x,11),b=x^y,c=a&b,d=c|y,e=rot(d,7),f=e^a,g=f&d,h=rot(g,13);return(h^b)|x;},
chain12:(x,y)=>{let a=rot(x,3),b=rot(y,17),c=a^b,d=c&x,e=rot(d,9),f=e^y,g=f|d,h=g&c,i=rot(h,23),j=i^e;return(j&g)^a;}
};
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let calls=0;
for(const row of rows){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(row.file))).exports;
 const bytes=new Uint8Array(e.memory.buffer),words=new Int32Array(e.memory.buffer),prefix=bytes.slice(0,row.prefix);
 for(let i=0;i<256;i++){
  for(let j=row.old/4;j<Math.ceil(row.end/4);j++)words[j]=rng();
  bytes.fill(0xa7,row.end);const x=rng(),y=rng();
  if(e.run(x,y)!==(oracle[row.name](x,y)|0))throw Error(row.file+' random state changed answer');
  if(!Buffer.from(prefix).equals(Buffer.from(bytes.subarray(0,row.prefix))))throw Error('descriptor changed');
  if(bytes.subarray(row.end).some(x=>x!==0xa7))throw Error('scratch bounds exceeded');
  calls++;
 }
}
console.log(JSON.stringify({targets:rows.length,calls,mismatches:0,descriptor_and_tail_checks:calls,seed:'0x37251649'}));
