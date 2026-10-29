const fs=require('fs'),path=require('path');const dir=process.argv[2],spec=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const xs=[0,1,2,3,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa,0x55555555];let seed=221020;
for(let i=0;i<4096;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;xs.push(seed>>>0);}
function oracle(x,depth){let value=BigInt(x);for(let i=0;i<depth;i++)value=(value*value+3n*value+5n)&0xffffffffn;return Number(value);}
const rows=[];
for(const t of spec){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,t.file)))).exports;
 for(const x of xs)if((e.run(x)>>>0)!==oracle(x,t.depth))throw Error(t.file+' '+x);
 rows.push({file:t.file,depth:t.depth,calls:xs.length,mismatches:0});
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,rows,calls:rows.reduce((a,r)=>a+r.calls,0),oracle:'BigInt with explicit modulo 2^32 after each recurrence'}));
