'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const root=process.argv[2],read=p=>JSON.parse(fs.readFileSync(p));
class BudgetStop extends Error{}
const manifest=read(path.join(root,'manifest.json'));let checks=0,budgetChecks=0,coverageChecks=0,refunds=0;const rows=[];

function scheduleFromExecutions(executions){
  // Independent baseline: examine actual interpreter traces, not structural paths.
  const nodes=[];
  function build(prefix,chosen){
    const i=prefix.length,index=nodes.length;
    const node={bound:Math.max(...chosen.map(p=>p.events[i]?.cost??p.total)),terminalBound:null,next:{}};nodes.push(node);
    const terminal=chosen.filter(p=>p.events.length===i);if(terminal.length)node.terminalBound=Math.max(...terminal.map(p=>p.total));
    const labels=new Set(chosen.filter(p=>p.events[i]).map(p=>p.events[i].label.join(',')));
    for(const key of labels)node.next[key]=build(prefix.concat([key]),chosen.filter(p=>p.events[i]?.label.join(',')===key));
    return index;
  }build([],executions);return {nodes};
}

function makeRunner(mod,env,mode){
  let expected,index,depth,credit,remaining,ledger,eventIndex,started,stopped;
  function adjust(target){
    assert(Number.isSafeInteger(target)&&target>=0,'invalid bound');
    const delta=target-credit;ledger.push(['reserve',target,delta]);
    if(delta>remaining){stopped=true;throw new BudgetStop();}
    remaining-=delta;credit=target;
  }
  function target(){return mode==='whole'?env.whole:mode==='depth'?env.depthBounds[depth]:env.nodes[index].bound;}
  const instance=new WebAssembly.Instance(mod,{env:{mark(id,payload){
    if(id===-2147483648){assert(!started);started=true;adjust(target());return;}
    assert(started);assert.deepStrictEqual([id,payload],expected.events[eventIndex].label);
    assert(credit>=expected.events[eventIndex].cost,'under-reserved at published event');coverageChecks++;
    ledger.push(['event',id,payload]);eventIndex++;depth++;
    index=env.nodes[index].next[id+','+payload];assert.notStrictEqual(index,undefined);
    adjust(target());
  }}});
  return function run(item,budget){
    expected=item;index=0;depth=0;credit=0;remaining=budget;ledger=[];eventIndex=0;started=false;stopped=false;
    let value,status;
    try{value=instance.exports.run(item.secret,item.x)>>>0;status='ok';assert(credit>=item.total,'under-reserved at return');coverageChecks++;
      assert.strictEqual(value,item.value);assert.strictEqual(eventIndex,item.events.length);
      // The return is public before any terminal-specific refund.
      ledger.push(['return',value]);
      if(mode==='observer'||mode==='manual'){assert(env.nodes[index].terminalBound>=item.total);adjust(env.nodes[index].terminalBound);}
    }catch(e){if(!(e instanceof BudgetStop))throw e;status='budget';}
    assert.strictEqual(stopped,status==='budget');
    const result={status,value,credit,remaining,events:eventIndex,ledger};
    refunds+=ledger.filter(v=>v[0]==='reserve'&&v[2]<0).length;return result;
  };
}

function assertPublicPrefixOnly(outcomes){
  const observed=new Map();
  for(const outcome of outcomes){
    const prefix=[];
    for(const row of outcome.ledger){
      if(row[0]==='event'||row[0]==='return')prefix.push(row);
      if(row[0]==='reserve'){
        const key=JSON.stringify(prefix);
        if(observed.has(key))assert.deepStrictEqual(row,observed.get(key),'accounting before release depends on hidden data');
        else observed.set(key,row);
      }
    }
  }
}

for(const record of manifest.records){
  const folder=path.join(root,record.kind),env=read(path.join(folder,'target.json')),oracle=read(path.join(folder,'oracle.json'));
  const original=new WebAssembly.Module(fs.readFileSync(path.join(folder,'original.wasm')));
  let current=[];const plain=new WebAssembly.Instance(original,{env:{mark:(a,b)=>current.push([a,b])}});
  for(const item of oracle){current=[];assert.strictEqual(plain.exports.run(item.secret,item.x)>>>0,item.value);assert.deepStrictEqual(current,item.events.map(e=>e.label));checks++;}
  const actual=oracle.filter(v=>v.x===0);const manual=scheduleFromExecutions(actual);let rawStats;
  for(const file of ['target.wasm','target-O3.wasm']){
    const bytes=fs.readFileSync(path.join(folder,file));if(file==='target.wasm')assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'),env.targetSha256);
    const mod=new WebAssembly.Module(bytes);const modes={};
    for(const mode of ['whole','depth','observer','manual']){
      const runner=makeRunner(mod,mode==='manual'?manual:env,mode);const full=oracle.map(p=>runner(p,env.whole+1));checks+=full.length;assert(full.every(v=>v.status==='ok'));assertPublicPrefixOnly(full);
      let success=0,published=0,negativeRefunds=0;const finalCredits={};
      for(let budget=0;budget<=env.whole+1;budget++){
        const outputs=actual.map(p=>runner(p,budget));budgetChecks+=outputs.length;assertPublicPrefixOnly(outputs);
        success+=outputs.filter(v=>v.status==='ok').length;published+=outputs.reduce((a,v)=>a+v.events,0);negativeRefunds+=outputs.flatMap(v=>v.ledger).filter(v=>v[0]==='reserve'&&v[2]<0).length;
      }
      actual.forEach(p=>{finalCredits[p.secret]=runner(p,env.whole+1).credit;});
      modes[mode]={success,published,negativeRefunds,finalCredits};
    }
    if(rawStats)assert.deepStrictEqual(modes,rawStats);else rawStats=modes;
    rows.push({kind:record.kind,file,modes});
  }
}
const report={node:process.version,v8:process.versions.v8,checks,budgetChecks,coverageChecks,refunds,rows,note:'Logical source-opcode accounting only. Seven self-authored fixtures. Manual schedule is exact only over the 16 tested secret classes; no general proof for arbitrary programs.'};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({checks,budgetChecks,coverageChecks,refunds}));
