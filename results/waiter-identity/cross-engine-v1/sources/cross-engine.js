/* Globals are supplied by the engine-specific test adapter. */
(async function(){
  const assert=(ok,message)=>{if(!ok)throw new Error(message);},rows=[];let memoriesChecked=0,bytesCompared=0;
  function* partitions(n,a=[0]){if(a.length===n){yield a.slice();return;}for(let i=0;i<=1+Math.max(...a);i++)yield* partitions(n,[...a,i]);}
  const cases=[];for(let n=1;n<=6;n++)for(const p of partitions(n))cases.push(p);
  let seed=2026102418;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
  for(const n of [8,16,32,64])for(const k of [1,2,4]){
    const a=Array.from({length:n},(_,i)=>i%k);for(let i=n-1;i>0;i--){const j=rand()%(i+1);[a[i],a[j]]=[a[j],a[i]];}
    const seen=[];cases.push(a.map(x=>{if(!seen.includes(x))seen.push(x);return seen.indexOf(x);}));
  }
  for(const labels of cases){
    const backing=Array.from({length:Math.max(...labels)+1},()=>new WebAssembly.Memory({initial:1,maximum:4,shared:true}));
    for(const m of backing)new Uint8Array(m.buffer).fill(17);
    const input=labels.map(i=>cloneMemory(backing[i]));
    assert(input.every((m,i)=>m!==backing[labels[i]]),'clone wrapper identity');
    const result=await partitionApi.partition(input);
    assert(JSON.stringify(result.labels)===JSON.stringify(labels),'partition');assert(result.registrations===labels.length,'registrations');assert(result.notifications===backing.length,'notifications');
    for(const m of backing){const a=new Uint8Array(m.buffer);for(let i=0;i<a.length;i++)assert(a[i]===17,'byte changed');memoriesChecked++;bytesCompared+=a.length;}
    rows.push({labels:result.labels,registrations:result.registrations,notifications:result.notifications});
  }
  const wasm=new WebAssembly.Module(pairBytes),pairs=[];
  for(const alias of [false,true])for(const clone of [false,true]){
    const a=new WebAssembly.Memory({initial:1,maximum:4,shared:true}),base=alias?a:new WebAssembly.Memory({initial:1,maximum:4,shared:true}),b=clone?cloneMemory(base):base;
    const p=await partitionApi.partition([a,b]);const instance=new WebAssembly.Instance(wasm,{env:{a:p.memories[0],b:p.memories[1]}});const value=instance.exports.run(123456);
    assert(value===(alias?123456:0),'pair value');assert((p.labels[0]===p.labels[1])===alias,'pair classification');pairs.push({alias,clone,value,labels:p.labels});
  }
  const growing=new WebAssembly.Memory({initial:1,maximum:4,shared:true}),old=growing.buffer;growing.grow(1);const copied=cloneMemory(growing);
  const growLabels=(await partitionApi.partition([growing,copied])).labels;assert(JSON.stringify(growLabels)==='[0,0]','grow');
  const grow={oldBytes:old.byteLength,currentBytes:growing.buffer.byteLength,cloneBytes:copied.buffer.byteLength,labels:growLabels};
  const negatives=[];
  for(const input of [[new WebAssembly.Memory({initial:1})],[new WebAssembly.Memory({initial:0,maximum:4,shared:true})],[{buffer:new SharedArrayBuffer(65536)}]]){
    let rejected=false;try{await partitionApi.partition(input);}catch(e){rejected=true;}assert(rejected,'negative');negatives.push({rejected});
  }
  const x=new WebAssembly.Memory({initial:1,maximum:4,shared:true});Object.defineProperty(x,'buffer',{value:new SharedArrayBuffer(65536)});
  const shadowLabels=(await partitionApi.partition([x,cloneMemory(x)])).labels;assert(JSON.stringify(shadowLabels)==='[0,0]','builtin getter shadow');
  const result={engine:engineDescription,conditions:rows.length,memoriesChecked,bytesCompared,rows,pairs,grow,negatives,shadowLabels,timers:timerMode};
  finishTest(result);
})().catch(failTest);
