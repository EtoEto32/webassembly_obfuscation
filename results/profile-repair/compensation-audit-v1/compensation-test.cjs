'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const request=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let seed=2026102426;function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed>>>24;}
const tables=[Buffer.alloc(256),Buffer.from(Array.from({length:256},(_,i)=>i)),Buffer.from(Array.from({length:256},(_,i)=>255-i)),Buffer.alloc(256,255)];
for(let j=0;j<16;j++)tables.push(Buffer.from(Array.from({length:256},random)));
for(let j=0;j<256;j++){const table=Buffer.alloc(256);table[j]=1;tables.push(table);}
const rows=[],traces=[];let calls=0,bytes=0,traps=0;
for(const row of request.rows)for(const version of ['file','optimized']){
 const module=new WebAssembly.Module(fs.readFileSync(path.join(request.directory,row[version])));
 const e=new WebAssembly.Instance(module).exports,memory=Buffer.from(e.memory.buffer);
 for(const n of [0,16,65536]){
  const before=Buffer.from(memory);let trapped=false;try{e.run(n);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trapped=true;}
  if(!trapped||!memory.equals(before))throw new Error('uninitialized guard');traps++;
 }
 let localCalls=0,localBytes=0,profile=null;
 for(let ti=0;ti<tables.length;ti++){
  memory.fill(0xa5);tables[ti].copy(memory);const original=Buffer.from(memory);profile=e.init();
  if(!memory.subarray(0,512).equals(original.subarray(0,512))||!memory.subarray(768).equals(original.subarray(768)))throw new Error('init write outside encoded table');
  const sizes=ti<20?[0,16,32,256,4096,65536]:[256];
  for(const n of sizes){
   for(let i=0;i<n;i++)memory[1024+i]=i&255;
   const before=Buffer.from(memory);e.run(n);calls++;localCalls++;bytes+=n;localBytes+=n;
   for(let i=0;i<n;i++)if(memory[131072+i]!==tables[ti][before[1024+i]])throw new Error('lookup mismatch '+row.mode+' '+version+' '+ti+' '+i);
   if(!memory.subarray(0,131072).equals(before.subarray(0,131072))||!memory.subarray(131072+n).equals(before.subarray(131072+n)))throw new Error('run write outside output');
  }
 }
 for(const n of [-1,1,15,17,65537,0x80000000,0xfffffff0]){
  const before=Buffer.from(memory);let trapped=false;try{e.run(n);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trapped=true;}
  if(!trapped||!memory.equals(before))throw new Error('length guard');traps++;
 }
 rows.push({mode:row.mode,version,calls:localCalls,bytes:localBytes,profile});
}
for(const row of request.rows){
 const logs=[];let trace=[];
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(request.directory,row.trace))),{env:{trace:(id,address)=>{trace.push([id,address>>>0]);return address;}}}).exports;
 const memory=Buffer.from(e.memory.buffer);
 for(let variant=0;variant<4;variant++){
  for(let i=0;i<256;i++)memory[i]=random();e.init();
  for(let i=0;i<256;i++)memory[1024+i]=(i+variant*37)&255;
  trace=[];e.run(256);logs.push(JSON.stringify(trace));
 }
 const identical=logs.every(v=>v===logs[0]);const expected=row.kind!=='scalar'&&!(row.kind==='dispatch'&&e.init()===0);
 if(identical!==expected)throw new Error('address trace expectation '+row.mode);
 traces.push({mode:row.mode,identical,expected,events:JSON.parse(logs[0]).length,traceSHA256:logs.map(v=>require('node:crypto').createHash('sha256').update(v).digest('hex'))});
}
process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,calls,bytes,traps,rows,traces,seed:2026102426,tableCount:tables.length}));
