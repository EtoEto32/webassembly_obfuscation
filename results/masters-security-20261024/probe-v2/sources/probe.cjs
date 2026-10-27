'use strict';
// Controlled host-boundary experiments, not an implementation of WASI 0.3.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');
const os = require('os');
const out = path.resolve(process.argv[2]);
const manifest = JSON.parse(fs.readFileSync(path.join(out, 'manifest.json')));
let rngState = 20261024;
function rnd() { rngState ^= rngState << 13; rngState ^= rngState >>> 17; rngState ^= rngState << 5; return rngState >>> 0; }
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const ns = () => process.hrtime.bigint();
function stats(v) { const a = [...v].sort((x,y)=>x-y); return {median:a[Math.floor(a.length/2)],min:a[0],max:a.at(-1),p95:a[Math.min(a.length-1,Math.ceil(.95*a.length)-1)],samples:v}; }
function moduleBytes(entry) { const b=fs.readFileSync(path.join(out,entry.file)); assert.equal(hash(b),entry.sha256); assert(WebAssembly.validate(b)); return b; }

async function authority(entry) {
  let state, policy, tickets, next;
  const prepare = (tag,h0,h1) => {
    if (![0,1,2].includes(tag)) return -1;
    const hs = tag===0 ? [h0] : tag===1 ? [h1] : [h0,h1];
    if (hs.some(h=>!state.slots[h])) return -1;
    const deps=hs.map(h=>({h,slot:state.slots[h].generation,object:state.slots[h].object}));
    if (deps.some(d=>!state.objects[d.object].write)) return -1;
    for (const d of deps) { d.write=state.objects[d.object].wv; d.all=state.objects[d.object].all; }
    const id=next++;
    tickets.set(id,{deps,global:state.global,used:false});
    return id;
  };
  const inst=(await WebAssembly.instantiate(moduleBytes(entry),{host:{prepare}})).instance;
  const rows=[];
  const changes=['none','revoke-selected','revoke-other','revoke-read','regrant-selected','reuse-selected','reuse-other','alias-revoke'];
  function reset() {
    state={global:0,objects:[{write:true,read:true,wv:0,all:0},{write:true,read:true,wv:0,all:0}],slots:[{object:0,generation:0},{object:1,generation:0},{object:0,generation:0}]};
    tickets=new Map(); next=0;
  }
  function commit(id) {
    const t=tickets.get(id);
    if (!t || t.used) return false;
    t.used=true;
    if (policy==='entry') return true;
    if (policy==='global' && t.global!==state.global) return false;
    return t.deps.every(d=>{
      const s=state.slots[d.h],o=state.objects[d.object];
      return s && s.generation===d.slot && s.object===d.object && o.write &&
        (policy==='resource' ? o.all===d.all : o.wv===d.write);
    });
  }
  for (policy of ['entry','global','resource','operation']) {
    let checked=0,unsafe=0,falseReject=0,replayAccepted=0;
    for(let tag=0;tag<3;tag++) for(let h0=0;h0<3;h0++) for(let h1=0;h1<3;h1++) for(const change of changes) {
      reset();
      const handles=tag===0?[h0]:tag===1?[h1]:[h0,h1];
      const objects=new Set(handles.map(h=>state.slots[h].object));
      const selected=state.slots[handles[0]].object,other=1-selected;
      const ticket=inst.exports.request(tag,h0,h1);
      assert(ticket>=0);
      // Independent event oracle: did this event touch a selected write grant
      // or the particular table incarnation captured by this invocation?
      let expected=true;
      const revoke = id => {const o=state.objects[id];o.write=false;o.wv++;o.all++;state.global++;};
      if(change==='revoke-selected') {revoke(selected);expected=false;}
      if(change==='revoke-other') {revoke(other);expected=!objects.has(other);}
      if(change==='alias-revoke') {revoke(0);expected=!objects.has(0);}
      if(change==='revoke-read') {state.objects[selected].read=false;state.objects[selected].all++;state.global++;}
      if(change==='regrant-selected') {revoke(selected);state.objects[selected].write=true;state.objects[selected].wv++;state.objects[selected].all++;expected=false;}
      if(change==='reuse-selected') {state.slots[handles[0]]={object:other,generation:1};state.global++;expected=false;}
      if(change==='reuse-other') {const h=[0,1,2].find(x=>!handles.includes(x));if(h!==undefined){state.slots[h]={object:other,generation:1};state.global++;}}
      const accepted=commit(ticket);checked++;
      if(accepted&&!expected) unsafe++;
      if(!accepted&&expected) falseReject++;
      if(commit(ticket)) replayAccepted++;
      if(policy==='operation') assert.equal(accepted,expected,JSON.stringify({tag,h0,h1,change}));
    }
    reset(); assert.equal(inst.exports.request(9,0,1),-1); assert.equal(inst.exports.request(0,99,1),-1); assert.equal(commit(123456),false);
    rows.push({policy,cases:checked,unsafe,falseReject,replayAccepted,invalidRequestsRejected:2,forgedTicketRejected:1});
  }
  return {file:entry.file,rows};
}

