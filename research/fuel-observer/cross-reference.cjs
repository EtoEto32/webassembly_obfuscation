'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');const {bind}=require('./guard.cjs');
const [root,out]=process.argv.slice(2),read=p=>JSON.parse(fs.readFileSync(p));const cases=[];
for(const rec of read(path.join(root,'manifest.json')).records){
  const folder=path.join(root,rec.kind),contract=read(path.join(folder,'target.json'));
  const budgets=[...new Set([0,contract.whole,contract.whole+1,...contract.nodes.flatMap(n=>[Math.max(0,n.bound-1),n.bound,n.bound+1])])].sort((a,b)=>a-b);
  for(const file of ['target.wasm','target-O3.wasm']){
    const bytes=fs.readFileSync(path.join(folder,file));const fixed={...contract,targetSha256:crypto.createHash('sha256').update(bytes).digest('hex')};
    for(const mode of ['whole','depth','observer']){
      const runner=bind(bytes,fixed,{mode});
      for(let secret=0;secret<16;secret++)for(const x of [0,0xffffffff])for(const budget of budgets){
        const got=runner.run(secret,x,budget);got.value??=null;cases.push({kind:rec.kind,file,mode,secret,x,budget,expected:got});
      }
    }
  }
}
fs.writeFileSync(out,JSON.stringify(cases));console.log(JSON.stringify({cases:cases.length}));
