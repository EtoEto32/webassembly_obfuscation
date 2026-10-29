'use strict';
const fs=require('node:fs'),path=require('node:path');
function rot(x,n){return((x<<n)|(x>>>(32-n)))>>>0;}
function enc(a,b,kind){if(kind==='high'||kind==='wide')a=(a^rot(b,7))>>>0;if(kind==='low'||kind==='wide')b=(b^rot(a,13))>>>0;return[a>>>0,b>>>0];}
function dec(a,b,kind){if(kind==='low'||kind==='wide')b=(b^rot(a,13))>>>0;if(kind==='high'||kind==='wide')a=(a^rot(b,7))>>>0;return[a>>>0,b>>>0];}
function instantiate(file){const bytes=fs.readFileSync(file),memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),module=new WebAssembly.Module(bytes);return{module,memory,physical:new Uint32Array(memory.buffer),api:new WebAssembly.Instance(module,{env:{memory}}).exports};}
function save(out,name,value){const f=path.join(out,name);if(fs.existsSync(f))throw Error('refuse overwrite '+f);fs.writeFileSync(f,JSON.stringify(value,null,2));}
function rng(seed){return()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;}
function outcome(fn,args){try{return{result:fn(...args)};}catch(e){if(e instanceof WebAssembly.RuntimeError)return{trap:true};throw e;}}
function initialize(obj,codec,seed){const r=rng(seed);for(let i=0;i<obj.physical.length;i+=2)obj.physical.set(enc(r(),r(),codec),i);}
function identify(file){
  const start=performance.now(),o=instantiate(file),observations=[];
  for(const[a,b]of[[0,1],[1,0]]){o.api.store(0,a);o.api.store(4,b);observations.push([o.physical[0],o.physical[1]]);}
  const matches=['identity','low','high','wide'].filter(k=>[[0,1],[1,0]].every(([a,b],i)=>enc(a,b,k).every((v,j)=>v===observations[i][j])));
  if(matches.length!==1)throw Error('unsupported encoding family');
  return{codec:matches[0],store_calls:4,observed_words:4,elapsed_ms:performance.now()-start,observations};
}
module.exports={enc,dec,instantiate,save,rng,outcome,initialize,identify};
