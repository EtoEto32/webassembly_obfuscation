'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),c=require('./common.cjs');
const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),defs=JSON.parse(fs.readFileSync(path.join(out,'definitions.json'))),results=[];
for(const row of rows)for(const adapter of row.mode==='validator'?['validator','recognizer']:['native']){
 const o=c.instantiate(path.join(out,row.file),adapter),d=defs[row.name],r=c.rng(817223),inputs=[];
 for(const a of [0,1,0x7fffffff,0x80000000,0xffffffff])for(const b of [0,1,0x7fffffff,0x80000000,0xffffffff])inputs.push([a,b]);
 for(let i=0;i<32;i++){inputs.push([2**i,0],[0,2**i],[(~(2**i))>>>0,0xffffffff],[0xffffffff,(~(2**i))>>>0]);}
 inputs.push(d.witness);
 for(const clause of d.clauses){const v=d.witness.slice();for(const[word,bit,neg]of clause)v[word]=(v[word]&~(1<<bit))|(neg<<bit);inputs.push(v);}
 for(let i=0;i<2048;i++)inputs.push([r(),r()]);let positive=0,negative=0;
 for(const [a,b]of inputs){const want=c.evaluate(d.clauses,a,b),got=o.api.run(a,b);assert.equal(got,want,JSON.stringify({row,adapter,a,b,want,got}));want?positive++:negative++;}
 results.push({file:row.file,adapter,calls:inputs.length,positive,negative,host_calls:o.hostCalls(),passed:true});
}
const queries=JSON.parse(fs.readFileSync(path.join(out,'queries.json'))).map(row=>{const bytes=fs.readFileSync(path.join(out,row.file)),actual=WebAssembly.validate(bytes);assert.equal(actual,row.expected,row.file);return{...row,actual};});
c.save(out,'checks.json',{node:process.version,v8:process.versions.v8,results,queries});console.log(JSON.stringify({kind:'correctness',conditions:results.length,calls:results.reduce((s,x)=>s+x.calls,0),query_cases:queries.length,passed:true}));
