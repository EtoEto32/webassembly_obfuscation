'use strict';
const fs=require('fs'),path=require('path'),h=require('./common.cjs');
(async()=>{
 const file=path.resolve(process.argv[2]),base=path.dirname(file),m=JSON.parse(fs.readFileSync(file)),tests=h.inputs(),rows=[];
 for(const row of m.rows){
  const r={id:row.id,cases:tests.length,calls:0,mismatches:0,traps:0,status:'passed'};
  try{
   const a=await h.core(path.join(base,row.source)),b=await h.core(path.join(base,row.recovered)),c=await h.component(path.join(base,row.js)),d=await h.component(path.join(base,row.js));
   for(const [x,y] of tests){
    const expected=h.evaluate(row.expression,x,y);
    for(const [name,unit] of [['original',a],['recovered',b],['componentA',c],['componentB',d]]){
     try{const actual=unit.run(x>>>0,y>>>0)|0;r.calls++;if(actual!==expected){r.mismatches++;if(!r.witness)r.witness={name,x,y,expected,actual};}}
     catch(error){r.traps++;r.status='runtime_trap';if(!r.error)r.error=String(error);}
    }
   }
   if(r.mismatches)r.status='wrong_result';
  }catch(error){r.status='setup_error';r.error=String(error);}
  rows.push(r);
 }
 const negative=[];
 for(const row of m.negative){
  const a=await h.component(path.join(base,row.js));let witness=null;
  for(const [x,y] of tests){const actual=a.run(x>>>0,y>>>0)|0,expected=h.evaluate(row.expression,x,y);if(actual!==expected){witness={x,y,actual,expected};break;}}
  negative.push({id:row.id,witness});
 }
 const summary={rows:rows.length,calls:rows.reduce((s,r)=>s+r.calls,0),mismatches:rows.reduce((s,r)=>s+r.mismatches,0),traps:rows.reduce((s,r)=>s+r.traps,0),passed:rows.every(r=>r.status==='passed')&&negative.every(r=>r.witness),negative:negative.length};
 fs.writeFileSync(path.join(base,'check.json'),JSON.stringify({summary,rows,negative},null,2));console.log(summary);
})().catch(e=>{console.error(e);process.exitCode=1;});