function evaluate(e,args) {
  if(e[0]==='const')return e[1];
  if(e[0]==='arg')return args[e[1]]>>>0;
  const a=evaluate(e[1],args),b=evaluate(e[2],args);
  if(e[0]==='add')return (a+b)>>>0;
  if(e[0]==='sub')return (a-b)>>>0;
  if(e[0]==='and')return (a&b)>>>0;
  throw Error('unknown certificate expression');
}
function union(ranges) {
  const a=ranges.filter(([l,r])=>l<r).sort((x,y)=>x[0]-y[0]),res=[];
  for(const [l,r] of a) { const prev=res.at(-1);if(prev&&l<=prev[1])prev[1]=Math.max(r,prev[1]);else res.push([l,r]); }
  return res;
}
function selected(summary,args,length) {
  if(summary.kind==='reject')throw Error(summary.reason);
  if(summary.kind==='full')return [[0,length]];
  return union(summary.writes.map(w=>{
    const l=evaluate(w.addr,args)+w.offset,r=l+evaluate(w.length,args);
    return [Math.max(0,l),Math.min(length,r)];
  }));
}
function snapshot(memory,ranges) {const v=new Uint8Array(memory.buffer);return ranges.map(([l,r])=>[l,v.slice(l,r)]);}
function materialize(memory,pieces,length) {const r=new Uint8Array(memory.buffer).slice(0,length);for(const [l,b] of pieces)r.set(b,l);return r;}
function checksum(a) {let s=2166136261;for(const x of a)s=Math.imul(s^x,16777619);return s>>>0;}

async function snapshots(entry) {
  // Matched raw/O3 inputs, independent of preceding module enumeration.
  rngState=(20261024^parseInt(hash(Buffer.from(entry.name)).slice(0,8),16))>>>0;
  const inst=(await WebAssembly.instantiate(moduleBytes(entry))).instance;
  const {memory,callback}=inst.exports;
  const view=new Uint8Array(memory.buffer);
  const length=4096, init=new Uint8Array(view.length);
  for(let i=0;i<init.length;i++)init[i]=(i*17+3)&255;
  new DataView(init.buffer).setUint32(16,8,true);
  let cases=0,traps=0,mismatch=0,unprotectedMismatch=0,savedBytes=0,fullBytes=0;
  const inputs=[[0,99,0],[4,99,1],[4093,99,16],[7000,99,16],[131070,99,4],[-1,99,4],[-7,99,64],[0x7fffffff,99,16]];
  for(let i=0;i<200;i++)inputs.push([rnd()%8200,rnd()|0,rnd()%65]);
  for(const args of inputs) {
    view.set(init);
    const before=view.slice(0,length),ranges=selected(entry.summary,args,length),pieces=snapshot(memory,ranges);
    try{callback(...args);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;traps++;}
    const actual=materialize(memory,pieces,length);
    if(!Buffer.from(actual).equals(Buffer.from(before)))mismatch++;
    if(!Buffer.from(view.subarray(0,length)).equals(Buffer.from(before)))unprotectedMismatch++;
    savedBytes+=pieces.reduce((s,[l,b])=>s+b.length,0);fullBytes+=length;cases++;
  }
  assert.equal(mismatch,0,entry.file);
  // Same callback workload, with warmup. Timings include producing a host
  // snapshot result and checksum; allocation reduction need not mean speedup.
  const timing=[];let sink=0;
  const iterations=300,warmup=30,repetitions=9;
  for(const strategy of ['full-copy','generated','precomputed-same-ranges','no-copy']) {
    const samples=[];const args=[4,123,16],fixed=selected(entry.summary,args,length);
    const one=()=>{
      view.set(init.subarray(0,length));
      if(strategy==='full-copy'){
        const keep=view.slice(0,length);try{callback(...args);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;}return checksum(keep);
      }
      const ranges=strategy==='no-copy'?[]:strategy==='generated'?selected(entry.summary,args,length):fixed;
      const keep=snapshot(memory,ranges);try{callback(...args);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;}
      return checksum(materialize(memory,keep,length));
    };
    for(let i=0;i<warmup;i++)sink^=one();
    for(let r=0;r<repetitions;r++){const t=ns();for(let i=0;i<iterations;i++)sink^=one();samples.push(Number(ns()-t)/1e6/iterations);}
    timing.push({strategy,ms_per_call:stats(samples)});
  }
  return {file:entry.file,summary:entry.summary,cases,traps,mismatch,unprotectedMismatch,savedBytes,fullBytes,retainedFraction:savedBytes/fullBytes,timing,iterations,warmup,repetitions,sink,memoryBytes:memory.buffer.byteLength};
}

