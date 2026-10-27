'use strict';
// Trusted contract produced from the matching original module. No guest execution
// is used to select a reserve; decisions use only public events already emitted.
const crypto=require('crypto');
class BudgetStop extends Error{}
function bind(bytes,contract,{mode='observer',capture=true,policy=()=>0}={}){
  if(!['whole','depth','observer'].includes(mode))throw new Error('mode');
  const hash=crypto.createHash('sha256').update(bytes).digest('hex');
  if(hash!==contract.targetSha256)throw new Error('contract/binary mismatch');
  const mod=new WebAssembly.Module(bytes);let active=false,started,node,depth,credit,remaining,events,ledger;
  function log(row){if(capture)ledger.push(row);}
  function adjust(target){
    if(!Number.isSafeInteger(target)||target<0)throw new Error('invalid contract bound');
    const delta=target-credit;log(['reserve',target,delta]);
    if(delta>remaining)throw new BudgetStop();remaining-=delta;credit=target;
  }
  function nextBound(){return mode==='whole'?contract.whole:mode==='depth'?contract.depthBounds[depth]:contract.nodes[node].bound;}
  const instance=new WebAssembly.Instance(mod,{env:{mark(id,payload){
    if(!active)throw new Error('outside call');
    if(id===-2147483648){if(started)throw new Error('duplicate start');started=true;adjust(nextBound());return;}
    if(!started)throw new Error('missing start');
    const next=contract.nodes[node].next[id+','+payload];
    if(!Number.isSafeInteger(next))throw new Error('unmodelled event');
    log(['event',id,payload]);events++;node=next;depth++;
    const change=policy(Object.freeze({id,payload,events,remaining}));
    if(!Number.isSafeInteger(change))throw new Error('invalid public budget input');
    if(change!==0){log(['budget-input',change]);remaining+=change;if(!Number.isSafeInteger(remaining))throw new Error('budget overflow');if(remaining<0)throw new BudgetStop();}
    adjust(nextBound());
  }}});
  return {run(secret,x,budget){
    if(active)throw new Error('reentry');if(!Number.isSafeInteger(budget)||budget<0)throw new Error('budget');
    active=true;started=false;node=depth=credit=events=0;remaining=budget;ledger=[];
    let status='ok',value;
    try{value=instance.exports.run(secret,x)>>>0;if(!started)throw new Error('missing start');log(['return',value]);if(mode==='observer')adjust(contract.nodes[node].terminalBound);}
    catch(e){if(!(e instanceof BudgetStop))throw e;status='budget';}
    finally{active=false;}
    return {status,value,credit,remaining,events,ledger};
  }};
}
module.exports={bind,BudgetStop};
