const fs=require('fs'),path=require('path');
const dir=process.argv[2],spec=JSON.parse(fs.readFileSync(path.join(dir,'helper-cases.json')));
function evalpoly(c,x){let y=0;for(let i=c.length-1;i>=0;i--)y=(Math.imul(y,x)+c[i])>>>0;return y;}
const xs=Array.from({length:16},(_,i)=>i);for(let i=0;i<32;i++)xs.push((2**i)>>>0,((2**i)-1)>>>0);
xs.push(0xffffffff,0xaaaaaaaa,0x55555555);let seed=221017;
for(let i=0;i<64;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;xs.push(seed>>>0);}
let calls=0;
for(const t of spec){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,t.file)))).exports;
 for(let i=0;i<32;i++)for(const x of xs){const got=e['step'+i](x)>>>0;const want=(evalpoly(t.source,(x+2**i)>>>0)-evalpoly(t.source,x))>>>0;const stat=evalpoly(t.polynomials[i],x);calls++;
  if(got!==want||got!==stat)throw Error(JSON.stringify({file:t.file,i,x,got,want,stat}));
 }
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,conditions:spec.length,inputs_per_step:xs.length,calls,mismatches:0}));
