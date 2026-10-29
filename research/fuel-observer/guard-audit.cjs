'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {bind}=require('./guard.cjs');
const [root,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:false});fs.mkdirSync(path.join(out,'sources'));
for(const name of ['guard.cjs','guard-audit.cjs'])fs.copyFileSync(path.join(__dirname,name),path.join(out,'sources',name));
const read=p=>JSON.parse(fs.readFileSync(p));let checks=0,prefixComparisons=0,coverageChecks=0;const rows=[],counterexamples=[];
function hash(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
try{
  const manifest=read(path.join(root,'manifest.json'));const inputs={};
  for(const rec of manifest.records){
    const folder=path.join(root,rec.kind),contract=read(path.join(folder,'target.json')),all=read(path.join(folder,'oracle.json')),oracle=all.filter(v=>v.x===0);
    for(const name of ['target.wasm','target-O3.wasm','target.json','oracle.json'])inputs[path.resolve(folder,name)]=hash(path.join(folder,name));
    for(const file of ['target.wasm','target-O3.wasm']){
      const bytes=fs.readFileSync(path.join(folder,file));const fixed={...contract,targetSha256:hash(path.join(folder,file))};
      // Additional optimized bytes are bound explicitly; changing the contract
      // hash is allowed only here because this harness itself ran the optimizer.
      for(const [policyName,policy] of Object.entries({none:()=>0,topup:e=>e.payload===0?17:3,withdraw:e=>-Math.floor(e.remaining/2),deny:e=>-e.remaining-1})){
        for(const mode of ['whole','depth','observer']){
          const g=bind(bytes,fixed,{mode,policy});let success=0,events=0;
          for(let budget=0;budget<=contract.whole+1;budget++){
            const known=new Map();
            for(const item of oracle){
              const got=g.run(item.secret,item.x,budget);checks++;if(got.status==='ok'){success++;assert.strictEqual(got.value,item.value);}events+=got.events;
              let paid=0,pos=0,remaining=budget;const prefix=[];
              for(const row of got.ledger){
                if(row[0]==='reserve'){
                  const key=JSON.stringify(prefix);if(known.has(key)){assert.deepStrictEqual(row,known.get(key));prefixComparisons++;}else known.set(key,row);
                  if(row[2]<=remaining){remaining-=row[2];paid=row[1];}
                }else if(row[0]==='budget-input'){remaining+=row[1];prefix.push(row);}
                else if(row[0]==='event'){
                  assert.deepStrictEqual(row.slice(1),item.events[pos].label);assert(paid>=item.events[pos].cost);pos++;prefix.push(row);coverageChecks++;
                }else if(row[0]==='return'){assert(paid>=item.total);prefix.push(row);coverageChecks++;}
              }
              if(got.status==='ok')assert(got.credit>=item.total,'terminal refund below actual cost');
            }
          }
          rows.push({kind:rec.kind,file,policy:policyName,mode,success,events});
        }
      }
    }
    if(rec.kind==='early-split'){
      const a=oracle.find(x=>x.secret===0),b=oracle.find(x=>x.secret===1);
      assert.notStrictEqual(a.total,b.total);
      counterexamples.push({kind:'future-output-precharge',beforeReleaseHistory:[],secret0Charge:a.total,secret1Charge:b.total,reason:'Same empty public history, different entrance reservation based on not-yet-published output.'});
    }
    if(rec.kind==='hidden-tail'){
      const a=oracle.find(x=>x.secret===0),b=oracle.find(x=>x.secret===1);
      assert.deepStrictEqual(a.events.map(x=>x.label),b.events.map(x=>x.label));assert.notStrictEqual(a.events[0].cost,b.events[0].cost);
      counterexamples.push({kind:'actual-cost-refund',publishedHistory:a.events.map(x=>x.label),secret0Spent:a.events[0].cost,secret1Spent:b.events[0].cost,reason:'Refund based on hidden measured prefix cost differs under the same published event.'});
    }
  }
  const bad=read(path.join(root,'early-split','target.json'));assert.throws(()=>bind(fs.readFileSync(path.join(root,'hidden-tail','target.wasm')),bad),/mismatch/);
  fs.writeFileSync(path.join(out,'input-sha256.json'),JSON.stringify(inputs,null,2));
  const report={checks,prefixComparisons,coverageChecks,rows,counterexamples,note:'Two negative controls are arithmetic consequences of independently interpreted real Wasm fixture traces; no new runtime vulnerability is claimed.'};
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({checks,prefixComparisons,coverageChecks,counterexamples:counterexamples.length}));
}finally{
  const hashes={};function walk(p){for(const x of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,x.name);if(x.isDirectory())walk(f);else if(x.name!=='sha256.json')hashes[path.relative(out,f)]=hash(f);}}walk(out);fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(hashes,null,2));
}
