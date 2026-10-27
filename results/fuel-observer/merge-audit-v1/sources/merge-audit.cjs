'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');const {bind}=require('./guard.cjs');
const root=process.argv[2],read=p=>JSON.parse(fs.readFileSync(p)),manifest=read(path.join(root,'manifest.json'));let valueChecks=0,coverageChecks=0,budgetChecks=0;
for(const rec of manifest.rows){
  const folder=path.join(root,String(rec.id)),contract=read(path.join(folder,'merged.json')),cases=read(path.join(folder,'oracle.json')),bytes=fs.readFileSync(path.join(folder,'merged.wasm'));
  const guard=bind(bytes,contract),plain=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(folder,'original.wasm'))),{env:{mark:()=>{}}});
  const budgets=[...new Set([0,contract.whole,contract.whole+1,...contract.nodes.flatMap(n=>[Math.max(0,n.bound-1),n.bound,n.bound+1])])];
  for(const item of cases){
    assert.strictEqual(plain.exports.run(item.secret,item.x)>>>0,item.value);valueChecks++;
    for(const budget of budgets){
      const got=guard.run(item.secret,item.x,budget);let credit=0,remaining=budget,pos=0;budgetChecks++;
      for(const row of got.ledger){
        if(row[0]==='reserve'){if(row[2]<=remaining){remaining-=row[2];credit=row[1];}}
        else if(row[0]==='event'){assert.deepStrictEqual(row.slice(1),item.events[pos].label);assert(credit>=item.events[pos].cost);pos++;coverageChecks++;}
        else if(row[0]==='return'){assert(credit>=item.total);assert.strictEqual(row[1],item.value);coverageChecks++;}
      }
      if(got.status==='ok')assert(got.credit>=item.total);if(budget>=contract.whole)assert.strictEqual(got.status,'ok');
    }
  }
}
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify({valueChecks,coverageChecks,budgetChecks,fixtures:manifest.rows.length},null,2));console.log(JSON.stringify({valueChecks,coverageChecks,budgetChecks}));
