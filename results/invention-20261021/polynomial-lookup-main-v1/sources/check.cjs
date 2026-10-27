'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const task=JSON.parse(fs.readFileSync(process.argv[2]));
let calls=0;const rows=[];
for(const row of task){
 const bytes=fs.readFileSync(row.file);
 assert(WebAssembly.validate(bytes));
 const api=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 assert.deepEqual(Object.keys(api),['lookup']);
 for(const [x,expected] of row.tests){
  const actual=api.lookup(x)>>>0;assert.equal(actual,expected>>>0,row.file+' '+x);calls++;
 }
 rows.push({file:row.file,calls:row.tests.length,status:'success',traps:0});
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,calls,mismatches:0,rows}));
