'use strict';
const fs=require('fs'),path=require('path'),h=require('./common.cjs');
(async()=>{
 const dir=path.resolve(process.argv[2]),unit=await h.component(path.join(dir,'js')),rows=[];
 for(const y of [0,1,0x40000000,0x80000000,0xffffffff]){const expected=y>>>0,actual=unit.run(0,y)>>>0;rows.push({x:0,y,expected,actual,equal:expected===actual});}
 const result={scope:'Jco 1.27.0 generated JS resource rep path; one add destructor',rows,mismatches:rows.filter(x=>!x.equal).length};fs.writeFileSync(path.join(dir,'probe.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exitCode=1;});
