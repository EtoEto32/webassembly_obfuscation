'use strict';
const assert=require('assert/strict'),dispose=Symbol.dispose||Symbol.for('dispose');
function manualProject(value,resolve){
 const d=(v,permission)=>({...resolve(v),permission});
 switch(value.tag){case'read':return[d(value.val,'read')];case'write':return[d(value.val,'write')];
 case'copy':return[d(value.val.source,'read'),d(value.val.destination,'write')];case'batch':return value.val.map(v=>d(v,'write'));
 case'optional':return[d(value.val.primary,'write'),...(value.val.backup===undefined?[]:[d(value.val.backup,'write')])];case'idle':return[];default:throw Error('variant');}
}
function createHost(project,granularity='operation'){
 assert(['operation','object','global'].includes(granularity));
 const slots=[],records=new WeakMap(),objects=Array.from({length:3},(_,id)=>({id,epoch:{read:0,write:0},objectEpoch:0,allowed:{read:true,write:true},pins:0}));
 const tickets=new Map(),log=[];let next=1,prepares=0,drops=0,resolves=0,globalEpoch=0,admitting=false;
 function idle(){if(admitting)throw Error('reentrant admission/revocation forbidden');}
 class File{
  constructor(id){idle();if(!objects[id])throw Error('unknown backend');let slot=slots.findIndex(s=>!s.alive);if(slot<0)slot=slots.length;
   const rec={slot,generation:(slots[slot]?.generation??0)+1,object:objects[id],alive:true};slots[slot]=rec;records.set(this,rec);rec.object.pins++;}
  [dispose](){idle();const r=records.get(this);if(!r||!r.alive)throw Error('duplicate drop');r.alive=false;r.generation++;r.object.pins--;drops++;}
 }
 function resolve(file){const r=records.get(file);if(!r||!r.alive)throw Error('unknown/closed host resource');resolves++;return{slot:r.slot,generation:r.generation};}
 function prepare(value){
  idle();if(next>0xffffffff)throw Error('ticket ID space exhausted');
  const deps=project(value,resolve),slotDeps=[],grants=new Map();
  for(const d of deps){const r=slots[d.slot];if(!r.alive||r.generation!==d.generation||!r.object.allowed[d.permission])throw Error('not authorized at entry');
   slotDeps.push(Object.freeze({slot:r.slot,generation:r.generation,objectId:r.object.id}));
   grants.set(r.object.id+':'+d.permission,Object.freeze({object:r.object,permission:d.permission,epoch:r.object.epoch[d.permission]}));}
  const retained=[...new Set([...grants.values()].map(g=>g.object))];for(const o of retained)o.pins++;
  const objectDeps=granularity==='object'?retained.map(object=>({object,epoch:object.objectEpoch})):[];
  const id=next++;tickets.set(id,Object.freeze({slots:Object.freeze(slotDeps),grants:Object.freeze([...grants.values()]),
    retained:Object.freeze(retained),objectDeps:Object.freeze(objectDeps),globalEpoch}));prepares++;return id;
 }
 function admit(id,executeSync){idle();const t=tickets.get(id);if(!t)return false;tickets.delete(id);
  // Admission and revocation run synchronously on this single JS thread.
  let ok=t.slots.every(d=>{const r=slots[d.slot];return r.alive&&r.generation===d.generation&&r.object.id===d.objectId;});
  if(ok){if(granularity==='global')ok=!t.grants.length||t.globalEpoch===globalEpoch;
    else if(granularity==='object')ok=t.objectDeps.every(d=>d.object.objectEpoch===d.epoch);
    else ok=t.grants.every(g=>g.object.allowed[g.permission]&&g.object.epoch[g.permission]===g.epoch);}
  try{
   if(ok){admitting=true;log.push(id);if(executeSync)executeSync();}
   return ok;
  }finally{admitting=false;for(const o of t.retained)o.pins--;}
 }
 return{imports:{File,open:id=>new File(id),prepare},slots,objects,admit,tickets,log,
  update(id,permission){idle();globalEpoch++;objects[id].objectEpoch++;objects[id].epoch[permission]++;objects[id].allowed[permission]=false;},
  invalidate(slot){idle();assert(slots[slot].alive);slots[slot].generation++;},
  reset(){assert.equal(tickets.size,0);assert(objects.every(o=>o.pins===0));for(const o of objects)o.allowed={read:true,write:true};log.length=0;},
  stats(){return{prepares,drops,resolves,liveTickets:tickets.size,logicalPins:objects.reduce((n,o)=>n+o.pins,0)};}};
}
module.exports={createHost,manualProject};
