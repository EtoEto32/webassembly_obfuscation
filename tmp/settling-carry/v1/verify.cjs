const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname, manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed=0x77340121;
function next(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const edges=[0,1,2,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,0xaaaaaaaa,0x55555555];
const inputs=[];
for(const x of edges)for(const y of edges)for(const u of [0,1,0xffffffff])inputs.push([x,y,u]);
for(let i=0;i<1024;i++)inputs.push([next(),next(),next()]);
const mask=0xffffffffn;
// Independent, direct scalar interpretation. No carry iteration or compiler helpers.
function reference(nodes,x,y){
 const state=[], env={x:BigInt(x),y:BigInt(y)};
 const val=q=>typeof q==='number'?state[q]:env[q];
 for(const [op,...args] of nodes){
   const a=val(args[0]);let z;
   if(op==='rotl'){const k=BigInt(args[1]);z=(a<<k)|(a>>(32n-k));}
   else if(op==='select')z=val(args[2])!==0n?a:val(args[1]);
   else {const b=val(args[1]);z=op==='add'?a+b:op==='mul'?a*b:op==='xor'?a^b:op==='lt'?(a<b?1n:0n):undefined;}
   if(z===undefined)throw Error('unsupported operator');state.push(z&mask);
 }
 return Number(state.at(-1));
}
const results=[];
for(const b of manifest.binaries){
 const bytes=fs.readFileSync(path.join(root,b.file));
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==b.sha256)throw Error('hash changed');
 const mod=new WebAssembly.Module(bytes);if(WebAssembly.Module.imports(mod).length)throw Error('imports');
 const run=new WebAssembly.Instance(mod).exports.run;
 for(let i=0;i<inputs.length;i++){
   const [x,y,u]=inputs[i], got=run(x,y,u)>>>0, expected=reference(manifest.programs[b.program],x,y);
   if(got!==expected)throw Error(JSON.stringify({file:b.file,i,input:inputs[i],got,expected}));
 }
 results.push({file:b.file,cases:inputs.length,mismatches:0});
}
fs.writeFileSync(path.join(root,'inputs.json'),JSON.stringify(inputs));
const report={node:process.version,v8:process.versions.v8,seed:'0x77340121',results,totalComparisons:results.length*inputs.length};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
