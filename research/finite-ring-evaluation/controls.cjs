'use strict';const fs=require('fs'),path=require('path'),assert=require('assert');
const [src,out]=process.argv.slice(2),load=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports;
const triples=JSON.parse(fs.readFileSync(path.join(src,'checks.json'))).localResults;
const records=[];
for(const name of ['odd-mixer','one-iteration']){
 const e=load(path.join(out,name+'.wasm'));let example;
 for(const row of triples){const actual=e.run(...row.input)>>>0;if(actual!==row.expected){example={...row,actual};break;}}
 assert(example,'counterexample required '+name);records.push({name,counterexample:example});
}
for(const [name,file,wantChanged] of [['original',path.join(src,'hash-original-raw.wasm'),false],['write-before-trap',path.join(out,'write-before-trap.wasm'),true]]){
 const e=load(file),m=new Uint8Array(e.memory.buffer);m.fill(0x5a);
 const before=Buffer.from(new Uint8Array(e.memory.buffer)),counter=e.evaluations.value;
 assert.throws(()=>e.hash(-1),WebAssembly.RuntimeError);
 const changed=Buffer.compare(Buffer.from(e.memory.buffer),before)!==0;
 assert.strictEqual(changed,wantChanged);assert.strictEqual(e.evaluations.value,counter);
 records.push({name,expected_trap:true,memory_changed:changed,before_first4:[...before.subarray(0,4)],after_first4:[...m.subarray(0,4)]});
}
fs.writeFileSync(path.join(out,'controls.json'),JSON.stringify(records,null,2),{flag:'wx'});
console.log(JSON.stringify(records));
