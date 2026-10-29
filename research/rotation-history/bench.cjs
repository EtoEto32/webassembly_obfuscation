const fs=require('fs'),{performance}=require('perf_hooks'),assert=require('assert');
const [target,baseline]=process.argv.slice(2);
const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports;
const e=get(target),b=get(baseline);let state=21102195;
const data=new DataView(e.memory.buffer),other=new DataView(b.memory.buffer);
for(let i=0;i<128;i++){state^=state<<13;state^=state>>>17;state^=state<<5;data.setUint32(4*i,state,true);other.setUint32(4*i,state,true);}
function batch(e,n){let checksum=0;const t=performance.now();for(let i=0;i<n;i++)checksum=((checksum<<3|checksum>>>29)+e.run(i^0x57a7139d,0,128)+i)|0;return {ms:performance.now()-t,checksum};}
assert.equal(batch(e,1024).checksum,batch(b,1024).checksum);
let n=32;while(n<2**18){if(batch(e,n).ms>=5)break;n*=2;}
const expected=batch(b,n).checksum,samples=[];
for(let i=0;i<9;i++){const r=batch(e,n);assert.equal(r.checksum,expected);samples.push(r.ms*1e6/n);}
console.log(JSON.stringify({ns:samples,batch:n,words:128,warmup:1024,rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
