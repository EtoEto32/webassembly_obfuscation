'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const{createHost}=require('./fence-runtime.cjs'),out=path.resolve(process.argv[2]);
const before=require(path.join(out,'before.cjs')).project,after=require(path.join(out,'after.cjs')).project;
const events=[null,...[0,1,2].flatMap(id=>['read','write'].map(permission=>({id,permission})))];
(async()=>{
 const rows=[],bindingErrors=[],depthChecks=[];let oldRecordFailures=0,oldOptionFailures=0;
 for(const optimization of['raw','optimized']){
  const h=createHost(after),orig=h.imports.prepare;
  h.imports.prepare=value=>{
   // Only record observations during the borrow lifetime; retain no wrappers.
   const resolver=x=>{const deps=after({firstFile:x,nested:{tag:'none'},batches:[]},hostResolve);return deps[0];};
   function hostResolve(x){if(!localObjects.has(x))throw Error('not a resource leaf');return localObjects.get(x);}
   const localObjects=new WeakMap();let counter=0;
   const add=x=>{if(x!==undefined&&!localObjects.has(x))localObjects.set(x,{slot:counter++,generation:1});};
   add(value.firstFile);if(value.nested.tag==='some')add(value.nested.val);for(const x of value.batches)add(x);
   assert(Object.hasOwn(value,'firstFile'));assert(['none','some'].includes(value.nested.tag));
   try{before(value,hostResolve);throw Error('old record unexpectedly accepted');}catch(e){assert.match(String(e),/record shape/);oldRecordFailures++;}
   try{before({'first-file':value.firstFile,nested:value.nested,batches:value.batches},hostResolve);throw Error('old option unexpectedly accepted');}
   catch(e){assert.match(String(e),/not a resource leaf/);oldOptionFailures++;}
   if(bindingErrors.length<4)bindingErrors.push({optimization,keys:Object.keys(value),nestedTag:value.nested.tag,
    nestedValuePresent:Object.hasOwn(value.nested,'val'),nestedValueUndefined:value.nested.val===undefined,listLength:value.batches.length});
   return orig(value);
  };
  const dir=path.join(out,optimization),api=await import(pathToFileURL(path.join(dir,'unit.js')).href);
  const c=await api.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:shapes/storage':h.imports});
  for(const alias of[false,true])for(let nested=0;nested<3;nested++)for(const count of[0,1,2,8])for(const event of events){
   h.reset();const b=alias?0:1;c.setup(0,b);const id=c.request(nested,count),ticket=h.tickets.get(id);
   const expected=[[0,'read'],...(nested===2?[[b,'write']]:[])];for(let i=0;i<count;i++)if(i%3)expected.push([i%2?b:0,'write']);
   assert.deepEqual(ticket.slots.map(s=>s.objectId),expected.map(d=>d[0]));
   assert.deepEqual(ticket.grants.map(g=>g.object.id+':'+g.permission).sort(),[...new Set(expected.map(d=>d.join(':')))].sort());
   if(event)h.update(event.id,event.permission);await Promise.resolve();
   const want=!expected.some(([id,p])=>event&&event.id===id&&event.permission===p);assert.equal(h.admit(id),want);
   c.release();h.reset();rows.push({optimization,alias,nested,count,event,admitted:want});
  }
  h.shutdown();
 }
 // Explicit independent representations from Jco's generated TS, depth 1..4.
 const handle={slot:0,generation:1},handle2={slot:1,generation:1};
 const values={1:[undefined,handle2],2:[{tag:'none'},{tag:'some',val:undefined},{tag:'some',val:handle2}],
  3:[undefined,{tag:'none'},{tag:'some',val:undefined},{tag:'some',val:handle2}],
  4:[{tag:'none'},{tag:'some',val:undefined},{tag:'some',val:{tag:'none'}},{tag:'some',val:{tag:'some',val:undefined}},{tag:'some',val:{tag:'some',val:handle2}}]};
 for(const depth of[1,2,3,4]){
  const p=require(path.join(out,'depth-'+depth+'.cjs')).project;
  const types=fs.readFileSync(path.join(out,'types-'+depth,'interfaces/research-shapes-storage.d.ts'),'utf8');
  const expectedType={1:'nested?: File',2:'nested: Option<File | undefined>',3:'nested?: Option<File | undefined>',4:'nested: Option<Option<File | undefined> | undefined>'}[depth];
  assert(types.includes(expectedType));
  for(let i=0;i<values[depth].length;i++){
   const got=p({firstFile:handle,nested:values[depth][i],batches:[]},x=>{assert(x===handle||x===handle2);return x;});
   assert.deepEqual(got,[{...handle,permission:'read'},...(i===values[depth].length-1?[{...handle2,permission:'write'}]:[])]);
   depthChecks.push({depth,valueIndex:i,dependencies:got.length});
  }
 }
 const result={summary:{componentCalls:rows.length,mismatches:0,oldRecordFailures,oldOptionFailures,depthBindingChecks:depthChecks.length},
  rows,bindingErrors,depthChecks,scope:'depth-2 options traverse real Canonical ABI; depth-1/3/4 JS cases match Jco type declarations but are not full ABI execution'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
