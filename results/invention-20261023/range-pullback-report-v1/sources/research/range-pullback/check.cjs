const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))),targets=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed=0xe473bb91;const rand=()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;
let rows=[],calls=0,traps=0,negative=[];
for(const c of cases){
  const inputs=[],n=c.plan.length*3+1;
  const encode=(ops,q)=>{let a=Array(n).fill(0);c.plan.forEach(([d,s,l],i)=>{a[d]=ops[i][0]|0;a[s]=ops[i][1]|0;a[l]=ops[i][2]|0;});a[n-1]=q|0;return a;};
  // Exact bounds, zero lengths, overlap in both directions, wide unsigned sums.
  const edge=[[0,0,0],[65536,65536,0],[65537,0,0],[0,65537,0],[65535,0,1],[0,65535,1],[65535,0,2],[0,65535,2],[0xffffffff,1,2],[1,0xffffffff,2],[0,0,0xffffffff],[1,0,31],[0,1,31],[0,0,65536]];
  for(let step=0;step<c.plan.length;step++)for(const op of edge)for(const q of [0,1,15,31,4095,65535,65536,0xffffffff]){
    let ops=c.plan.map((_,i)=>[i*17,i*11,48]);ops[step]=op;inputs.push(encode(ops,q));
  }
  for(let i=0;i<2048;i++){
    let ops=c.plan.map(()=>{let l=rand()%257;return [rand()%(65537-l),rand()%(65537-l),l];});
    if(i%2===0)ops=c.plan.map(()=>{let l=rand()%65;return [rand()%(257-l),rand()%(257-l),l]});
    const chosen=ops[rand()%ops.length];let q=i%3===0?chosen[0]+(chosen[2]?rand()%chosen[2]:0):rand()%65536;
    inputs.push(encode(ops,q));
  }
  function reference(args){
    const memory=new Uint8Array(65536);memory.set(c.initial);
    for(const [d,s,l] of c.plan){const dst=args[d]>>>0,src=args[s]>>>0,len=args[l]>>>0;if(dst+len>65536||src+len>65536)return {trap:true};memory.copyWithin(dst,src,src+len);}
    const q=args[n-1]>>>0;return q>=65536?{trap:true}:{value:memory[q]};
  }
  const expects=inputs.map(reference);
  for(const target of targets.filter(x=>x.name===c.name)){
    const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,target.file)))).exports;
    let tc=0,tt=0,first=null,mismatches=0;
    for(let i=0;i<inputs.length;i++){
      let result;try{result={value:e.run(...inputs[i])>>>0}}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;result={trap:true};}
      tc++;if(result.trap)tt++;
      if(JSON.stringify(result)!==JSON.stringify(expects[i])){mismatches++;if(!first)first={args:inputs[i],expected:expects[i],actual:result};}
    }
    const row={file:target.file,calls:tc,traps:tt,mismatches,first};
    if(target.negative){if(!mismatches)throw Error('negative not detected '+target.file);negative.push(row);}
    else{if(mismatches)throw Error(JSON.stringify(row));calls+=tc;traps+=tt;rows.push(row);}
  }
}
console.log(JSON.stringify({binaries:rows.length,calls,traps,mismatches:0,rows,negative,seed:'0xe473bb91'}));
