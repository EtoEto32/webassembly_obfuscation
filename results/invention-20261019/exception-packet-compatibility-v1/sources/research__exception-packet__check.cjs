const fs=require('fs'),path=require('path');
const dir=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function rotl(x,n){return (x<<n)|(x>>>(32-n));}
function oracle(kind,k,x,y,z){let h=x|0;for(let j=0;j<k;j++){
 let c=(z & (j%2===0?1:0x80000000));let a,b;
 if(kind==='blend'){a=rotl((x+j*123+17)|0,j%31+1);b=Math.imul(y^(j*311+91),j*2+3);h^=c?a:b;}
 else {a=(h+(j+1)*12345)|0;b=rotl(h^y,j%31+1);if(kind==='rolling')c=(x>>>(j%8))&1;h=c?a:b;}
 }return h|0;}
const edge=[0,1,2,-1,-2147483648,2147483647,0x55555555,0xaaaaaaaa|0],inputs=[];
for(const x of edge)for(const y of edge)for(const z of edge)inputs.push([x,y,z]);
let seed=0x51a22d13;function next(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
for(let i=0;i<512;i++)inputs.push([next(),next(),next()]);
let calls=0,mismatches=0,exceptions=0;const rows=[];
for(const row of manifest.files){for(const field of ['file','recovered']){if(!row[field])continue;
 const bytes=fs.readFileSync(path.join(dir,row[field]));let errors=0;
 if(!WebAssembly.validate(bytes))throw Error('Validation failed '+row[field]);
 const f=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 for(const xs of inputs){let actual;calls++;try{actual=f(...xs);}catch(e){exceptions++;errors++;continue;}if(actual!==oracle(row.kernel,row.k,...xs)){mismatches++;errors++;}}
 rows.push({file:row[field],calls:inputs.length,errors});
}}
const result={status:mismatches||exceptions?'failed':'passed',inputs:inputs.length,calls,mismatches,unexpected_exceptions:exceptions,rows};
fs.writeFileSync(path.join(dir,'correctness.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({calls,mismatches,exceptions}));
if(mismatches||exceptions)process.exitCode=1;
module.exports={oracle};
