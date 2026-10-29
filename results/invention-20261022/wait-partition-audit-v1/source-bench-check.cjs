'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),c=require('./common.cjs');
const dir=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;
for(const row of rows){const o=c.instantiate(path.join(dir,row.file));
 for(const n of [0,1,2,3,7,1024,32768])for(const field of [0,4]){
  o.physical.fill(0);let expect=0;for(let i=0;i<n;i++)expect^=i;
  assert.equal(o.api.bench(n,field),expect);assert.equal(o.api.load(field),n);assert.equal(o.api.load(field^4),0);calls+=3;
 }
}
console.log(JSON.stringify({conditions:rows.length,checked_calls:calls,passed:true}));
