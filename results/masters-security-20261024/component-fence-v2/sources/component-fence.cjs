'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const out=path.resolve(process.argv[2]),{project}=require(path.join(out,'project.cjs'));
const dispose=Symbol.dispose||Symbol.for('dispose');
// This host adapter resolves captured host objects during the borrow call only.
// A ticket contains host-owned records and copied integers; no borrowed wrapper.
function host(){
 const slots=[],records=new WeakMap(),objects=Array.from({length:3},(_,id)=>({id,epoch:{read:0,write:0},allowed:{read:true,write:true},pins:0}));
 const tickets=new Map(),log=[];let next=1,prepares=0,drops=0,resolves=0;
 class File{
  constructor(id){if(!objects[id])throw Error('unknown backend');let slot=slots.findIndex(s=>!s.alive);if(slot<0)slot=slots.length;
   const rec={slot,generation:(slots[slot]?.generation??0)+1,object:objects[id],alive:true};slots[slot]=rec;records.set(this,rec);rec.object.pins++;}
  [dispose](){const r=records.get(this);if(!r||!r.alive)throw Error('duplicate drop');r.alive=false;r.generation++;r.object.pins--;drops++;}
 }
 function resolve(file){const r=records.get(file);if(!r||!r.alive)throw Error('unknown/closed host resource');resolves++;return{slot:r.slot,generation:r.generation};}
 function prepare(value){
  const deps=project(value,resolve),slotDeps=[],grants=new Map();
  for(const d of deps){const r=slots[d.slot];if(!r.alive||r.generation!==d.generation||!r.object.allowed[d.permission])throw Error('not authorized at entry');
   slotDeps.push(Object.freeze({slot:r.slot,generation:r.generation,objectId:r.object.id}));
   const key=r.object.id+':'+d.permission;grants.set(key,Object.freeze({object:r.object,permission:d.permission,epoch:r.object.epoch[d.permission]}));}
  const retained=[...new Set([...grants.values()].map(g=>g.object))];for(const o of retained)o.pins++;
  const id=next++;tickets.set(id,Object.freeze({slots:Object.freeze(slotDeps),grants:Object.freeze([...grants.values()]),retained:Object.freeze(retained)}));prepares++;return id;
 }
 function admit(id){const t=tickets.get(id);if(!t)return false;tickets.delete(id);
  // No await/callback/external code between the checks and synchronous admission.
  const ok=t.slots.every(d=>{const r=slots[d.slot];return r.alive&&r.generation===d.generation&&r.object.id===d.objectId;})&&
   t.grants.every(g=>g.object.allowed[g.permission]&&g.object.epoch[g.permission]===g.epoch);
  if(ok)log.push(id);for(const o of t.retained)o.pins--;return ok;
 }
 return {imports:{File,open:id=>new File(id),prepare},slots,objects,admit,tickets,log,
  update(id,permission){objects[id].epoch[permission]++;objects[id].allowed[permission]=false;},
  invalidate(slot){assert(slots[slot].alive);slots[slot].generation++;},
  reset(){assert.equal(tickets.size,0);assert(objects.every(o=>o.pins===0));for(const o of objects)o.allowed={read:true,write:true};},
  stats(){return{prepares,drops,resolves,liveTickets:tickets.size,logicalPins:objects.reduce((n,o)=>n+o.pins,0)};}};
}
function expected(mode,count,a,b){switch(mode){case 0:return[[0,a,'read']];case 1:return[[0,a,'write']];case 2:return[[0,a,'read'],[1,b,'write']];
 case 3:return Array.from({length:count},(_,i)=>[i%2,i%2?b:a,'write']);case 4:return[[0,a,'write'],...(count?[[1,b,'write']]:[])];case 5:return[];default:throw Error('oracle mode');}}
async function instantiate(dir,h){const m=await import(pathToFileURL(path.join(dir,'unit.js')).href);return m.instantiate(name=>WebAssembly.compile(fs.readFileSync(path.join(dir,name))),{'research:fence/storage':h.imports});}
const cases=[[0,0],[1,0],[2,0],[3,0],[3,1],[3,2],[3,8],[3,64],[4,0],[4,1],[5,0]];
const events=[{kind:'none'},...Array.from({length:3},(_,id)=>['read','write'].map(permission=>({kind:'permission',id,permission}))).flat(),{kind:'release'},{kind:'reuse'},{kind:'invalidate',slot:0},{kind:'invalidate',slot:1}];
(async()=>{
 const rows=[];
 for(const variant of ['raw','optimized']){
  const dir=path.join(out,variant),h=host(),c=await instantiate(dir,h);let decisions=0,mismatches=0,entryUnsafe=0,globalFalseRejects=0,duplicateRejected=0;const examples=[];
  for(let a=0;a<3;a++)for(let b=0;b<3;b++)for(const[mode,count]of cases)for(const event of events){
   h.reset();c.setup(a,b);const id=c.request(mode,count),deps=expected(mode,count,a,b),t=h.tickets.get(id);
   assert(t);assert.deepEqual(t.slots.map(s=>[s.slot,s.objectId]),deps.map(d=>d.slice(0,2)));
   assert(t.slots.every(s=>s.generation===h.slots[s.slot].generation));
   const wantKeys=[...new Set(deps.map(d=>d[1]+':'+d[2]))].sort();assert.deepEqual(t.grants.map(g=>g.object.id+':'+g.permission).sort(),wantKeys);
   let released=false;
   if(event.kind==='permission')h.update(event.id,event.permission);
   if(event.kind==='invalidate')h.invalidate(event.slot);
   if(event.kind==='release'||event.kind==='reuse'){c.release();released=true;if(event.kind==='reuse'){c.setup((a+1)%3,(b+1)%3);released=false;}}
   // This continuation is deliberately after the component borrow call returned.
   await Promise.resolve();
   const invalid=deps.some(d=>event.kind==='permission'?d[1]===event.id&&d[2]===event.permission:event.kind==='invalidate'?d[0]===event.slot:event.kind==='release'||event.kind==='reuse');
   const got=h.admit(id),want=!invalid;decisions++;if(got!==want){mismatches++;examples.push({a,b,mode,count,event,got,want});}
   if(invalid)entryUnsafe++;if(event.kind!=='none'&&deps.length&&!invalid)globalFalseRejects++;
   assert.equal(h.admit(id),false);duplicateRejected++;if(!released)c.release();h.reset();
  }
  // Independent instance per deliberate trap: do not assume post-trap recovery.
  const rejected=[];
  for(const [name,mode,count]of [['bad-tag',6,0],['oversize-guest-list',3,65]]){
   const nh=host(),nc=await instantiate(dir,nh);nc.setup(0,1);let error=null;try{nc.request(mode,count);}catch(e){error=String(e);}assert(error);assert.equal(nh.stats().prepares,0);rejected.push({name,error,logicalPinsAtTrap:nh.stats().logicalPins});
  }
  rows.push({variant,decisions,mismatches,entryUnsafe,globalFalseRejects,duplicateRejected,...h.stats(),rejected,examples});assert.equal(mismatches,0);
 }
 const result={rows,summary:{componentPrepares:rows.reduce((s,r)=>s+r.prepares,0),decisions:rows.reduce((s,r)=>s+r.decisions,0),mismatches:rows.reduce((s,r)=>s+r.mismatches,0)},
 scope:'real component imports via Jco; synchronous host effect log after JS await; no OS I/O or multi-threaded admission; logical pins are not process memory'};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
})().catch(e=>{console.error(e);process.exitCode=1;});
