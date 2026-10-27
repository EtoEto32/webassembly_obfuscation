'use strict';
const fs=require('fs'),assert=require('assert/strict'),{createHost}=require('./fence-runtime.cjs');
// The operator table is part of the TCB. There is no per-call permission input
// and no per-call arbitrary executor. One prepared immutable plan feeds both.
function createEngine(build,fds){
 const plans=new Map();let reads=0,writes=0;
 const h=createHost((ops,resolve)=>ops.map((op,i)=>{
  assert(op.op==='read'||op.op==='write');
  if(op.op==='write'){assert(Object.hasOwn(op,'literal')!==Object.hasOwn(op,'from'));
   if(Object.hasOwn(op,'literal'))assert.equal(typeof op.literal,'string');
   else assert(Number.isInteger(op.from)&&op.from>=0&&op.from<i&&ops[op.from].op==='read');}
  return{...resolve(op.file),permission:op.op};
 }));
 const prepare=h.imports.prepare;
 h.imports.prepare=value=>{
  const ops=build(value);assert(ops.length<=8192);let id;
  try{
   id=prepare(ops);const ticket=h.tickets.get(id);assert.equal(ticket.slots.length,ops.length);
   const fixed=ops.map((op,i)=>Object.freeze({op:op.op,objectId:ticket.slots[i].objectId,
    ...(Object.hasOwn(op,'literal')?{literal:op.literal}:{}),...(Object.hasOwn(op,'from')?{from:op.from}:{})}));
   plans.set(id,Object.freeze(fixed));return id;
  }catch(error){if(id!==undefined)h.cancel(id);throw error;}
 };
 function read(id){const size=fs.fstatSync(fds[id]).size;if(size>16384)throw Error('backend read bound');
  const data=Buffer.alloc(size);let n=0;while(n<size){const k=fs.readSync(fds[id],data,n,size-n,n);if(!k)throw Error('unexpected EOF');n+=k;}reads++;return data;}
 function write(id,data){let n=0;while(n<data.length){const k=fs.writeSync(fds[id],data,n,data.length-n,n);if(!k)throw Error('zero write');n+=k;}
  fs.ftruncateSync(fds[id],data.length);writes++;}
 return{
  imports:h.imports,
  admit(id,...extra){if(extra.length)throw Error('external executor forbidden');const plan=plans.get(id);if(!plan)return{admitted:false,readValues:[]};plans.delete(id);
   const readValues=[];const admitted=h.admit(id,()=>{const values=[];for(let i=0;i<plan.length;i++){
    const op=plan[i];if(op.op==='read'){values[i]=read(op.objectId);readValues.push(values[i].toString('utf8'));}
    else write(op.objectId,Object.hasOwn(op,'literal')?Buffer.from(op.literal):values[op.from]);
   }});return{admitted,readValues};
  },
  cancel(id){plans.delete(id);return h.cancel(id);},
  shutdown(){plans.clear();return h.shutdown();},
  revoke:(id,p)=>h.update(id,p),
  reset(){assert.equal(plans.size,0);h.reset();},
  describe(id){const p=plans.get(id);return p?JSON.parse(JSON.stringify(p)):null;},
  stats(){return{...h.stats(),plans:plans.size,reads,writes};}
 };
}
module.exports={createEngine};
