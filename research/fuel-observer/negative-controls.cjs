'use strict';
// Deliberately incorrect ACCOUNTING on harmless local integer fixtures.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const [source,out]=process.argv.slice(2);fs.mkdirSync(path.join(out,'sources'),{recursive:true});
fs.copyFileSync(__filename,path.join(out,'sources','negative-controls.cjs'));
for(const name of ['transform.py','acyclic.py'])fs.copyFileSync(path.join(__dirname,'..','fuel-frontier',name),path.join(out,'sources','frontier-'+name));
const read=p=>JSON.parse(fs.readFileSync(p)),hidden=read(path.join(source,'hidden-tail','oracle.json'));
let spent=0,events=[];const measured=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,'dynamic.wasm'))),{fuel:{charge:n=>{spent+=Number(n);}},env:{mark:(id,value)=>events.push({event:[id,value],refund:57-spent,measuredPrefix:spent})}});
const observed=[];
for(let secret=0;secret<4;secret++){
  spent=0;events=[];const value=measured.exports.run(secret,0)>>>0,expected=hidden.find(p=>p.secret===secret&&p.x===0);
  assert.strictEqual(value,expected.value);assert.strictEqual(spent,expected.total);assert.strictEqual(events[0].measuredPrefix,expected.events[0].cost);observed.push({secret,value,events,measuredTotal:spent});
}
assert.deepStrictEqual(observed[0].events[0].event,observed[1].events[0].event);assert.notStrictEqual(observed[0].events[0].refund,observed[1].events[0].refund);
const plain=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(source,'early-split','original.wasm'))),{env:{mark:(id,value)=>events.push([id,value])}}),early=[];
for(const secret of [0,1]){
  events=[];const precharge=(secret&1)?90:26,budget=26;let value=null,status='budget';
  if(precharge<=budget){value=plain.exports.run(secret,0)>>>0;status='ok';}
  early.push({secret,budget,precharge,events,status,value});
}
assert.notStrictEqual(early[0].status,early[1].status);
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({observed,early,note:'Refund difference measured by per-opcode instrumentation in actual Wasm. Early precharge is an intentionally incorrect host rule using a secret bit before the event is published.'},null,2));
const hashes={};function walk(p){for(const d of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,d.name);if(d.isDirectory())walk(f);else if(d.name!=='sha256.json')hashes[path.relative(out,f)]=crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');}}walk(out);fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(hashes,null,2));console.log(JSON.stringify({refunds:observed.map(x=>x.events[0].refund),earlyStatus:early.map(x=>x.status)}));
