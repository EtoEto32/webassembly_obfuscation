const fs=require('fs'),path=require('path');
const root=process.argv[2],man=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed=0x261019;function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0}
function reference(name,args,mem){const [p,q,n,v,c]=args;let trap=false;
 function put(a,v,k){if(a+k>mem.length){trap=true;return false;}for(let i=0;i<k;i++)mem[a+i]=v>>>(8*i);return true}
 function fill(a,v,k){if(a+k>mem.length){trap=true;return false}mem.fill(v&255,a,a+k);return true}
 function copy(a,b,k){if(a+k>mem.length||b+k>mem.length){trap=true;return false}mem.copyWithin(a,b,b+k);return true}
 if(name==='byte'){if(c)put(p,v,1);else put(q,v^165,1)}
 if(name==='wide'){if(v<n){if(put(p+7,Math.imul(v,2654435761)>>>0,4))put(q+1,n,2)}else{if(put(q+3,v^n,2))put(p,c,1)}}
 if(name==='nested'){if(c){if(put(p,v,1)){if(v&1)put(q+2,n,4);else put(p+11,n,2)}}else{if(put(p,(v+n)>>>0,4))put(q,v,1)}}
 if(name==='bulk'){if(c){if(copy(p,q,n))put(p+4,v,4)}else{if(fill(q,v,n))put(p,v>>>8,1)}}
 return {trap,value:(v^n)>>>0};
}
const rows=[];let calls=0,traps=0;
for(const item of man.files){const binary=fs.readFileSync(path.join(root,item.path));let itemCalls=0,itemTraps=0;
 for(const pages of [0,1,2]){const e=new WebAssembly.Instance(new WebAssembly.Module(binary)).exports;e.memory.grow(pages);
  const mem=new Uint8Array(e.memory.buffer),initial=new Uint8Array(mem.length);for(let i=0;i<initial.length;i++)initial[i]=(i*73+(i>>>7)*11+41)&255;
  const cases=[],end=mem.length,addrs=[0,1,2,Math.max(0,end-14),Math.max(0,end-11),Math.max(0,end-7),Math.max(0,end-4),Math.max(0,end-1),end,end+1,0xfffffffe,0xffffffff];
  for(const a of addrs)for(const b of [0,Math.max(0,end-2),0xffffffff])for(const v of [0,1,0x80000000,0xffffffff])for(const flag of [0,1,2,0x80000000])cases.push([a,b,16,v,flag]);
  for(let i=0;i<256;i++)cases.push([i%3?rnd()%Math.max(1,end+16):rnd(),i%4?rnd()%Math.max(1,end+16):rnd(),[0,1,2,4,8,16,0xffffffff][i%7],rnd(),rnd()&3]);
  for(const args of cases){mem.set(initial);const want=initial.slice(),expected=reference(item.model,args,want);let trap=false,value;
   try{value=e.run(...args)>>>0}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true}
   if(trap!==expected.trap||(!trap&&value!==expected.value)||Buffer.compare(Buffer.from(mem),Buffer.from(want))!==0)throw Error(JSON.stringify({item,pages,args,trap,expected}));
   calls++;itemCalls++;if(trap){traps++;itemTraps++;}
  }
 }
 rows.push({path:item.path,calls:itemCalls,traps:itemTraps});
}
console.log(JSON.stringify({binaries:man.files.length,calls,traps,mismatches:0,pages:[0,1,2],rows}));
