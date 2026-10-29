'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=process.argv[2],rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const instantiate=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,f)))).exports;
const records=[],recovery=[];let wasmCalls=0,stateChecks=0,memoryByteChecks=0,expectedTraps=0;
for(const row of rows){
  const n=row.counters_per_bank,e=row.encoding,real=instantiate(row.file),obs=instantiate(row.observed);
  const memory=new Uint8Array(obs.memory.buffer),banks=[new Uint8Array(n),new Uint8Array(n)];
  const call=(name,...args)=>{wasmCalls+=2;const a=real[name](...args),b=obs[name](...args);assert.strictEqual(a,b,row.file+' observer');return a;};
  const verify=()=>{
    let sum=0;
    for(let i=0;i<n;i++)for(let b=0;b<2;b++){
      assert.strictEqual(call('get',i,b),banks[b][i],row.file+': get '+i+','+b);
    }
    for(let i=0;i<n;i++)sum=(Math.imul(sum,31)+banks[0][i]+banks[1][i])|0;
    assert.strictEqual(call('checksum'),sum,row.file+': checksum');
    for(let i=0;i<memory.length;i++){
      const bank=i<(n/2)?0:1,j=(i%(n/2))*2;
      const want=i<n?(e[banks[bank][j]]|(e[banks[bank][j+1]]<<4)):0;
      assert.strictEqual(memory[i],want,row.file+': memory '+i);memoryByteChecks++;
    }
    stateChecks++;
  };
  const reset=()=>{call('reset');banks.forEach(b=>b.fill(0));};
  const merge=()=>{call('merge');for(let i=0;i<n;i++)banks[0][i]=Math.min(banks[0][i]+banks[1][i],15);};
  const decay=()=>{call('decay');for(let i=0;i<n;i++)banks[0][i]>>=1;};
  const set=(i,b,x)=>{call('set',i,b,x);banks[b][i]=x&15;};
  const init=s=>{
    call('init',s);
    for(let offset=0;offset<n;offset+=16){
      s=(Math.imul(s,1664525)+1013904223)|0;
      for(let j=0;j<16;j++){
        const byte=(s>>>((j%4)*8))&255,bank=offset+j<n/2?0:1,k=((offset+j)%(n/2))*2;
        banks[bank][k]=byte&15;banks[bank][k+1]=byte>>>4;
      }
    }
  };
  verify(); // The start function must establish encoded logical zero.
  for(let i=0;i<n;i++){set(i,0,(i>>4)&15);set(i,1,i&15);}
  verify();merge();verify();decay();verify();reset();verify();
  let seed=211021;
  const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
  for(let k=0;k<128;k++){
    const op=rnd()%5;
    if(op===0)init(rnd());else if(op===1)merge();else if(op===2)decay();
    else if(op===3)reset();else for(let z=0;z<17;z++)set(rnd()%n,rnd()%2,rnd());
    verify();
  }
  init(0x80000000);verify();init(-1);verify();
  for(const i of [0,n-1])for(const b of [0,1])for(const x of [0,15,16,255,-1,0x7fffffff,0x80000000])set(i,b,x);
  verify();
  for(const [i,b] of [[n,0],[-1,0],[0x80000000,0],[0,2],[0,-1],[n,2]]){
    for(const name of ['get','set'])for(const inst of [real,obs]){
      wasmCalls++;assert.throws(()=>inst[name](i,b,15),WebAssembly.RuntimeError);expectedTraps++;
    }
    verify();
  }
  // Adaptation uses only chosen values and observed byte zero, not row.encoding.
  const start=process.hrtime.bigint(),learned=[];
  for(let x=0;x<16;x++){obs.set(0,0,x);wasmCalls++;learned.push(memory[0]&15);}
  const learnMs=Number(process.hrtime.bigint()-start)/1e6;
  assert.strictEqual(new Set(learned).size,16);
  const inverse=Array.from({length:16},(_,c)=>learned.indexOf(c));
  set(0,0,15);init(0x12345678);merge();decay();verify();
  let decoded=0;for(let i=0;i<n;i++)for(let b=0;b<2;b++){
    const code=(memory[b*n/2+(i>>1)]>>>((i&1)*4))&15;
    assert.strictEqual(inverse[code],banks[b][i]);decoded++;
  }
  recovery.push({file:row.file,status:'recovered',chosen_queries:16,learn_ms:learnMs,decoded_counters:decoded,learned});
  records.push({file:row.file,mismatches:0,all_value_pairs:256,random_operations:128,memory_bytes:memory.length});
}
fs.writeFileSync(path.join(dir,'recovery.json'),JSON.stringify(recovery,null,2));
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({targets:rows.length,wasm_calls:wasmCalls,state_checks:stateChecks,memory_byte_checks:memoryByteChecks,expected_traps:expectedTraps,mismatches:0,unexpected_traps:0,records},null,2));
console.log(JSON.stringify({targets:rows.length,wasmCalls,stateChecks,memoryByteChecks,expectedTraps,recovered:recovery.length}));
