'use strict';
// Separate process: input contains public x and anonymous observed state only.
const fs=require('node:fs');
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const basis=(a,b)=>[1,a>>>0,b>>>0,Math.imul(a,a)>>>0,Math.imul(a,b)>>>0,Math.imul(b,b)>>>0];
const evaluate=(c,f)=>c.reduce((s,v,i)=>s+v*f[i],0)>>>0;
function search(data,indices){
 const prepared=data.map(r=>({x:r.input>>>0,f:basis(...indices.map(i=>r.state[i]))}));
 const matches=[];
 for(let id=0;id<15625;id++){
  let n=id;const c=[];for(let k=0;k<6;k++){c.push(n%5-2);n=Math.floor(n/5);}
  if(prepared.every(r=>evaluate(c,r.f)===r.x))matches.push(c);
 }
 return matches;
}
const start=performance.now();
const fixed=search(rows,[0,1]),partitions=[];
// A declared grammar: try each observed binary-valued coordinate as a split.
for(let axis=0;axis<3;axis++){
 const values=[...new Set(rows.map(r=>r.state[axis]))].sort((a,b)=>a-b);
 if(values.length!==2||values[0]!==0||values[1]!==1)continue;
 const indices=[0,1,2].filter(i=>i!==axis);
 const groups=values.map(value=>({value,matches:search(rows.filter(r=>r.state[axis]===value),indices)}));
 partitions.push({axis,indices,groups,unique:groups.every(g=>g.matches.length===1)});
}
fs.writeFileSync(process.argv[3],JSON.stringify({trainingRows:rows.length,basis:['1','a','b','a*a','a*b','b*b'],coefficientRange:[-2,2],candidatesPerSearch:15625,fixed,partitions,elapsedMs:performance.now()-start},null,2));
