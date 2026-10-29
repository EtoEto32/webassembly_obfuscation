'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto'),{bind}=require('./guard.cjs');
const root=process.argv[2],read=p=>JSON.parse(fs.readFileSync(p)),manifest=read(path.join(root,'manifest.json'));let values=0,budgets=0,prefixChecks=0;const rows=[];
for(const record of manifest.records){
  const dir=path.join(root,record.kind),contract=read(path.join(dir,'target.json')),oracle=read(path.join(dir,'oracle.json')),dataset=oracle.filter(x=>x.datasetIndex!==undefined);const modes={};
  for(const file of ['original.wasm','original-O3.wasm']){
    let events=[];const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file))),{env:{mark:(i,v)=>events.push([i,v])}});
    for(const item of oracle){events=[];assert.strictEqual(inst.exports.run(item.secret,0),item.value);assert.deepStrictEqual(events,item.events.map(x=>x.label));values++;}
  }
  for(const file of ['target.wasm','target-O3.wasm'])for(const mode of ['whole','depth','observer']){
    const bytes=fs.readFileSync(path.join(dir,file)),env={...contract,targetSha256:crypto.createHash('sha256').update(bytes).digest('hex')},guard=bind(bytes,env,{mode});
    const full=oracle.map(item=>{const r=guard.run(item.secret,0,contract.whole+1);assert.strictEqual(r.status,'ok');assert.strictEqual(r.value,item.value);assert.deepStrictEqual(r.ledger.filter(x=>x[0]==='event').map(x=>x.slice(1)),item.events.map(x=>x.label));assert(r.credit>=item.total);values++;return r;});
    const finalByClass={};dataset.forEach((item,i)=>{const v=full[i].credit;if(finalByClass[item.value]!==undefined)assert.strictEqual(v,finalByClass[item.value]);finalByClass[item.value]=v;});
    let completed=0,publicEvents=0;
    for(let budget=0;budget<=contract.whole+1;budget++){
      const prefixes=new Map();
      for(const item of dataset){const r=guard.run(item.secret,0,budget);budgets++;completed+=r.status==='ok';publicEvents+=r.events;const prefix=[];
        for(const row of r.ledger){if(row[0]==='event'||row[0]==='return')prefix.push(row);if(row[0]==='reserve'){const key=JSON.stringify(prefix);if(prefixes.has(key)){assert.deepStrictEqual(row,prefixes.get(key));prefixChecks++;}else prefixes.set(key,row);}}
      }
    }
    const stats={completed,publicEvents,finalByClass,totalFinalCredit:dataset.reduce((n,_,i)=>n+full[i].credit,0)};
    if(modes[mode])assert.deepStrictEqual(stats,modes[mode]);else modes[mode]=stats;
  }
  rows.push({kind:record.kind,oracleInputs:oracle.length,modes});
}
const report={values,budgets,prefixChecks,rows,node:process.version,v8:process.versions.v8,note:'One external dataset, four self-generated models. Logical costs; not timing privacy or four third-party applications.'};fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({values,budgets,prefixChecks,rows}));
