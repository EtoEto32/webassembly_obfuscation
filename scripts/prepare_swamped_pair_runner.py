"""Extract reviewed host functions into a reusable loader, retaining the older report provenance."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'experiments/runtime-reference'
s=(p/'swamped-seed-check.cjs').read_text()
host=s[s.index('const memory='):s.index('const report=')]
host=host.replace('const now=Date.now();','const now=1700000000500;')
loader="'use strict';\nfunction load(bytes){\n"+host+'''
const exports=new WebAssembly.Instance(new WebAssembly.Module(bytes),{env}).exports;
view.setUint32(dynamicPtr,heapTop,true);
const ctx=exports._cryptonight_create(),input=exports._malloc(256),output=exports._malloc(32);
if(!ctx||!input||!output)throw Error('Allocation failed');
return {calls,layout:{dynamicPtr,stackTop,heapTop,tm,ctx,input,output},
 hash(v){const b=Buffer.from(v.hex,'hex');new Uint8Array(memory.buffer).set(b,input);
 exports._cryptonight_hash_variant_0(ctx,input,output,b.length);},
 output(){return Buffer.from(memory.buffer,output,32).toString('hex');},
 close(){exports._cryptonight_destroy(ctx);}};
}
module.exports={load};
'''
(p/'swamped-host.cjs').write_text(loader)
print('Saved recovered host with a fixed initialization timestamp; older experiment source unchanged')
