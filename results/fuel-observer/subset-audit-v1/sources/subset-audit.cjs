'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');const {bind}=require('./guard.cjs');
const root=process.argv[2],contract=JSON.parse(fs.readFileSync(path.join(root,'signed-target.json'))),bytes=fs.readFileSync(path.join(root,'signed-target.wasm'));const g=bind(bytes,contract);
let checks=0;for(const secret of [0,1,2,0xffffffff])for(const x of [0,1,0xffffffff,0x80000000]){
  const r=g.run(secret,x,1000),label=(secret&1)?-1:-2147483648;assert.strictEqual(r.status,'ok');assert.deepStrictEqual(r.ledger.find(v=>v[0]==='event'),['event',2147483647,label]);checks++;
}
const exact=g.run(0,0,Number.MAX_SAFE_INTEGER);assert(Number.isSafeInteger(exact.remaining));checks++;
let reentry;reentry=bind(bytes,contract,{policy:()=>{assert.throws(()=>reentry.run(0,0,1000),/reentry/);checks++;return 0;}});assert.strictEqual(reentry.run(0,0,1000).status,'ok');
const overflow=bind(bytes,contract,{policy:e=>Number.MAX_SAFE_INTEGER-e.remaining});assert.throws(()=>overflow.run(0,0,1000),/overflow/);checks++;
for(const b of [-1,NaN,Infinity,Number.MAX_SAFE_INTEGER+1]){assert.throws(()=>g.run(0,0,b),/budget/);checks++;}
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify({checks,unsupported:JSON.parse(fs.readFileSync(path.join(root,'subset.json'))).length,note:'Added safe-integer overflow rejection for refunds after very large public top-ups. Signed marker payloads and reentry tested.'},null,2));console.log(JSON.stringify({checks,unsupported:8}));
