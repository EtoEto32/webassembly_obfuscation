'use strict';const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=process.argv[2],rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const instantiate=name=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,name)))).exports;
let calls=0,states=0,byteChecks=0,expectedTraps=0;const records=[];
for(const row of rows){
  const e=instantiate(row.file),o=instantiate(row.observed),size=row.pages*65536,a=new Uint8Array(size),m=new Uint8Array(o.memory.buffer);
  a.set(Buffer.from('abcdefghijklmnop'),3);a.set(Buffer.from('UVWXYZ'),9);a.set([254,255],size-2);let trace=row.pages===2?97:0;
  if(row.pages===2)a[2]=219;
  const encoded=b=>row.mode==='plain'?b:row.encoding[b&15]|(row.encoding[b>>>4]<<4);
  function verify(){
    for(let i=0;i<size;i++){const want=encoded(a[i])^(row.mode==='plain'?0:row.mask[i&15]);if(m[i]!==want)throw Error(row.file+' memory '+i+': '+m[i]+' vs '+want);byteChecks++;}
    assert.strictEqual(e.trace.value,trace);assert.strictEqual(o.trace.value,trace);states++;
  }
  function invoke(name,args,expected,trap=false){
    for(const inst of [e,o]){calls++;let value,err;try{value=inst[name](...args);}catch(x){err=x;}
      if(trap){assert(err instanceof WebAssembly.RuntimeError,row.file+' missing trap '+name);expectedTraps++;}else{if(err)throw err;assert.strictEqual(value,expected,row.file+' '+name);}
    }
  }
  function copy(d,s,n,name='copy',mark=71){
    d>>>=0;s>>>=0;n>>>=0;
    if(name==='markcopy')a[0]=mark&255;
    if(name==='ordered')for(const tag of [1,2,3])trace=(Math.imul(trace,5)+tag)|0;
    const bad=d+n>size||s+n>size;
    if(!bad)a.copyWithin(d,s,s+n);
    invoke(name,name==='markcopy'?[d,s,n,mark]:[d,s,n],undefined,bad);verify();
  }
  function fill(s){invoke('fill',[s]);for(let i=0;i<size;i++){s=(Math.imul(s,1664525)+1013904223)|0;a[i]=s>>>24;}verify();}
  verify();fill(12345);
  for(const [d,s,n] of [[0,0,0],[size,size,0],[size+1,0,0],[0,size+1,0],[0,0,-1],[-1,0,1],[0,-1,1],[size-1,0,2],[0,size-1,2],[0,1,31],[1,0,31],[3,17,1],[17,3,16],[15,16,17],[16,15,33],[0,0,size],[0,1,size-1],[1,0,size-1]]){
    copy(d,s,n);copy(d,s,n,'ordered');copy(d,s,n,'markcopy');
  }
  let seed=211023;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
  for(let j=0;j<64;j++){
    if(j%16===0)fill(rnd());
    const n=rnd()%258,s=rnd()%(size-n+1),d=j%3===0?Math.min(s+1,size-n):j%3===1?Math.max(s-1,0):rnd()%(size-n+1);
    copy(d,s,n);
    const index=rnd()%size,value=rnd();invoke('write',[index,value]);a[index]=value&255;verify();
    invoke('read',[index],a[index]);invoke('signed',[index],a[index]>=128?a[index]-256:a[index]);
    const len=rnd()%50,start=rnd()%(size-len+1),v=rnd();
    if(len){a.copyWithin(start,start+1,start+len);a[start+len-1]=v&255;}
    invoke('splice',[start,len,v]);verify();
  }
  for(const x of [size,-1,0x80000000]){invoke('write',[x,255],undefined,true);invoke('read',[x],undefined,true);invoke('signed',[x],undefined,true);verify();}
  records.push({file:row.file,mismatches:0,trace_matches:true});
}
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({targets:rows.length,wasm_calls:calls,states,byte_checks:byteChecks,expected_traps:expectedTraps,mismatches:0,unexpected_traps:0,records},null,2));
console.log(JSON.stringify({targets:rows.length,calls,states,byteChecks,expectedTraps}));
