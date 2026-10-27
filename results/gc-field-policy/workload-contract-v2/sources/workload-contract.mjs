import fs from 'node:fs';
import {admit} from './loader.mjs';
const [checker,path]=process.argv.slice(2),spec=JSON.parse(fs.readFileSync(path,'utf8')),rows=[];
for(const c of spec.cases){
  const r=admit(checker,Buffer.from(c.library),c.policy,Buffer.from(c.consumer),c.allowed);
  if(r.status!=='accepted')throw Error(JSON.stringify(r));
  const lib=r.library.exports,f=r.client.exports.run;lib.init(c.n,c.secret);
  for(let k=0;k<12;k++)f(c.n,8,17,123456+k);
  const checks=Array.from({length:11},(_,k)=>f(c.n,8,17,123456+k));
  const privateValues=Array.from({length:c.n},(_,i)=>lib['private-at'](i));
  rows.push({mode:c.mode,n:c.n,secret:c.secret,checks,private:privateValues});
}
const b=spec.bad,r=admit(checker,Buffer.from(b.library),b.policy,Buffer.from(b.consumer),b.allowed);
console.log(JSON.stringify({rows,badImport:r.status}));