async function budgets(entry) {
  let jobs,policy,held,booked,nextId,peak,accepted,invalidRelease;
  const capacity=8,weight=2;
  function event(op,id) {
    if(policy==='semaphore') {
      // Reference implementation recomputes occupancy from the set of live
      // backend allocations; it does not use the proposal's charged flag.
      const occupancy=()=>weight*[...jobs.values()].filter(j=>!j.released).length;
      if(op===0){
        if(occupancy()+weight>capacity)return -1;
        const k=nextId++;jobs.set(k,{cancel:false,resolved:false,released:false});accepted++;
        held=booked=occupancy();peak=Math.max(peak,held);return k;
      }
      const j=jobs.get(id);if(!j)return -1;
      if(op===1)j.cancel=true;
      else if(op===2)j.resolved=true;
      else if(op===3){if(j.released){invalidRelease++;return 0;}j.released=true;}
      else return -1;
      held=booked=occupancy();return 0;
    }
    if(op===0){
      if(booked+weight>capacity)return -1;
      const k=nextId++;jobs.set(k,{cancel:false,resolved:false,released:false,charged:true});
      booked+=weight;held+=weight;peak=Math.max(peak,held);accepted++;return k;
    }
    const j=jobs.get(id);if(!j)return -1;
    if(op===1)j.cancel=true;
    else if(op===2)j.resolved=true;
    else if(op===3){if(j.released){invalidRelease++;return 0;}j.released=true;held-=weight;}
    else return -1;
    const refund=policy==='cancel' ? j.cancel||j.resolved||j.released : policy==='resolve' ? j.resolved||j.released : j.released;
    if(refund&&j.charged){j.charged=false;booked-=weight;}
    assert(booked>=0 && held>=0);
    if(['release','semaphore'].includes(policy))assert.equal(booked,held);
    return 0;
  }
  const inst=(await WebAssembly.instantiate(moduleBytes(entry),{host:{event}})).instance;
  const rows=[];
  for(policy of ['cancel','resolve','release','semaphore']) {
    for(const trace of ['cancel-storm','resolve-before-release','release-before-resolve','mixed-seeded']) {
      jobs=new Map();held=0;booked=0;nextId=0;peak=0;accepted=0;invalidRelease=0;
      const events=[];
      function emit(op,id=0){const result=inst.exports.event(op,id);events.push({op,id,result,held,booked});return result;}
      if(trace==='cancel-storm'||trace==='resolve-before-release') {
        for(let i=0;i<32;i++){const id=emit(0);if(id>=0){emit(1,id);if(trace==='resolve-before-release')emit(2,id);}}
      } else if(trace==='release-before-resolve') {
        for(let i=0;i<32;i++){const id=emit(0);if(id>=0){emit(3,id);emit(3,id);emit(2,id);}}
      } else {
        // Same deterministic operations for every policy. IDs refer to admitted
        // jobs; invalid IDs are explicitly rejected rather than acting as release.
        let localSeed=20261024;
        const rand=()=>{localSeed=(Math.imul(localSeed,1664525)+1013904223)>>>0;return localSeed;};
        for(let i=0;i<1000;i++){const x=rand()>>>8;if(x%4===0)emit(0);else emit(1+x%3,((rand()>>>8)%40));}
        assert(accepted>0,'random trace must actually allocate resources');
      }
      const beforeDrain={held,booked};
      for(const id of jobs.keys()){emit(3,id);emit(3,id);emit(2,id);}
      assert.equal(held,0);assert.equal(booked,0);
      if(['release','semaphore'].includes(policy))assert(peak<=capacity);
      rows.push({policy,trace,capacity,weight,accepted,peak,amplification:peak/capacity,beforeDrain,duplicateReleasesIgnored:invalidRelease,eventCount:events.length,events});
    }
  }
  // Strong baseline equivalence, deliberately explicit.
  for(const a of rows.filter(r=>r.policy==='release')){
    const b=rows.find(r=>r.policy==='semaphore'&&r.trace===a.trace);assert.deepEqual(a.events,b.events);
  }
  return {file:entry.file,rows};
}

(async()=>{
  const result={scope:'Core Wasm plus controlled Node host; not native Component Model/WASI',environment:{node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0].model},authority:[],snapshots:[],budgets:[]};
  const start=ns();
  for(const e of manifest){
    if(e.name==='authority')result.authority.push(await authority(e));
    else if(e.name==='budget')result.budgets.push(await budgets(e));
    else result.snapshots.push(await snapshots(e));
  }
  result.elapsedMs=Number(ns()-start)/1e6;result.processMemory=process.memoryUsage();
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({wasmModules:manifest.length,authorityRows:result.authority.reduce((s,x)=>s+x.rows.length,0),snapshotCases:result.snapshots.reduce((s,x)=>s+x.cases,0),snapshotMismatches:result.snapshots.reduce((s,x)=>s+x.mismatch,0),budgetRows:result.budgets.reduce((s,x)=>s+x.rows.length,0),elapsedMs:result.elapsedMs}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
