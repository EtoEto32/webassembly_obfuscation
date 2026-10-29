'use strict';
// Only the callable public oracle is passed to learn(). This is a small, stated
// expression grammar, not general program inference or a source-reading attack.
const rot=(x,n)=>((x<<(n&31))|(x>>>((32-n)&31)))|0;
const ops={add:(a,b)=>(a+b)|0,xor:(a,b)=>a^b,and:(a,b)=>a&b,or:(a,b)=>a|b};
function ev(e,x,y){if(e==='x')return x;if(e==='y')return y;if(typeof e==='number')return e;
  if(e[0]==='rot')return rot(ev(e[1],x,y),e[2]);return ops[e[0]](ev(e[1],x,y),ev(e[2],x,y));}
function learn(oracle){
  const queries=[],cache=new Map();
  const ask=(a,b)=>{const key=a+':'+b;if(cache.has(key))return cache.get(key);
    const v=oracle(a,b)|0;cache.set(key,v);queries.push({input:[a,b],value:v});return v;};
  let seed=0x2be1967;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};
  const train=[[0,0],[1,0],[0,1],[-1,-1]];
  for(let i=0;i<12;i++)train.push([rnd(),rnd()]);
  const c=ask(0,0),wanted=train.map(([a,b])=>ask(a,b));let tested=0;
  function match(e){tested++;return train.every(([a,b],i)=>ev(e,a,b)===wanted[i]);}
  function* candidates(){
    for(const outer of Object.keys(ops))for(const inner of Object.keys(ops))for(const z of ['x','y'])for(let k=0;k<32;k++)
      yield [outer,[inner,'x','y'],['rot',z,k]];
    for(const outer of Object.keys(ops))for(const left of Object.keys(ops))for(const right of Object.keys(ops))
      for(const [x,y] of [['x','y'],['y','x']])for(let k=0;k<32;k++)
        yield [outer,[left,x,['rot',y,k]],[right,y,c]];
  }
  for(const e of candidates())if(match(e)){
    let mismatch=0;for(let i=0;i<256;i++){const a=rnd(),b=rnd();if(ev(e,a,b)!==ask(a,b))mismatch++;}
    if(mismatch)return {status:'holdout_mismatch',expression:e,tested,queries,mismatch};
    return {status:'matched',expression:e,tested,queries,holdout:256};
  }
  return {status:'not_found_in_5120_templates',tested,queries};
}
module.exports={learn};
if(require.main===module){
  const fs=require('fs'),path=require('path'),root=path.resolve(process.argv[2]),dest=path.join(root,'io-audit.json');
  if(fs.existsSync(dest))throw Error('Refuse overwrite');
  const m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'))),rows=[];
  for(const r of m.rows){
    const oracle=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,r.wasm)))).exports.run;
    const learned=learn(oracle);rows.push({family:r.family,mode:r.mode,optimization:r.optimization,wasm:r.wasm,...learned});
  }
  const result={grammar:'1024 op(op(x,y),rot(z,k)) plus 4096 op(op(x,rot(y,k)),op(y,f(0,0))), swapped x/y allowed in second family; op in add/xor/and/or.',
    oracle_scope:'Public input/output only. Source and generator metadata not passed to learner.',rows};
  fs.writeFileSync(dest,JSON.stringify(result,null,2));console.log(JSON.stringify(rows.map(({family,mode,optimization,status,tested,expression,queries})=>({family,mode,optimization,status,tested,expression,queries:queries.length}))));
  if(rows.some(x=>x.status!=='matched'))process.exitCode=1;
}
