'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const out=path.resolve(process.argv[2]),manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const digestSize={adler32:4,crc32:4,md5:16,sha1:20,sha256:32,sha512:64,xxhash32:4,xxhash64:8};
function val(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;const a=val(e[1],args),b=val(e[2],args);switch(e[0]){case'add':return(a+b)>>>0;case'sub':return(a-b)>>>0;case'and':return(a&b)>>>0;default:throw Error('expression');}}
function union(rs){const out=[];for(const [l,h]of rs.filter(([l,h])=>l<h).sort((a,b)=>a[0]-b[0])){const p=out.at(-1);if(p&&l<=p[1])p[1]=Math.max(h,p[1]);else out.push([l,h]);}return out;}
function ranges(summary,args,lo,hi){if(summary.kind==='full')return[[lo,hi]];assert.equal(summary.kind,'ranges');return union(summary.writes.map(w=>{const l=val(w.addr,args)+w.offset;return[Math.max(lo,l),Math.min(hi,l+val(w.length,args))];}));}
const initArgs=name=>name==='crc32'?[0xedb88320]:name==='sha256'?[256]:name==='sha512'?[512]:[0];
const memory=e=>new Uint8Array(e.memory.buffer);
const put=(e,data)=>memory(e).set(data,e.Hash_GetBuffer());
function init(e,name){memory(e).fill(0,e.Hash_GetBuffer(),e.Hash_GetBuffer()+16);e.Hash_Init(...initArgs(name));}
function update(e,data){put(e,data);e.Hash_Update(data.length);}
function oracle(name,input){if(['md5','sha1','sha256','sha512'].includes(name))return crypto.createHash(name).update(input).digest('hex');
 if(name==='adler32'){let a=1,b=0;for(const x of input){a=(a+x)%65521;b=(b+a)%65521;}return(((b<<16)|a)>>>0).toString(16).padStart(8,'0');}
 if(name==='crc32'){let c=0xffffffff;for(const x of input){c^=x;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return((c^0xffffffff)>>>0).toString(16).padStart(8,'0');}return null;}
let seed=20261024;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const lengths=[0,1,31,63,64,65,127,128,129,1024,16384,...Array.from({length:24},()=>rand()%4097)];
const data=lengths.map(n=>Uint8Array.from({length:n},()=>rand()&255));
const prefix=Uint8Array.from({length:17},(_,i)=>(i*19+2)&255);
(async()=>{
 const rows=[];
 for(const row of manifest){if(row.status!=='built')continue;
  const bytes=fs.readFileSync(path.join(out,row.file));assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),row.sha256);
  const e=(await WebAssembly.instantiate(bytes)).instance.exports,o=(await WebAssembly.instantiate(fs.readFileSync(path.join(out,row.original)))).instance.exports;
  const state=e.Hash_GetState(),size=new DataView(e.memory.buffer).getUint32(e.STATE_SIZE.value,true);assert(size>0&&state+size<=e.memory.buffer.byteLength);
  let savedBytes=0,changedBytes=0,independentDigests=0,wholeMemoryChangedBytes=0;const cases=[];
  for(const input of data){
   init(e,row.algorithm);init(o,row.algorithm);update(e,prefix);update(o,prefix);
   if(row.operation==='Hash_Final'){update(e,input);update(o,input);}else if(row.operation==='Hash_Update'){put(e,input);put(o,input);}
   const args=(row.operation==='Hash_Init'?initArgs(row.algorithm):row.operation==='Hash_Update'?[input.length]:[]);while(args.length<3)args.push(0);
   const before=memory(e).slice(),R=before.slice(state,state+size),save=ranges(row.summary,args,state,state+size),kept=save.map(([l,h])=>[l,before.slice(l,h)]);
   e.callback(...args);o[row.operation](...args.slice(0,row.params));
   const after=memory(e),view=after.slice(state,state+size);for(const[l,part]of kept)view.set(part,l-state);assert.deepEqual(view,R,row.file);
   assert.deepEqual(after,memory(o),'wrapper changed library behavior');let changed=0,changedAll=0;
   for(let i=0;i<after.length;i++)if(after[i]!==before[i]){changedAll++;if(i>=state&&i<state+size)changed++;if(row.summary.kind==='ranges'){
    const covered=row.summary.writes.some(w=>{const l=val(w.addr,args)+w.offset;return l<=i&&i<l+val(w.length,args);});assert(covered,'write outside inferred bound');}}
   const saved=kept.reduce((n,x)=>n+x[1].length,0);savedBytes+=saved;changedBytes+=changed;wholeMemoryChangedBytes+=changedAll;
   if(row.operation==='Hash_Init'){update(e,input);update(o,input);}if(row.operation!=='Hash_Final'){e.Hash_Final();o.Hash_Final();}
   const digest=Buffer.from(memory(e).slice(e.Hash_GetBuffer(),e.Hash_GetBuffer()+digestSize[row.algorithm])).toString('hex');
   const originalDigest=Buffer.from(memory(o).slice(o.Hash_GetBuffer(),o.Hash_GetBuffer()+digestSize[row.algorithm])).toString('hex');assert.equal(digest,originalDigest);
   const expected=oracle(row.algorithm,row.operation==='Hash_Init'?input:Buffer.concat([prefix,input]));if(expected!==null){assert.equal(digest,expected);independentDigests++;}
   cases.push({inputLength:input.length,savedBytes:saved,changedStateBytes:changed,changedMemoryBytes:changedAll,digest});
  }
  rows.push({file:row.file,algorithm:row.algorithm,operation:row.operation,optimized:row.optimized,analysis:row.summary.kind,reason:row.summary.reason,
   stateBytes:size,memoryBytes:e.memory.buffer.byteLength,cases:cases.length,mismatches:0,savedBytes,fullStateBytes:size*cases.length,
   changedBytes,wholeMemoryChangedBytes,independentDigests,inputs:cases});
 }
 const summary={binaryEntries:rows.length,rangeEntries:rows.filter(r=>r.analysis==='ranges').length,fullCopyEntries:rows.filter(r=>r.analysis==='full').length,
 cases:rows.reduce((n,r)=>n+r.cases,0),mismatches:0,independentDigestChecks:rows.reduce((n,r)=>n+r.independentDigests,0),
 savedBytes:rows.reduce((n,r)=>n+r.savedBytes,0),fullStateBytes:rows.reduce((n,r)=>n+r.fullStateBytes,0)};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({summary,rows,scope:'third-party library bodies in a research harness; state old-value contract; not deployment in an existing third-party application'},null,2));
 const lines=['# hash-wasm 4.12.0 適用範囲','', '|algorithm|operation|O3|analysis|state bytes|saved / full (35 calls)|reason|','|---|---|---|---|---:|---:|---|',
 ...rows.map(r=>`|${r.algorithm}|${r.operation}|${r.optimized}|${r.analysis}|${r.stateBytes}|${r.savedBytes} / ${r.fullStateBytes}|${r.reason??''}|`),
 '', '既存save()はstateと4byteのbinary識別子を保持する。全memoryをコピーする対照とは区別する。上記は長寿命save()と同じAPIではない。'];
 fs.writeFileSync(path.join(out,'report.md'),lines.join('\n'));console.log(JSON.stringify(summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
