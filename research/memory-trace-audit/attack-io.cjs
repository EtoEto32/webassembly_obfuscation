'use strict';

// A membership-query attack on the PUBLIC linked-fold API contract.
// This module receives only a callable oracle. It cannot read a Wasm file,
// memory, trace, generation map, node count, or original graph.
const rotl = (x, n) => ((x << (n & 31)) | (x >>> ((32 - n) & 31))) >>> 0;

function recoverIO(oracle, options = {}) {
  const maxNodes = options.maxNodes || 4096;
  const maxLength = options.maxLength || 8;
  const maxQueries = options.maxQueries || 100000;
  const maxFrontier = options.maxFrontier || 100000;
  const queries = [], cache = new Map(), phases = [];
  function ask(i, k) {
    const key = `${i}:${k}`;
    if (cache.has(key)) return cache.get(key);
    if (queries.length >= maxQueries) throw Error('query_budget');
    let r;
    try { r = {value: oracle(i, k) >>> 0}; }
    catch (e) {
      if (!(e instanceof WebAssembly.RuntimeError)) throw e;
      r = {trap: true};
    }
    queries.push({start: i, length: k, result: r});
    cache.set(key, r);
    return r;
  }
  // The documented contract traps iff the public start index is out of range,
  // even for a zero-length query. Discover this boundary instead of receiving N.
  if (ask(0, 0).trap) return {status:'unsupported_empty_domain',queries};
  let lo = 0, hi = 1;
  while (!ask(hi, 0).trap) {
    lo = hi; hi *= 2;
    if (hi > maxNodes) return {status:'node_budget',queries};
  }
  while (hi - lo > 1) {
    const mid = Math.floor((lo + hi) / 2);
    if (ask(mid, 0).trap) hi = mid; else lo = mid;
  }
  const n = hi;
  const values = Array.from({length:n}, (_,i)=>ask(i,1).value);
  if (values.some(x=>x === undefined)) return {status:'contract_mismatch',queries};
  const byValue = new Map();
  values.forEach((x,i)=>{if(!byValue.has(x))byValue.set(x,[]);byValue.get(x).push(i);});
  let candidates = values.map((v,i)=>{
    const two = ask(i,2);
    if (two.trap) return [];
    const wanted = (two.value ^ rotl(v,5)) >>> 0;
    const a = [...(byValue.get(wanted) || [])];
    // A terminal node stops immediately; it does NOT rotate a second time.
    if (two.value === v) a.push(-1);
    return a;
  });
  phases.push({length:2, queries:queries.length,
    unique:candidates.filter(x=>x.length===1).length,
    alternatives:candidates.reduce((s,x)=>s+x.length,0)});
  let frontierLimit = false;

  // Conservative bounded lookahead. A path can choose any remaining successor
  // at each visit; this over-approximates a deterministic graph. Therefore no
  // true edge is deleted if the public contract and query outputs are correct.
  function compatible(first, successor, length, wanted) {
    let frontier = new Map([[`${successor}:${values[first]}`,[successor,values[first]]]]);
    for (let step=1; step<length; step++) {
      const next = new Map();
      for (const [node,acc] of frontier.values()) {
        if(node === -1) {next.set(`-1:${acc}`,[-1,acc]); continue;}
        const v = (rotl(acc,5) ^ values[node]) >>> 0;
        for(const dst of candidates[node]) next.set(`${dst}:${v}`,[dst,v]);
      }
      if(next.size>maxFrontier) {frontierLimit=true;return true;}
      frontier=next;
    }
    for(const [,acc] of frontier.values()) if(acc===wanted)return true;
    return false;
  }
  for(let k=3;k<=maxLength && candidates.some(x=>x.length!==1);k++) {
    const answers=values.map((_,i)=>ask(i,k));
    if(answers.some(x=>x.trap))return {status:'contract_mismatch',queries};
    let changed;
    do {
      changed=false;
      const next=candidates.map((xs,i)=>xs.filter(j=>compatible(i,j,k,answers[i].value)));
      for(let i=0;i<n;i++)if(next[i].length!==candidates[i].length)changed=true;
      candidates=next;
    } while(changed && candidates.every(x=>x.length));
    phases.push({length:k,queries:queries.length,unique:candidates.filter(x=>x.length===1).length,
      alternatives:candidates.reduce((s,x)=>s+x.length,0)});
    if(candidates.some(x=>x.length===0))break;
  }
  const unique=candidates.every(x=>x.length===1);
  return {status: candidates.some(x=>!x.length)?'contract_mismatch':unique?'unique':'ambiguous',
    nodes:n,values,candidates,next:unique?candidates.map(x=>x[0]):null,queries,phases,frontierLimit,
    assumptions:['Known rotl32/XOR linked-fold API; start indices expose individual nodes.',
      'Range trap occurs before considering the traversal length; length is masked to 8 bits.',
      'Only public return values and trap occurrence are observed.']};
}

module.exports = {recoverIO};
