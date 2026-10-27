const fs=require('fs'),path=require('path');
const root=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let rng=20261019;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
function calc(e,x,y){
 const op=e[0];if(op==='local.get')return (e[1]==='0'?x:y)|0;if(op==='i32.const')return Number(e[1])|0;
 const a=calc(e[1],x,y),b=calc(e[2],x,y),s=b&31;
 switch(op){case 'i32.add':return (a+b)|0;case 'i32.sub':return (a-b)|0;case 'i32.mul':return Math.imul(a,b);case 'i32.xor':return a^b;case 'i32.and':return a&b;case 'i32.or':return a|b;case 'i32.shl':return a<<s;case 'i32.shr_u':return (a>>>s)|0;case 'i32.rotl':return (a<<s)|(a>>>((32-s)&31));case 'i32.rotr':return (a>>>s)|(a<<((32-s)&31));default:throw Error(op);}
}
const edge=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff],cases=[];
for(const x of edge)for(const y of edge)cases.push([x,y]);
for(let i=0;i<32;i++){const x=(2**i)>>>0;cases.push([x,0],[0,x],[x,~x],[~x,x]);}
for(let i=0;i<4096;i++)cases.push([random(),random()]);
const records=[];let calls=0;
for(const row of manifest.files){const bytes=fs.readFileSync(path.join(root,row.path));if(!WebAssembly.validate(bytes))throw Error(row.path);const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 for(const [x,y] of cases){const actual=run(x,y),expected=calc(manifest.models[row.model],x,y);if(actual!==expected)throw Error(JSON.stringify({row,x,y,actual,expected}));calls++;}
 records.push({path:row.path,calls:cases.length});}
console.log(JSON.stringify({binaries:records.length,calls,mismatches:0,traps:0,boundary:64,walking_bit:128,random:4096,seed:20261019,records}));
