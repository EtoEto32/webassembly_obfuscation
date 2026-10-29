'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const initial=c=>Uint8Array.from({length:65536},(_,i)=>(i*17+c*13)&255);
class Trap extends Error{}
function model(rec,p){
 const memories=Array.from({length:Math.max(...p)+1},(_,c)=>initial(c));let dropped=false;
 for(let i=0;i<rec.n;i++){memories[p[i]][20]=65+i;memories[p[i]][21]=81+i;}
 const range=(a,i,n)=>{if(i+n>a.length)throw new Trap();};
 return {memories,run(args){const [a,b,c]=args.map(x=>x>>>0),z=memories[p[0]],k=memories[p[rec.n-1]];let value=null,status='complete';
  try{switch(rec.kind){
   case 'store_load':range(z,a,4);new DataView(z.buffer).setUint32(a,b,true);range(k,a,4);value=new DataView(k.buffer).getUint32(a,true);break;
   case 'overlap_copy':range(k,a,c);range(z,b,c);k.set(z.slice(b,b+c),a);range(k,a,1);value=k[a];break;
   case 'copy_chain':for(let i=1;i<rec.n;i++){const dst=memories[p[i]],src=memories[p[i-1]];range(dst,a,c);range(src,b,c);dst.set(src.slice(b,b+c),a);}range(k,a,1);value=k[a];break;
   case 'fill_load':range(z,a,c);z.fill(b&255,a,a+c);range(k,a,1);value=k[a];break;
   case 'grow_size':{const old=z.length/65536;if(a<=3-old){const next=new Uint8Array((old+a)*65536);next.set(z);memories[p[0]]=next;}value=memories[p[rec.n-1]].length/65536;break;}
   case 'write_trap':z[7]=b&255;range(k,a,4);value=new DataView(k.buffer).getUint32(a,true);break;
   case 'branch':{const target=b&1?z:k;range(target,a,1);target[a]=(b&1?b:c)&255;range(k,a,1);value=k[a];break;}
   case 'data_drop':dropped=true;
   case 'data_init':{const data=dropped?new Uint8Array():Buffer.from('abcdefghijklmnop');range(k,a,c);range(data,b,c);k.set(data.slice(b,b+c),a);range(z,a,1);value=z[a];break;}
   default:throw Error(rec.kind);
  }}catch(e){if(!(e instanceof Trap))throw e;status='trap';}
  return {status,value};
 }};
}
function engine(rec,alias,stem,isQuotient){
 const p=alias.partition,memories=Array.from({length:Math.max(...p)+1},(_,c)=>{const m=new WebAssembly.Memory({initial:1,maximum:3});new Uint8Array(m.buffer).set(initial(c));return m;});
 const env={};for(let i=0;i<rec.n;i++)if(!isQuotient||alias.representatives.includes(i))env['m'+i]=memories[p[i]];
 const bytes=fs.readFileSync(path.join(root,rec.folder,stem+'.wasm'));assert(WebAssembly.validate(bytes));
 const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes),{env});
 for(let i=0;i<rec.n;i++)for(let j=0;j<rec.n;j++)assert.equal(instance.exports['m'+i]===instance.exports['m'+j],p[i]===p[j]);
 return {memories,stem,run(args){let value=null,status='complete';try{value=instance.exports.run(...args)>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;status='trap';}return {status,value};}};
}
let checks=0,memoryChecks=0,trapChecks=0,instances=0,mutantsKilled=0,mutantNonAliasMatches=0;
const rows=[];const start=process.hrtime.bigint();
for(const rec of mf.records){let rc=0,rt=0;
 for(const alias of rec.aliases){
  const ref=model(rec,alias.partition),engines=[engine(rec,alias,'original',false),engine(rec,alias,'original-O3',false),engine(rec,alias,'q'+alias.id,true),engine(rec,alias,'q'+alias.id+'-O3',true)];instances+=4;
  function memoryEqual(e){ref.memories.forEach((a,c)=>{assert.deepEqual(Buffer.from(e.memories[c].buffer),Buffer.from(a));memoryChecks++;});}
  engines.forEach(memoryEqual);
  for(const args of mf.inputs){const expected=ref.run(args);for(const e of engines){const actual=e.run(args);assert.deepEqual(actual,expected,JSON.stringify({rec:rec.folder,engine:e.stem,p:alias.partition,args}));memoryEqual(e);checks++;rc++;if(expected.status==='trap'){trapChecks++;rt++;}}}
  if(rec.kind==='store_load'){
   const test=engine(rec,alias,'mutant',false),want=model(rec,alias.partition).run([0,12345678,0]),got=test.run([0,12345678,0]);instances++;
   if(alias.partition[0]===alias.partition[rec.n-1]){assert.notDeepEqual(got,want);mutantsKilled++;}
   else{assert.deepEqual(got,want);mutantNonAliasMatches++;}
  }
 }
 rows.push({fixture:rec.folder,partitions:rec.aliases.length,checks:rc,traps:rt});
}
const result={node:process.version,v8:process.versions.v8,fixtures:mf.records.length,quotients:mf.records.reduce((a,r)=>a+r.aliases.length,0),instances,checks,memoryChecks,trapChecks,mutantsKilled,mutantNonAliasMatches,seconds:Number(process.hrtime.bigint()-start)/1e9,memory:process.memoryUsage(),resourceUsage:process.resourceUsage(),rows,
 limitations:['Mutants are intentionally incorrect load-motion transformations, not vulnerabilities found in V8/Binaryen.','All imported memories have the same 1..3 page limits; no host callbacks or concurrent access.','Sequential calls and passive data-drop state are included; no start function in these fixtures.']};
if(!process.argv.includes('--read-only'))fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
