const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2], cases=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))),targets=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let rows=[];
for(const c of cases){
  let seed=0x731bab39;const rand=()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;
  let calls=[];const bounds=[0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
  for(let op=0;op<4;op++)for(const i of [0,1,c.n-1])for(const j of [0,1,c.n-1])for(const d of bounds)calls.push([op,i,j,d]);
  for(let t=0;t<4096;t++){
    const op=rand()>>>24&3,i=rand()%c.n,j=rand()%c.n,d=rand();calls.push([op,i,j,d]);
    if(t%23===0)calls.push([t%3===0?4:op,t%3===1?c.n:i,t%3===2?0xffffffff:j,d]);
  }
  for(const t of targets.filter(t=>t.name===c.name)){
    const bytes=fs.readFileSync(path.join(root,t.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+t.file);
    const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
    let x=c.initial.slice(),count=0,traps=0,resetCalls=0;
    const expected=([op,i,j,d])=>{
      if(op>3||i>=c.n||j>=c.n)return {trap:true};
      if(op===1)x[i]=(x[i]+d)>>>0;
      if(op===2)x[i]=(x[j]+d)>>>0;
      if(op===3)x[i]=(Math.imul(x[i],c.k)+d)>>>0;
      return {value:(x[i]-x[j])|0};
    };
    function test(args){
      const before=e.memory?new Uint8Array(e.memory.buffer).slice():null;
      const want=expected(args);let got;
      try{got={value:e.run(...args)|0};}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;got={trap:true};}
      count++;if(got.trap)traps++;
      if(got.trap!==want.trap||got.value!==want.value)throw Error(JSON.stringify({file:t.file,args,count,want,got}));
      if(e.memory){
        const physical=new Uint32Array(e.memory.buffer,64,c.n),low=c.erased_bits===32?0:(2**(32-c.erased_bits)-1)>>>0;
        if(t.mode==='canonical'){
          for(let z=0;z<c.n;z++){const want=z===0?(x[0]&low)>>>0:(x[z]-x[0])>>>0;if(physical[z]!==want)throw Error('canonical memory '+t.file);}
        }else{
          const shift=(physical[0]-x[0])>>>0;
          if((shift&low)!==0||t.mode==='plain'&&shift!==0)throw Error('illegal representative shift');
          for(let z=0;z<c.n;z++)if(((physical[z]-x[z])>>>0)!==shift)throw Error('memory relation '+t.file);
        }
        if(got.trap&&!Buffer.from(before).equals(Buffer.from(e.memory.buffer)))throw Error('trap mutated memory');
      }
    }
    for(let i=0;i<calls.length;i++){
      test(calls[i]);
      // Observe both an updated and an unrelated cell after exceptional calls.
      if(i%23===0){test([0,0,c.n-1,0]);test([0,1,0,0]);}
      if(i%997===996){e.reset();x=c.initial.slice();resetCalls++;}
    }
    for(let i=0;i<c.n;i++)test([0,i,0,0]);
    rows.push({...t,calls:count,traps,reset_calls:resetCalls,mismatches:0});
  }
}
console.log(JSON.stringify({binaries:rows.length,calls:rows.reduce((s,r)=>s+r.calls,0),traps:rows.reduce((s,r)=>s+r.traps,0),mismatches:0,rows,node:process.version,v8:process.versions.v8}));
