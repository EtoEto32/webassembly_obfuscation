'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost}=require('./fence-runtime.cjs');
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),{project}=require(path.join(source,'project.cjs'));
const directory=path.join(out,'io');fs.mkdirSync(directory);const files=Array.from({length:3},(_,i)=>path.join(directory,'backend-'+i+'.txt'));
const fds=files.map(file=>fs.openSync(file,'wx+'));let readCalls=0,writeCalls=0;
function read(id){const size=fs.fstatSync(fds[id]).size,buffer=Buffer.alloc(size);let done=0;
 while(done<size){const n=fs.readSync(fds[id],buffer,done,size-done,done);if(!n)throw Error('unexpected EOF');done+=n;}readCalls++;return buffer.toString('utf8');}
function write(id,value){const buffer=Buffer.from(value);let done=0;
 while(done<buffer.length){const n=fs.writeSync(fds[id],buffer,done,buffer.length-done,done);if(!n)throw Error('zero write');done+=n;}
 fs.ftruncateSync(fds[id],buffer.length);writeCalls++;}
const payload='admitted-payload\n';
function execute(plan){switch(plan.tag){case'read':return[read(plan.ids[0])];case'write':write(plan.ids[0],payload);return[];
 case'copy':{const data=read(plan.ids[0]);write(plan.ids[1],data);return[];}
 case'batch':case'optional':for(const id of plan.ids)write(id,payload);return[];case'idle':return[];default:throw Error('effect tag');}}
const variants=[['read',0,0],['write',1,0],['copy',2,0],['batch0',3,0],['batch1',3,1],['batch8',3,8],['optional0',4,0],['optional1',4,1],['idle',5,0]];
const events=[{kind:'none'},...[ [0,'read'],[0,'write'],[1,'read'],[1,'write'],[2,'write'] ].map(([id,permission])=>({kind:'permission',id,permission})),{kind:'release'},{kind:'after'}];
function obligations(mode,count,b){switch(mode){case 0:return[[0,'read']];case 1:return[[0,'write']];case 2:return[[0,'read'],[b,'write']];
 case 3:return Array.from({length:count},(_,i)=>[i%2?b:0,'write']);case 4:return[[0,'write'],...(count?[[b,'write']]:[])];case 5:return[];default:throw Error('oracle');}}
function expectedContents(initial,mode,count,b,admitted){const values=initial.slice(),returned=[];if(!admitted)return{values,returned};
 switch(mode){case 0:returned.push(initial[0]);break;case 1:values[0]=payload;break;case 2:values[b]=initial[0];break;
 case 3:for(let i=0;i<count;i++)values[i%2?b:0]=payload;break;case 4:values[0]=payload;if(count)values[b]=payload;break;}return{values,returned};}
(async()=>{
 const rows=[],failures=[];
 try{
 for(const optimization of ['raw','optimized']){
  const h=createHost(project),plans=new Map(),original=h.imports.prepare;
  h.imports.prepare=value=>{const id=original(value),ticket=h.tickets.get(id);
    plans.set(id,Object.freeze({tag:value.tag,ids:Object.freeze(ticket.slots.map(s=>s.objectId))}));return id;};
  const dir=path.join(source,optimization),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':h.imports});
  for(const b of[1,0])for(const[name,mode,count]of variants)for(const event of events){
   h.reset();const initial=files.map((_,i)=>'initial-'+i+'-'+rows.length+'\n');initial.forEach((v,i)=>write(i,v));c.setup(0,b);
   const id=c.request(mode,count),plan=plans.get(id);plans.delete(id);const deps=obligations(mode,count,b);
   if(event.kind==='permission')h.update(event.id,event.permission);if(event.kind==='release')c.release();
   await Promise.resolve();const before={readCalls,writeCalls};let returned=[];
   const actual=h.admit(id,()=>{returned=execute(plan);});
   if(event.kind==='after')h.update(0,'write');
   const want=!deps.some(([object,permission])=>event.kind==='release'||event.kind==='permission'&&object===event.id&&permission===event.permission);
   assert.equal(actual,want);const expected=expectedContents(initial,mode,count,b,want);
   assert.deepEqual(returned,expected.returned);assert.deepEqual(files.map(file=>fs.readFileSync(file,'utf8')),expected.values);
   const after={readCalls,writeCalls};assert.equal(h.admit(id,()=>execute(plan)),false);assert.deepEqual({readCalls,writeCalls},after);
   if(event.kind!=='release')c.release();h.reset();rows.push({optimization,name,alias:b===0,event,admitted:actual,
    readCalls:after.readCalls-before.readCalls,writeCalls:after.writeCalls-before.writeCalls,contents:expected.values});
  }
  for(const kind of ['io-error','reentrant-revoke']){
   h.reset();c.setup(0,1);const id=c.request(1,0);plans.delete(id);let error=null;
   try{h.admit(id,()=>{if(kind==='io-error')fs.readSync(-1,Buffer.alloc(1),0,1,0);else h.update(0,'write');});}catch(e){error=String(e);}
   assert(error);assert.equal(h.admit(id),false);assert.equal(h.stats().liveTickets,0);c.release();h.reset();failures.push({optimization,kind,error,stats:h.stats()});
  }
  assert.equal(plans.size,0);
 }
 }finally{for(const fd of fds)fs.closeSync(fd);}
 const result={summary:{scenarios:rows.length,mismatches:0,rejected:rows.filter(r=>!r.admitted).length,
   effectReads:rows.reduce((n,r)=>n+r.readCalls,0),effectWrites:rows.reduce((n,r)=>n+r.writeCalls,0),controlledFailures:failures.length},
 rows,failures,scope:'fresh local files only; trusted synchronous executor on one JS thread; admission is not a multi-file transaction; backend fds are host-owned and closed after all tests'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
