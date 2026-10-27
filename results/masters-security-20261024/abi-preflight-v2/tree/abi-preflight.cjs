'use strict';
function estimate(buffer,depth,ptr,len,budget,memoize=true){
 if(!(buffer instanceof ArrayBuffer)||!Number.isSafeInteger(budget)||budget<0||budget>1e8)throw Error('preflight contract');
 const view=new DataView(buffer),cache=new Map();let visits=0,hits=0,edges=0;
 const cap=budget+1,add=(a,b)=>Math.min(cap,a+b);
 function cost(d,p,n){
  if(!Number.isInteger(d)||d<1||d>8||!Number.isInteger(p)||p<0||!Number.isInteger(n)||n<0||p>0xffffffff||n>0xffffffff)throw Error('shape');
  const stride=d===1?1:8;
  if((d>1&&p%4)||p>buffer.byteLength||n>Math.floor((buffer.byteLength-p)/stride))throw Error('bounds/alignment');
  const key=d+':'+p+':'+n;if(memoize&&cache.has(key)){hits++;return cache.get(key);}visits++;
  // Saturation preserves the budget decision without overflowing counters.
  let total=add(1,n);
  if(d>1&&total<=budget)for(let i=0;i<n;i++){
   if(++edges>100000)throw Error('metadata budget');
   total=add(total,cost(d-1,view.getUint32(p+8*i,true),view.getUint32(p+8*i+4,true)));
   if(total>budget)break;
  }
  if(memoize)cache.set(key,total);return total;
 }
 const costUnits=cost(depth,ptr>>>0,len>>>0);return{accepted:costUnits<=budget,costUnits,visits,hits,edges,memoEntries:cache.size};
}
function guard(buffer,ptr,len,config){
 const result=estimate(buffer,3,ptr,len,config.budget,config.mode==='memo');config.last=result;
 if(!result.accepted)throw Error('preflight budget');
}
module.exports={estimate,guard};
