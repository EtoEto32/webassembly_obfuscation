'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const N=6;
function* permutations(a,k=0){if(k===a.length){yield a.slice();return;}for(let i=k;i<a.length;i++){[a[k],a[i]]=[a[i],a[k]];yield* permutations(a,k+1);[a[k],a[i]]=[a[i],a[k]];}}
const contiguous=(p,s,n)=>Array.from({length:n},(_,i)=>p[s+i]===p[s]+i).every(Boolean);
const cases=[];for(let n=1;n<=N;n++)for(let s=0;s+n<=N;s++)for(let d=0;d+n<=N;d++)cases.push({s,d,n});
const rows=[];let comparisons=0,nativeComparisons=0,naiveFailures=0,example=null;
for(const p of permutations(Array.from({length:N},(_,i)=>i))){
 let eligible=0;
 for(const {s,d,n} of cases){
  const original=Array.from({length:N},(_,i)=>i+11),expected=original.slice();expected.splice(d,n,...original.slice(s,s+n));
  const encoded=Array(N);for(let i=0;i<N;i++)encoded[p[i]]=original[i];
  const actual=encoded.slice();
  // Logical memmove direction; accesses individually translated by p.
  const order=Array.from({length:n},(_,i)=>i);if(d>s)order.reverse();
  for(const i of order)actual[p[d+i]]=actual[p[s+i]];
  assert.deepEqual(p.map(i=>actual[i]),expected);comparisons++;
  if(contiguous(p,s,n)&&contiguous(p,d,n)){
   const native=encoded.slice();native.splice(p[d],n,...encoded.slice(p[s],p[s]+n));
   assert.deepEqual(p.map(i=>native[i]),expected);eligible++;nativeComparisons++;
  }
  const naive=encoded.slice();naive.splice(p[d],n,...encoded.slice(p[s],p[s]+n));
  if(JSON.stringify(p.map(i=>naive[i]))!==JSON.stringify(expected)){naiveFailures++;example??={permutation:p.slice(),s,d,n,expected,actual:p.map(i=>naive[i])};}
 }
 rows.push({permutation:p,eligible,total:cases.length,allAdjacentContiguous:Array.from({length:N-1},(_,i)=>contiguous(p,i,2)).every(Boolean)});
}
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'permutations.json'),JSON.stringify(rows,null,2));
const result={node:process.version,N,permutations:rows.length,cases_per_permutation:cases.length,logical_order_comparisons:comparisons,mismatches:0,native_eligible_comparisons:nativeComparisons,naive_unconditional_failures:naiveFailures,first_counterexample:example,all_adjacent_contiguous_layouts:rows.filter(r=>r.allAdjacentContiguous).map(r=>r.permutation),script_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),scope:'Abstract finite byte-layout model. No Wasm execution, traps, performance, or obfuscation resistance evaluated.'};
assert.equal(result.all_adjacent_contiguous_layouts.length,1);
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
