'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const {call,snapshot,difference}=require('./observer.cjs');
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const make=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,f))));
const rows=[],counts={accepted:0,unsupported:0,toolRejected:0,commands:0,skippedCommands:0,probes:0,instantiationRejected:0};
for(const r of m.rows){
  if(r.status!=='accepted'){counts[r.status==='unsupported'?'unsupported':'toolRejected']++;continue;}
  let a,b;
  try{a=make(r.source);b=make(r.observed);}catch(e){counts.instantiationRejected++;rows.push({source:r.source,status:'instantiation-rejected',error:String(e)});continue;}
  counts.accepted++;let tested=0;
  for(const c of r.commands){
    const action=c.action;
    if(!action||action.type!=='invoke'||action.module||(action.args||[]).some(x=>!['i32','i64'].includes(x.type))||
      (c.expected||[]).some(x=>!['i32','i64'].includes(x.type))){counts.skippedCommands++;continue;}
    const args=action.args.map(x=>x.type==='i64'?BigInt.asIntN(64,BigInt(x.value)):Number(BigInt.asIntN(32,BigInt(x.value))));
    const expected=call(a.exports[action.field],args),actual=call(b.exports[action.field],args);
    assert.deepStrictEqual(expected,actual,[r.source,c.line]);
    if(c.type==='assert_trap')assert(expected.trap);
    if(c.type==='assert_return'){
      assert(!expected.trap);
      if(c.expected.length===1){const x=c.expected[0];const want=x.type==='i64'?BigInt.asIntN(64,BigInt(x.value)).toString():Number(BigInt.asIntN(32,BigInt(x.value)));assert.strictEqual(expected.value,want);}
      else assert.strictEqual(c.expected.length,0);
    }
    const first=snapshot(b,r.manifest),second=snapshot(b,r.manifest);
    assert.deepStrictEqual(difference(first,second),[]);
    counts.probes+=2*(r.manifest.segments.filter(x=>x.probe).length+(r.manifest.memory?1:0)+(r.manifest.table?1:0));
    counts.commands++;tested++;
  }
  rows.push({source:r.source,status:'passed',commands:tested});
}
const result={node:process.version,counts,rows,note:'Official sources are independent tests; this is instrumentation validation, not a new runtime bug discovery.'};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(counts));
