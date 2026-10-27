'use strict';const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=process.argv[2],mutants=JSON.parse(fs.readFileSync(path.join(dir,'mutants.json'))),records=[];
for(const r of mutants){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.file)))).exports;
 const oracle=new Uint8Array(65536);let x=12345;for(let i=0;i<oracle.length;i++){x=(Math.imul(x,1664525)+1013904223)|0;oracle[i]=x>>>24;}
 e.fill(12345);const expectedTrap=r.d+r.n>65536||r.s+r.n>65536;
 if(!expectedTrap)oracle.copyWithin(r.d,r.s,r.s+r.n);
 let actualTrap=false;try{e.copy(r.d,r.s,r.n);}catch(x){assert(x instanceof WebAssembly.RuntimeError);actualTrap=true;}
 let firstMismatch=null;for(let i=0;i<65536;i++){const got=e.read(i);if(got!==oracle[i]){firstMismatch={offset:i,expected:oracle[i],actual:got};break;}}
 assert(expectedTrap!==actualTrap||firstMismatch,r.name+' was not detected');records.push({...r,expectedTrap,actualTrap,firstMismatch});
}
fs.writeFileSync(path.join(dir,'negative-controls.json'),JSON.stringify(records,null,2),{flag:'wx'});
