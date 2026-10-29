'use strict';
// Reads only observed entry states and their public inputs. No generator import.
const fs=require('node:fs');
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const features=(a,b)=>[1,a>>>0,b>>>0,Math.imul(a,a)>>>0,Math.imul(a,b)>>>0,Math.imul(b,b)>>>0];
const evalPoly=(c,f)=>c.reduce((v,k,i)=>v+k*f[i],0)>>>0;
const data=rows.map(r=>({f:features(...r.state),x:r.input>>>0}));
const start=performance.now(),matches=[];
for(let id=0;id<15625;id++){
 let q=id;const c=[];for(let j=0;j<6;j++){c.push(q%5-2);q=Math.floor(q/5);}
 if(data.every(r=>evalPoly(c,r.f)===r.x))matches.push(c);
}
const result={basis:['1','a','b','a*a','a*b','b*b'],coefficientRange:[-2,2],candidates:15625,trainingRows:rows.length,matches,elapsedMs:performance.now()-start};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2));
