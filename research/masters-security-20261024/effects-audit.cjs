'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const out=path.resolve(process.argv[2]),manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
function val(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;const a=val(e[1],args),b=val(e[2],args);
 if(e[0]==='add')return(a+b)>>>0;if(e[0]==='sub')return(a-b)>>>0;if(e[0]==='and')return(a&b)>>>0;throw Error('expression');}
(async()=>{let cases=0,traps=0,changed=0;const entries=[];
 for(const e of manifest){const bytes=fs.readFileSync(path.join(out,e.file));assert(WebAssembly.validate(bytes));
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),e.sha256);
  let instance;instance=(await WebAssembly.instantiate(bytes,{host:{mutate(){new Uint8Array(instance.exports.memory.buffer)[31]^=255;}}})).instance;
  let seed=20261024;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
  const inputs=[[0,255,0],[1,255,1],[0xffffffff,255,2],[0xfffffffc,255,3],[65535,255,63],[65536,255,64]];
  for(let i=0;i<64;i++)inputs.push([rand()%70000,rand(),rand()]);let localTraps=0,localChanged=0;
  for(const args of inputs){const memory=instance.exports.memory,v=new Uint8Array(memory.buffer);
   for(let i=0;i<v.length;i++)v[i]=(i*7+13)&255;const before=v.slice();
   const spans=e.summary.kind==='full'?[[0,v.length]]:e.summary.writes.map(w=>{const l=val(w.addr,args)+w.offset;return[l,l+val(w.length,args)];});
   try{instance.exports.callback(...args);}catch(err){assert(err instanceof WebAssembly.RuntimeError);localTraps++;}
   const after=new Uint8Array(memory.buffer);
   // Independent observation checks every changed byte, including those not
   // in a host read contract. Equal-value writes are not dynamically detected.
   for(let i=0;i<before.length;i++)if(before[i]!==after[i]){localChanged++;assert(spans.some(([l,h])=>l<=i&&i<h),e.file+': missing byte '+i);}
  }
  cases+=inputs.length;traps+=localTraps;changed+=localChanged;
  entries.push({file:e.file,kind:e.summary.kind,cases:inputs.length,traps:localTraps,observedChangedBytes:localChanged});
 }
 const result={modules:entries.length,cases,traps,observedChangedBytes:changed,uncoveredChangedBytes:0,entries};
 fs.writeFileSync(path.join(out,'audit.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,entries:undefined}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
