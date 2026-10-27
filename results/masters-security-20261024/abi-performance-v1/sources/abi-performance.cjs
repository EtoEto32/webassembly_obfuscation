'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const source=path.resolve(process.argv[2]),mode=process.argv[3],destination=path.resolve(process.argv[4]);
const cases=[['tiny',1,1,64,1],['shared-accept',8,8,64,1],['shared-deny',16,16,64,1],['disjoint-deny',16,16,64,0],['large-shared-deny',32,32,512,1],['empty-leaves',32,32,0,1]];
(async()=>{
 const cfg={mode,budget:8192,last:null};let hostCalls=0;
 const consume=value=>{hostCalls++;let cost=1+value.length,total=0;for(const row of value){cost+=1+row.length;for(const bytes of row){cost+=1+bytes.length;total+=bytes.length;}}
  if(cost>cfg.budget)throw Error('late budget');return total;};
 const dir=path.join(source,mode),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
 const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{consume:{default:consume},preflightConfig:cfg});
 const rows=[];
 for(const[name,w,n,s,shared]of cases){
  const want=1+w+w*(1+n+n*(1+s))<=cfg.budget;
  const call=()=>{try{const value=c.run(w,n,s,shared);assert(want);assert.equal(value,w*n*s);}catch(e){assert(!want);assert.match(String(e),/budget/);}};
  global.gc();const before=process.memoryUsage();for(let i=0;i<20;i++)call();
  const samples=[];for(let b=0;b<9;b++){const t=process.hrtime.bigint();for(let i=0;i<50;i++)call();samples.push(Number(process.hrtime.bigint()-t)/50/1000);}
  const after=process.memoryUsage();global.gc();rows.push({name,accepted:want,samples_us:samples,preflight:cfg.last,memoryBefore:before,memoryAfter:after,memoryAfterGC:process.memoryUsage()});
 }
 const result={mode,rows,hostCalls,maxRSS_kib:process.resourceUsage().maxRSS,warmup:20,batches:9,callsPerBatch:50,
  environment:{node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch}};
 fs.writeFileSync(destination,JSON.stringify(result,null,2));console.log(JSON.stringify({mode,hostCalls}));
})().catch(e=>{console.error(e);process.exitCode=1;});
