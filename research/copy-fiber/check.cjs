'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const vendor=fs.readFileSync(path.join(root,'experiments/sha256-research-baseline/vendor/sha256.js'),'utf8');
const K=vendor.match(/var K = \[([\s\S]*?)\]/)[1].match(/0x[0-9a-f]+/ig).map(Number);
const IV=[...vendor.matchAll(/this\._[a-h] = (0x[0-9a-f]+)/g)].map(m=>Number(m[1]));assert.equal(IV.length,8);
const u=x=>x>>>0,rot=(x,n)=>u((x>>>n)|(x<<(32-n))),rol=(x,n)=>rot(x,32-n);
function reference(h0,m){
 const w=m.slice();for(let i=16;i<64;i++)w[i]=u(w[i-16]+(rot(w[i-15],7)^rot(w[i-15],18)^(w[i-15]>>>3))+w[i-7]+(rot(w[i-2],17)^rot(w[i-2],19)^(w[i-2]>>>10)));
 let [a,b,c,d,e,f,g,h]=h0;
 for(let i=0;i<64;i++){const t1=u(h+(rot(e,6)^rot(e,11)^rot(e,25))+((e&f)^(~e&g))+K[i]+w[i]),t2=u((rot(a,2)^rot(a,13)^rot(a,22))+((a&b)^(a&c)^(b&c)));[a,b,c,d,e,f,g,h]=[u(t1+t2),a,b,c,u(d+t1),e,f,g];}
 return [a,b,c,d,e,f,g,h].map((x,i)=>u(x+h0[i]));
}
function hash(compress,data){
 const len=Math.ceil((data.length+9)/64)*64,b=Buffer.alloc(len);data.copy(b);b[data.length]=128;b.writeBigUInt64BE(BigInt(data.length)*8n,len-8);
 let h=IV.slice();for(let p=0;p<len;p+=64)h=compress(...h,...Array.from({length:16},(_,i)=>b.readUInt32BE(p+i*4))).map(u);
 const o=Buffer.alloc(32);h.forEach((x,i)=>o.writeUInt32BE(x,i*4));return o.toString('hex');
}
function decode(y,h,info){
 if(!info.gates)return y;
 const x=y.map((v,i)=>u(v^h[i]));
 for(const [i,j,k,r,s] of info.gates.slice().reverse()){
  const z=info.linear?(rol(x[j],r)^rol(x[k],s)):(rol(u(x[j]+x[k]),r)^(x[j]&rol(x[k],s)));x[i]=u(x[i]^z);
 }
 return x.map((v,i)=>u(v^h[i]));
}
function corpus(){
 let seed=211052;const rng=()=>seed=u(Math.imul(seed,1664525)+1013904223);
 const cases=[];for(const v of [0,1,0x7fffffff,0x80000000,0xffffffff])cases.push(Array(24).fill(v));cases.push(Array.from({length:24},(_,i)=>i&1?0x55555555:0xaaaaaaaa));
 for(let j=0;j<256;j++)cases.push(Array.from({length:24},rng));
 const lengths=[0,1,3,7,31,32,55,56,57,63,64,65,111,112,119,120,121,127,128,129,255,256,257,511,512,513,1024];
 for(let i=0;i<12;i++)lengths.push(rng()%2049);
 const messages=lengths.map(n=>Buffer.from(Array.from({length:n},()=>rng()>>>24)));messages.push(Buffer.from('abc'),Buffer.from('abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'));
 return {cases,messages};
}
function instantiate(f){const b=fs.readFileSync(f);assert(WebAssembly.validate(b));return new WebAssembly.Instance(new WebAssembly.Module(b)).exports;}
function check(targets){
 const {cases,messages}=corpus(),expected=cases.map(x=>reference(x.slice(0,8),x.slice(8))),hashes=messages.map(b=>crypto.createHash('sha256').update(b).digest('hex')),rows=[];
 for(const t of targets){
  const ex=instantiate(t.path);assert.deepEqual(Object.keys(ex),['compress']);
  for(let i=0;i<cases.length;i++)assert.deepEqual(ex.compress(...cases[i]).map(u),expected[i],t.label+' compress '+i);
  for(let i=0;i<messages.length;i++)assert.equal(hash(ex.compress,messages[i]),hashes[i],t.label+' hash '+i);
  let memoryCases=0;
  if(t.probe){const pe=instantiate(t.probe);for(let i=0;i<16;i++){
    const ans=pe.compress(...cases[i]).map(u),mem=new DataView(pe.memory.buffer);assert.deepEqual(ans,expected[i]);
    const h=Array.from({length:8},(_,j)=>mem.getUint32(j*4,true)),y=Array.from({length:8},(_,j)=>mem.getUint32(32+j*4,true));assert.deepEqual(h,cases[i].slice(0,8));
    assert.deepEqual(decode(y,h,t.info),ans.map((v,j)=>u(v-h[j])));assert(new Uint8Array(pe.memory.buffer,64).every(x=>x===0));memoryCases++;
  }}
  rows.push({label:t.label,compress:cases.length,full_hash:messages.length,memory_cases:memoryCases,mismatches:0});
 }
 return {node:process.version,v8:process.versions.v8,seed:211052,targets:rows,compress:rows.reduce((s,r)=>s+r.compress,0),full_hash:rows.reduce((s,r)=>s+r.full_hash,0),memory_cases:rows.reduce((s,r)=>s+r.memory_cases,0),mismatches:0,corpus_sha256:crypto.createHash('sha256').update(JSON.stringify(cases)).update(Buffer.concat(messages)).digest('hex')};
}
if(require.main===module){const out=process.argv[3];if(fs.existsSync(out))throw Error('Refuse overwrite');const r=check(JSON.parse(fs.readFileSync(process.argv[2])));fs.writeFileSync(out,JSON.stringify(r,null,2));console.log(JSON.stringify({targets:r.targets.length,compress:r.compress,full_hash:r.full_hash,memory_cases:r.memory_cases,mismatches:r.mismatches}));}
module.exports={reference,hash,decode,corpus,instantiate,check,IV};
