'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'artifacts');fs.mkdirSync(dir,{recursive:true});
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe'),opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe');
const g=n=>`(local.get $${n})`,add=(a,b)=>`(i32.add ${a} ${b})`,mul=(a,b)=>`(i32.mul ${a} ${b})`;
const dec=add(g('a'),mul(g('b'),g('b')));
const manifest=[];
for(const kind of ['plain','redundant']){
 const init=kind==='plain'?`(local.set $a ${g('x')})`:`(local.set $b ${g('mask')})(local.set $a (i32.sub ${g('x')} ${mul(g('b'),g('b'))}))`;
 const cond=kind==='plain'?g('a'):add(g('a'),g('b'));
 const plain=add(add(mul(g('a'),g('a')),mul(g('c'),g('a'))),g('y'));
 const expanded=add(add(add(add(mul(g('a'),g('a')),mul('(i32.const 2)',mul(g('a'),g('t')))),mul(g('t'),g('t'))),mul(g('c'),add(g('a'),g('t')))),g('y'));
 const step=kind==='plain'?`(local.set $a ${plain})`:`(local.set $t ${mul(g('b'),g('b'))})(local.set $next (i32.xor (i32.rotl ${g('b')} (i32.const 7)) ${g('a')}))(local.set $a (i32.sub ${expanded} ${mul(g('next'),g('next'))}))(local.set $b ${g('next')})`;
 const wat=`(module (import "env" "observe" (func $observe (param i32 i32)))
 (func (export "run") (param $x i32)(param $y i32)(param $n i32)(param $mask i32)(result i32)
 (local $a i32)(local $b i32)(local $c i32)(local $t i32)(local $next i32)
 ${init}(local.set $n (i32.and ${g('n')} (i32.const 31)))(call $observe ${g('a')} ${g('b')})
 (block $done (loop $again (br_if $done (i32.eqz ${g('n')}))
 (local.set $c (if (result i32) (i32.and ${cond} (i32.const 1))(then (i32.const 3))(else (i32.const 5))))
 ${step}(call $observe ${g('a')} ${g('b')})(local.set $n (i32.sub ${g('n')} (i32.const 1)))(br $again)))
 ${kind==='plain'?g('a'):dec}))`;
 fs.writeFileSync(path.join(dir,kind+'.wat'),wat);
 cp.execFileSync(asm,[path.join(dir,kind+'.wat'),'-o',path.join(dir,kind+'-raw.wasm')]);
 cp.execFileSync(opt,[path.join(dir,kind+'-raw.wasm'),'-O2','-o',path.join(dir,kind+'-O2.wasm')]);
 for(const mode of ['raw','O2']){const file=kind+'-'+mode+'.wasm',b=fs.readFileSync(path.join(dir,file));manifest.push({file,kind,mode,size:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')});}
}
let seed=0x38abcdef;const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const train=Array.from({length:16},()=>[rng(),rng(),0,rng()]);
const inputs=[];for(const x of [0,1,2,0x7fffffff,0x80000000,0xffffffff])for(const n of [0,1,2,31,32,0xffffffff])inputs.push([x,rng(),n,rng()]);
for(let i=0;i<1024;i++)inputs.push([rng(),rng(),rng(),rng()]);
// BigInt specification independently evaluates original scalar computation.
function reference(args){let x=BigInt(args[0]),y=BigInt(args[1]);const states=[Number(x)];for(let i=0;i<(args[2]&31);i++){x=BigInt.asUintN(32,x*x+((x&1n)?3n:5n)*x+y);states.push(Number(x));}return states;}
const results=[];
for(const m of manifest){let trace=[];const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,m.file))),{env:{observe:(a,b)=>trace.push([a>>>0,b>>>0])}});
 let coeff=null,recovery=null;
 if(m.kind==='redundant'){
  const rows=train.map(args=>{trace=[];instance.exports.run(...args);return {input:args[0],state:trace[0]};});
  const tf=path.join(dir,m.file+'.training.json'),rf=path.join(dir,m.file+'.recovery.json');fs.writeFileSync(tf,JSON.stringify(rows,null,2));
  cp.execFileSync(process.execPath,[path.join(__dirname,'recover.cjs'),tf,rf]);recovery=JSON.parse(fs.readFileSync(rf));assert.equal(recovery.matches.length,1);coeff=recovery.matches[0];
 }
 let states=0;const observations=[];
 for(const args of inputs){trace=[];const output=instance.exports.run(...args)>>>0,expected=reference(args);assert.equal(output,expected.at(-1));assert.equal(trace.length,expected.length);
  for(let j=0;j<trace.length;j++){const [a,b]=trace[j];const decoded=coeff?Number(BigInt.asUintN(32,coeff.reduce((s,c,k)=>s+BigInt(c)*[1n,BigInt(a),BigInt(b),BigInt(a)**2n,BigInt(a)*BigInt(b),BigInt(b)**2n][k],0n))):a;assert.equal(decoded,expected[j]);states++;}
  observations.push({args,output,trace});
 }
 fs.writeFileSync(path.join(dir,m.file+'.observations.json'),JSON.stringify(observations));results.push({...m,inputCases:inputs.length,verifiedStates:states,mismatches:0,recovery});
}
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify({seed:'0x38abcdef',train,inputs},null,2));
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,assembler:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),optimizer:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim(),results},null,2));
console.log(JSON.stringify(results.map(({file,inputCases,verifiedStates,recovery})=>({file,inputCases,verifiedStates,coefficients:recovery?.matches,searchMs:recovery?.elapsedMs})),null,2));
