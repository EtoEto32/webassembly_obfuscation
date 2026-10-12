const fs=require('fs'),path=require('path'),assert=require('assert/strict'),cp=require('child_process'),crypto=require('crypto');
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:false});
const save=(f,v)=>fs.writeFileSync(path.join(out,f),JSON.stringify(v,null,2));
const evalF=(cs,b,mask)=>cs.reduceRight((r,c)=>(Math.imul(r,b)+c)&mask,0)>>>0;
const signature=cs=>Array.from({length:16},(_,b)=>evalF(cs,b,15)).join(',');
function dictionary(degree){const map=new Map();let tested=0;for(let id=0;id<16**(degree+1);id++){let n=id;const c=[];for(let i=0;i<=degree;i++){c.push(n%16);n=Math.floor(n/16);}const s=signature(c);if(!map.has(s))map.set(s,c);tested++;}return {map,tested};}
const weak=dictionary(2),strong=dictionary(3),candidates=[];
for(let id=0;id<256;id++){let n=id;const f=[];for(let j=0;j<4;j++){f.push(n%4);n=Math.floor(n/4);}candidates.push({id,f,signature:signature(f)});}
const blocked=new Set(),rounds=[],survivors=[];
for(const cand of candidates){if(blocked.has(cand.signature))continue;const decoder=weak.map.get(cand.signature);if(decoder){blocked.add(cand.signature);rounds.push({id:cand.id,decoder,blockedSignature:cand.signature,blockedCandidateIds:candidates.filter(c=>c.signature===cand.signature).map(c=>c.id)});}else survivors.push(cand);}
const heldout=survivors.map(c=>({id:c.id,decoder:strong.map.get(c.signature)||null}));
// Canonical polynomial expansion; each term is coefficient*a^pa*b^pb.
function lifted(f,c){const terms=new Map();const add=(a,b,k)=>terms.set(a+','+b,(terms.get(a+','+b)||0)+k);
 add(2,0,1);add(1,0,c);
 for(let i=0;i<f.length;i++){add(1,i,2*f[i]);add(0,i,c*f[i]);for(let j=0;j<f.length;j++)add(0,i+j,f[i]*f[j]);}
 // f(b+1) via independently explicit Pascal rows for degree<=3.
 const choose=[[1],[1,1],[1,2,1],[1,3,3,1]];
 for(let i=0;i<f.length;i++)for(let j=0;j<=i;j++)add(0,j,-f[i]*choose[i][j]);
 return [...terms].filter(([,k])=>k!==0).map(([ab,k])=>({powers:ab.split(',').map(Number),coefficient:k}));
}
const pow=(a,n)=>{let r=1;for(let i=0;i<n;i++)r=Math.imul(r,a);return r;};
const evalTerms=(terms,a,b,u,mask)=>terms.reduce((r,t)=>(r+Math.imul(t.coefficient,Math.imul(pow(a,t.powers[0]),pow(b,t.powers[1]))))|0,u)&mask;
const bigF=(f,b,w)=>BigInt.asUintN(w,f.reduceRight((r,c)=>r*b+BigInt(c),0n));
let checks=0;
for(const cand of candidates){cand.updateEven=lifted(cand.f,5);cand.updateOdd=lifted(cand.f,3);
 for(let a=0;a<16;a++)for(let b=0;b<16;b++)for(let u=0;u<16;u++){
  const A=BigInt(a),B=BigInt(b),U=BigInt(u),x=BigInt.asUintN(4,A+bigF(cand.f,B,4));
  const expected=Number(BigInt.asUintN(4,x*x+((u&1)?3n:5n)*x+U));
  const nextA=evalTerms((u&1)?cand.updateOdd:cand.updateEven,a,b,u,15),nextB=(b+1)&15;
  assert.equal(Number(BigInt.asUintN(4,BigInt(nextA)+bigF(cand.f,BigInt(nextB),4))),expected);checks++;
 }
}
save('search.json',{weakGrammar:{degree:2,coefficientRange:[0,15],enumerated:weak.tested,distinctFunctions:weak.map.size},strongGrammar:{degree:3,coefficientRange:[0,15],enumerated:strong.tested,distinctFunctions:strong.map.size},candidates,rounds,survivorIds:survivors.map(c=>c.id),heldout,correctnessChecks:checks});
assert(survivors.length>0);const chosen=survivors[0],f=chosen.f;
const c=n=>`(i32.const ${n|0})`,g=n=>`(local.get $${n})`,o=(op,a,b)=>`(i32.${op} ${a} ${b})`;
const sum=terms=>terms.reduce((a,b)=>o('add',a,b),c(0));
const power=(v,p)=>p===0?c(1):Array.from({length:p-1},()=>v).reduce((a,b)=>o('mul',a,b),v);
const fwat=v=>sum(f.map((coef,i)=>o('mul',c(coef),power(v,i))));
const twat=terms=>sum([...terms.map(t=>o('mul',c(t.coefficient),o('mul',power(g('a'),t.powers[0]),power(g('b'),t.powers[1])))),g('u')]);
const cc=`(select ${c(3)} ${c(5)} ${o('and',g('u'),c(1))})`;
const native=o('add',o('add',o('mul',g('a'),g('a')),o('mul',cc,g('a'))),g('u'));
const decoded=o('add',g('a'),fwat(g('b')));
const conjugate=`(local.set $x ${decoded}) ${o('sub',o('add',o('add',o('mul',g('x'),g('x')),o('mul',cc,g('x'))),g('u')),fwat(o('add',g('b'),c(1))))}`;
const expanded=`(if (result i32) ${o('and',g('u'),c(1))} (then ${twat(chosen.updateOdd)}) (else ${twat(chosen.updateEven)}))`;
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe'),opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe');
let seed=0xc012bc39;const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const edge=[0,1,2,3,15,16,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const inputs=[];for(const a of edge)for(const b of edge)for(const u of [0,1,0xffffffff])inputs.push([a,b,u]);for(let i=0;i<1024;i++)inputs.push([rng(),rng(),rng()]);
save('inputs.json',{seed:'0xc012bc39',inputs});
const results=[];
for(const [variant,body]of Object.entries({plain:native,conjugate,expanded})){
 const wat=`(module (func (export "step") (param $a i32)(param $b i32)(param $u i32)(result i32)(local $x i32) ${body}) (func (export "init") (param $a i32)(param $b i32)(result i32) ${variant==='plain'?g('a'):o('sub',g('a'),fwat(g('b')))}) (func (export "decode") (param $a i32)(param $b i32)(result i32) ${variant==='plain'?g('a'):decoded}))`;
 fs.writeFileSync(path.join(out,variant+'.wat'),wat);cp.execFileSync(asm,[path.join(out,variant+'.wat'),'-o',path.join(out,variant+'-raw.wasm')]);cp.execFileSync(opt,[path.join(out,variant+'-raw.wasm'),'-O2','-o',path.join(out,variant+'-O2.wasm')]);
 for(const mode of ['raw','O2']){const file=variant+'-'+mode+'.wasm',bytes=fs.readFileSync(path.join(out,file)),e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,observations=[];
  for(const [x,b,u]of inputs){const a=e.init(x,b)>>>0;assert.equal(e.decode(a,b)>>>0,x);const a2=e.step(a,b,u)>>>0,actual=e.decode(a2,(b+1)>>>0)>>>0;
   const X=BigInt(x),U=BigInt(u),expected=Number(BigInt.asUintN(32,X*X+((u&1)?3n:5n)*X+U));assert.equal(actual,expected);observations.push({a,a2,actual,expected});}
  save(file+'.observations.json',observations);results.push({file,variant,mode,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),cases:inputs.length,mismatches:0});
 }
}
save('results.json',{node:process.version,v8:process.versions.v8,wabt:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),binaryen:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim(),chosenId:chosen.id,chosenEncoding:f,results});
console.log(JSON.stringify({candidates:256,correctnessChecks:checks,blockingRounds:rounds.length,weakSurvivors:survivors.length,strongRecovered:heldout.filter(h=>h.decoder).length,chosen:chosen.id,wasmExecutions:results.reduce((s,r)=>s+r.cases,0),mismatches:0}));
