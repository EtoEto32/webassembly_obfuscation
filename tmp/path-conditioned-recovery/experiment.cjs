'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict'),os=require('node:os');
const dir=path.join(__dirname,'artifacts');fs.mkdirSync(dir,{recursive:true});
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe'),opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe'),dump=path.join(root,'wabt-1.0.42/bin/wasm-objdump.exe');
const g=n=>`(local.get $${n})`,cn=n=>`(i32.const ${n})`,op=(name,a,b)=>`(i32.${name} ${a} ${b})`,add=(a,b)=>op('add',a,b),mul=(a,b)=>op('mul',a,b),sub=(a,b)=>op('sub',a,b);
const kinds=['plain','dynamic-linear','dynamic-quadratic','fixed-quadratic'];
const manifest=[];
for(const kind of kinds)for(const instrumented of [false,true]){
 const isPlain=kind==='plain',dynamic=kind.startsWith('dynamic'),quadratic=kind.endsWith('quadratic');
 const term=(b,h)=>{const t=quadratic?mul(b,b):b;return dynamic?`(if (result i32) ${h} (then ${sub(cn(0),t)}) (else ${t}))`:t;};
 const observe=instrumented?`(call $observe ${g('a')} ${g('b')} ${g('h')})`:'';
 const init=isPlain?`(local.set $a ${g('x')})`:`(local.set $b ${g('mask')})${dynamic?`(local.set $h (i32.and ${g('mask')} ${cn(1)}))`:''}(local.set $a ${sub(g('x'),term(g('b'),g('h')))})`;
 const parity=isPlain?g('a'):add(g('a'),g('b'));
 const expanded=add(add(add(add(mul(g('a'),g('a')),mul(cn(2),mul(g('a'),g('t')))),mul(g('t'),g('t'))),mul(g('c'),add(g('a'),g('t')))),g('y'));
 const step=isPlain?`(local.set $a ${add(add(mul(g('a'),g('a')),mul(g('c'),g('a'))),g('y'))})`:`(local.set $t ${term(g('b'),g('h'))})(local.set $next (i32.xor (i32.rotl ${g('b')} ${cn(7)}) ${g('a')}))${dynamic?`(local.set $h (i32.xor ${g('h')} ${g('p')}))`:''}(local.set $a ${sub(expanded,term(g('next'),g('h')))})(local.set $b ${g('next')})`;
 const wat=`(module ${instrumented?'(import "env" "observe" (func $observe (param i32 i32 i32)))':''}
 (func (export "run") (param $x i32)(param $y i32)(param $n i32)(param $mask i32)(result i32)
 (local $a i32)(local $b i32)(local $h i32)(local $p i32)(local $c i32)(local $t i32)(local $next i32)
 ${init}(local.set $n (i32.and ${g('n')} ${cn(31)}))${observe}
 (block $done (loop $again (br_if $done (i32.eqz ${g('n')}))
 (local.set $p (i32.and ${parity} ${cn(1)}))
 (local.set $c (if (result i32) ${g('p')} (then ${cn(3)}) (else ${cn(5)})))
 ${step}${observe}(local.set $n ${sub(g('n'),cn(1))})(br $again)))
 ${isPlain?g('a'):add(g('a'),term(g('b'),g('h')))}))`;
 const stem=kind+(instrumented?'-observed':'-release');fs.writeFileSync(path.join(dir,stem+'.wat'),wat);
 cp.execFileSync(asm,[path.join(dir,stem+'.wat'),'-o',path.join(dir,stem+'-raw.wasm')]);
 cp.execFileSync(opt,[path.join(dir,stem+'-raw.wasm'),'-O2','-o',path.join(dir,stem+'-O2.wasm')]);
 for(const mode of ['raw','O2']){
  const file=stem+'-'+mode+'.wasm',buf=fs.readFileSync(path.join(dir,file));
  const dis=cp.execFileSync(dump,['-d',path.join(dir,file)],{encoding:'utf8'});fs.writeFileSync(path.join(dir,file+'.disassembly.txt'),dis);
  manifest.push({kind,instrumented,mode,file,size:buf.length,instructionCount:dis.split(/\r?\n/).filter(l=>/^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2} )+\s*\|/.test(l)&&!l.includes('| local[')).length,sha256:crypto.createHash('sha256').update(buf).digest('hex')});
 }
}
let seed=0x741ac382;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const training=Array.from({length:32},(_,i)=>[rng(),rng(),0,((rng()&0xfffffffe)|(i&1))>>>0]);
const inputs=[];for(const x of [0,1,2,0x7fffffff,0x80000000,0xffffffff])for(const n of [0,1,2,31,32,0xffffffff])for(const mask of [0,1,0xffffffff])inputs.push([x,rng(),n,mask]);
for(let i=0;i<1024;i++)inputs.push([rng(),rng(),rng(),rng()]);
function reference(args){let x=BigInt(args[0]),y=BigInt(args[1]);const result=[Number(x)];for(let i=0;i<(args[2]&31);i++){x=BigInt.asUintN(32,x*x+((x&1n)?3n:5n)*x+y);result.push(Number(x));}return result;}
function specDecode(kind,state){const [a,b,h]=state.map(BigInt);if(kind==='plain')return Number(a);let t=kind.endsWith('quadratic')?b*b:b;if(kind.startsWith('dynamic')&&h)t=-t;return Number(BigInt.asUintN(32,a+t));}
function poly(c,state){const [a,b]=state.map(BigInt);return Number(BigInt.asUintN(32,c.reduce((s,v,i)=>s+BigInt(v)*[1n,a,b,a*a,a*b,b*b][i],0n)));}
const results=[],releases=[];
for(const m of manifest){
 let trace=[];const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,m.file))),m.instrumented?{env:{observe:(a,b,h)=>trace.push([a>>>0,b>>>0,h>>>0])}}:{});
 let recovery=null,decoder=null;
 if(m.instrumented&&m.kind!=='plain'){
  const rows=training.map(args=>{trace=[];instance.exports.run(...args);return {input:args[0],state:trace[0]};});
  const tf=path.join(dir,m.file+'.training.json'),rf=path.join(dir,m.file+'.recovery.json');fs.writeFileSync(tf,JSON.stringify(rows,null,2));
  cp.execFileSync(process.execPath,[path.join(__dirname,'recover.cjs'),tf,rf]);recovery=JSON.parse(fs.readFileSync(rf));
  if(recovery.fixed.length===1)decoder=s=>poly(recovery.fixed[0],s.slice(0,2));
  else {const split=recovery.partitions.find(p=>p.unique);if(split)decoder=s=>poly(split.groups.find(g=>g.value===s[split.axis]).matches[0],split.indices.map(i=>s[i]));}
 }
 let states=0,recovered=0,switches=0;const observations=[];
 for(const args of inputs){
  trace=[];const output=instance.exports.run(...args)>>>0,expected=reference(args);assert.equal(output,expected.at(-1));
  if(m.instrumented){assert.equal(trace.length,expected.length);for(let j=0;j<trace.length;j++){assert.equal(specDecode(m.kind,trace[j]),expected[j]);states++;if(j&&trace[j][2]!==trace[j-1][2])switches++;if(decoder){assert.equal(decoder(trace[j]),expected[j]);recovered++;}}}
  observations.push({args,output,...(m.instrumented?{trace}:{})});
 }
 fs.writeFileSync(path.join(dir,m.file+'.observations.json'),JSON.stringify(observations));results.push({...m,inputCases:inputs.length,verifiedStates:states,recoveredStates:recovered,phaseSwitches:switches,mismatches:0,recovery});
 if(!m.instrumented)releases.push({m,run:instance.exports.run});
}
// Release-only repeated timings. Includes equal JS/Wasm call overhead in all cases.
const calls=131072,rounds=7;let sink=0;
function batch(run,count){let checksum=0;for(let i=0;i<count;i++)checksum=(checksum+(run((Math.imul(i,2654435761)^0x76543210)>>>0,0x9e3779b9,15+(i&1),i)>>>0))>>>0;return checksum;}
for(const r of releases)sink^=batch(r.run,32768);
const expectedChecksum=batch(releases.find(r=>r.m.kind==='plain'&&r.m.mode==='raw').run,calls),timings=[];
for(let round=0;round<rounds;round++){
 const order=releases.slice();for(let i=order.length-1;i>0;i--){const j=rng()%(i+1);[order[i],order[j]]=[order[j],order[i]];}
 for(const r of order){const start=performance.now(),checksum=batch(r.run,calls),ms=performance.now()-start;assert.equal(checksum,expectedChecksum);sink^=checksum;timings.push({round,file:r.m.file,ms,calls,checksum});}
}
const stats=releases.map(r=>{const v=timings.filter(t=>t.file===r.m.file).map(t=>t.ms).sort((a,b)=>a-b);return {file:r.m.file,kind:r.m.kind,mode:r.m.mode,minMs:v[0],medianMs:v[3],maxMs:v[6]};});
for(const s of stats)s.ratioToPlain=s.medianMs/stats.find(t=>t.kind==='plain'&&t.mode===s.mode).medianMs;
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify({seed:'0x741ac382',training,inputs},null,2));
fs.writeFileSync(path.join(dir,'timings.json'),JSON.stringify({calls,rounds,expectedChecksum,sink,timings,stats},null,2));
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model,assembler:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),optimizer:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim(),results},null,2));
console.log(JSON.stringify({results:results.map(({file,size,instructionCount,inputCases,verifiedStates,recoveredStates,phaseSwitches,recovery})=>({file,size,instructionCount,inputCases,verifiedStates,recoveredStates,phaseSwitches,fixedMatches:recovery?.fixed.length,partitions:recovery?.partitions})),stats},null,2));
