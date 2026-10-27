const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const dir=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function pow(a,b,n){let r=1n;for(;b;b>>=1n,a=a*a%n)if(b&1n)r=r*a%n;return r;}
async function main(){
 const p=BigInt(m.prime),q=BigInt(m.q);
 assert.equal(p,BigInt('0x'+crypto.getDiffieHellman('modp14').getPrime().toString('hex')));
 assert.equal(pow(2n,q,p),1n);assert((1n<<2040n)<q && q<(1n<<2048n));
 let calls=0;
 for(const e of m.entries){
  const {instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(dir,e.file)));
  const mem=new Uint8Array(instance.exports.memory.buffer),pat=Buffer.from(e.pattern,'hex');
  const other=pat[0]^255;
  const cases=[pat,Buffer.concat([Buffer.from([other]),pat]),Buffer.alloc(pat.length,other),Buffer.concat([pat,pat])];
  for(const s of cases)for(const ptr of [0,65536-s.length]){
   mem.fill(17);mem.set(s,ptr);const before=Buffer.from(mem);
   assert.equal(instance.exports.run(ptr,s.length),s.indexOf(pat));
   assert.deepEqual(Buffer.from(mem),before);calls++;
  }
 }
 const r={binaries:m.entries.length,calls,mismatches:0,parameters_match_node_openssl_modp14:true,
  patterns:'length 1 and 255; all 00 and all FF',node:process.version};
 fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(r,null,2));console.log(JSON.stringify(r));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
