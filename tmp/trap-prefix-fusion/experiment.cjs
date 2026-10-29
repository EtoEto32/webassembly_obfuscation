'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const dir=path.join(__dirname,'artifacts-v2');fs.mkdirSync(dir,{recursive:true});
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe'),opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const c=n=>`(i32.const ${n>>>0})`,g=n=>`(local.get $${n})`,op=(name,a,b)=>`(i32.${name} ${a} ${b})`,get=v=>typeof v==='number'?c(v):g(v),set=(n,v)=>`(local.set $${n} ${v})`;
const and=(a,b)=>op('and',a,b),not=a=>`(i32.eqz ${a})`,valid=a=>op('le_u',a,c(65532));
const params=['a','b','d','x','y','e'];
const raiseHelper=`
 (func $raise (param $kind i32)(param $arg i32)
  (if (i32.eq (local.get $kind) (i32.const 1))
   (then (drop (i32.div_u (i32.const 1) (local.get $arg))))
   (else (drop (i32.load (local.get $arg))))))`;
const forwardHelper=`
 (func $forward (param $r i32)(param $la i32)(param $sa i32)(param $sv i32)(param $enabled i32)(result i32)
  (local $delta i32)
  ${[0,1,2,3].map(j=>`
   ${set('delta',op('sub',op('add',g('la'),c(j)),g('sa')))}
   (if ${and(g('enabled'),op('lt_u',g('delta'),c(4)))} (then
    ${set('r',op('or',and(g('r'),c(~(255<<(8*j)))),op('shl',and(op('shr_u',g('sv'),op('mul',g('delta'),c(8))),c(255)),c(8*j))))}))`).join('')}
  ${g('r')})`;
function compile(program,kind){
 const deferred=kind.startsWith('deferred'),coalesced=kind==='deferred-coalesced',decl=new Set(['fault','faultArg']);
 const defined=new Set(params),body=[],stores=[];
 const check=(good,type,arg)=>deferred?`(if ${and(not(g('fault')),not(good))} (then ${set('fault',c(type))}${set('faultArg',arg)}))`:(kind==='guarded'?`(if ${not(good)} (then (call $raise ${c(type)} ${arg})))`:'');
 for(const ins of program.ops){
  for(const value of (ins.args||[]))if(typeof value==='string')assert(defined.has(value),`Undefined IR ref ${value}`);
  if(ins.out){assert(!defined.has(ins.out));defined.add(ins.out);decl.add(ins.out);}
  const args=(ins.args||[]).map(get);
  if(['add','mul','xor'].includes(ins.op))body.push(set(ins.out,op(ins.op,...args)));
  else if(ins.op==='div'){
   body.push(check(not(`(i32.eqz ${args[1]})`),1,args[1]));
   body.push(set(ins.out,op('div_u',args[0],deferred?`(select ${args[1]} ${c(1)} ${not(`(i32.eqz ${args[1]})`)})`:args[1])));
  }else if(ins.op==='store'){
   body.push(check(valid(args[0]),2,args[0]));
   if(!deferred)body.push(`(i32.store ${args[0]} ${args[1]})`);
   else{
    const id=stores.length,s={addr:`sa${id}`,value:`sv${id}`,enabled:`se${id}`};Object.values(s).forEach(v=>decl.add(v));
    body.push(set(s.addr,args[0]),set(s.value,args[1]),set(s.enabled,not(g('fault'))));stores.push(s);
   }
  }else if(ins.op==='load'){
   body.push(check(valid(args[0]),2,args[0]));
   body.push(set(ins.out,deferred?`(if (result i32) ${valid(args[0])} (then (i32.load ${args[0]})) (else ${c(0)}))`:`(i32.load ${args[0]})`));
   if(deferred)for(const s of stores)body.push(set(ins.out,`(call $forward ${g(ins.out)} ${args[0]} ${g(s.addr)} ${g(s.value)} ${g(s.enabled)})`));
  }else throw Error('Unsupported IR op '+ins.op);
 }
 assert(defined.has(program.result));
 if(deferred){
  if(!coalesced)for(const s of stores)body.push(`(if ${g(s.enabled)} (then (i32.store ${g(s.addr)} ${g(s.value)})))`);
  else for(let i=stores.length-1;i>=0;i--)for(let j=3;j>=0;j--){
   const s=stores[i],addr=op('add',g(s.addr),c(j));let enabled=g(s.enabled);
   for(let k=i+1;k<stores.length;k++)enabled=and(enabled,not(and(g(stores[k].enabled),op('lt_u',op('sub',addr,g(stores[k].addr)),c(4)))));
   body.push(`(if ${enabled} (then (i32.store8 ${addr} ${op('shr_u',g(s.value),c(8*j))})))`);
  }
  body.push(`(if ${g('fault')} (then (call $raise ${g('fault')} ${g('faultArg')})))`);
 }
 return `(module (memory (export "memory") 1 1) ${kind!=='native'?raiseHelper:''} ${deferred?forwardHelper:''}
  (func (export "run") ${params.map(p=>`(param $${p} i32)`).join('')} (result i32)
  ${[...decl].map(v=>`(local $${v} i32)`).join('')}
  ${body.join('\n')} ${g(program.result)}))`;
}
const I=(op,out,...args)=>({op,...(out?{out}:{}),args});
const programs=[
 {name:'prefix-div',ops:[I('store',null,'a','x'),I('load','v','b'),I('div','q','v','d'),I('store',null,'b','q'),I('load','r','a'),I('xor','o','r','y')],result:'o'},
 {name:'partial-alias',ops:[I('store',null,'a','x'),I('store',null,'b','y'),I('add','p','a',1),I('load','v','p'),I('div','q','v','d'),I('add','p2','a',2),I('store',null,'p2','q'),I('load','o','b')],result:'o'},
 {name:'forwarded-divisor',ops:[I('store',null,'a','x'),I('load','v','b'),I('div','q','y','v'),I('store',null,'b','q'),I('load','o','a')],result:'o'},
 {name:'first-fault',ops:[I('div','q','x','d'),I('store',null,'a','q'),I('load','v','b'),I('div','q2','v','e'),I('store',null,'b','q2'),I('load','o','a')],result:'o'},
 {name:'forwarded-address',ops:[I('store',null,'a','x'),I('load','p','b'),I('store',null,'p','y'),I('load','v','p'),I('div','q','v','d'),I('store',null,'b','q'),I('load','o','a')],result:'o'}
];
let seed=0x3189defa;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
for(let i=0;i<8;i++)programs.push({name:'generated-'+i,ops:[I('mul','s','x',rng()|1),I('store',null,'a','s'),I('add','p','b',i%4),I('load','v','p'),I('xor','w','v','y'),I('div','q','w','d'),I('store',null,'b','q'),I('load','r','a'),I('mul','r2','r','q'),I('div','r3','r2','e'),I('store',null,'p','r3'),I('load','o','b')],result:'o'});
const cases=[];
const pairs=[[0,0],[0,1],[1,0],[1,2],[2,1],[65532,65532],[65532,65533],[65533,0],[0,65533],[0xffffffff,0],[0,0xffffffff],[65529,65531]];
for(const [a,b]of pairs)for(const d of [0,1,3,0xffffffff])for(const x of [0,0xffffffff])cases.push([a,b,d,x,rng(),d===0?1:0]);
for(let i=0;i<128;i++){const a=rng()%65536,b=(a+(rng()%9)-4)>>>0;cases.push([a,b,rng()%5,rng(),rng(),rng()%7]);}
const base=Buffer.alloc(65536);for(let i=0;i<base.length;i++)base[i]=(i*73+(i>>>8)*19+23)&255;
function interpret(program,input){
 const mem=Buffer.from(base),view=new DataView(mem.buffer,mem.byteOffset,mem.byteLength),regs=Object.fromEntries(params.map((p,i)=>[p,BigInt(input[i])])),val=x=>typeof x==='number'?BigInt(x>>>0):regs[x];
 let trap=null,faultIndex=null;
 for(let index=0;index<program.ops.length;index++){
  const ins=program.ops[index],args=ins.args.map(val);let result;
  if((ins.op==='load'||ins.op==='store')&&args[0]+4n>65536n){trap='memory';faultIndex=index;break;}
  if(ins.op==='div'&&args[1]===0n){trap='divide';faultIndex=index;break;}
  switch(ins.op){
   case'add':result=args[0]+args[1];break;
   case'mul':result=args[0]*args[1];break;
   case'xor':result=args[0]^args[1];break;
   case'div':result=args[0]/args[1];break;
   case'load':result=BigInt(view.getUint32(Number(args[0]),true));break;
   case'store':view.setUint32(Number(args[0]),Number(args[1]),true);break;
   default:throw Error('Unknown op');
  }
  if(ins.out)regs[ins.out]=BigInt.asUintN(32,result);
 }
 return {trap,faultIndex,output:trap?null:Number(regs[program.result]),mem};
}
const kinds=['native','guarded','deferred-ordered','deferred-coalesced'],results=[],observations=[];
for(const program of programs){
 const expected=cases.map(input=>interpret(program,input));
 const expectedRows=expected.map((e,index)=>({case:index,output:e.output,trap:e.trap,faultIndex:e.faultIndex,memorySha256:hash(e.mem)}));
 fs.writeFileSync(path.join(dir,program.name+'.expected.json'),JSON.stringify(expectedRows,null,2));
 for(const kind of kinds){
  const stem=program.name+'-'+kind,wat=compile(program,kind);fs.writeFileSync(path.join(dir,stem+'.wat'),wat);
  cp.execFileSync(asm,[path.join(dir,stem+'.wat'),'-o',path.join(dir,stem+'-raw.wasm')]);
  cp.execFileSync(opt,[path.join(dir,stem+'-raw.wasm'),'-O2','-o',path.join(dir,stem+'-O2.wasm')]);
  for(const mode of ['raw','O2']){
   const file=stem+'-'+mode+'.wasm',buf=fs.readFileSync(path.join(dir,file)),instance=new WebAssembly.Instance(new WebAssembly.Module(buf)),mem=Buffer.from(instance.exports.memory.buffer);let trapCases=0;
   const seen=[];
   for(let j=0;j<cases.length;j++){
    base.copy(mem);let output=null,trap=null;
    try{output=instance.exports.run(...cases[j])>>>0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;if(/divide by zero/.test(err.message))trap='divide';else if(/memory access out of bounds/.test(err.message))trap='memory';else throw err;}
    const exp=expected[j],actual={case:j,output,trap,memorySha256:hash(mem)};seen.push(actual);
    if(trap)trapCases++;
    if(output!==exp.output||trap!==exp.trap||!mem.equals(exp.mem)){
     fs.writeFileSync(path.join(dir,'failure.json'),JSON.stringify({file,input:cases[j],actual,expected:expectedRows[j]},null,2));throw Error('Mismatch '+file+' case '+j);
    }
   }
   fs.writeFileSync(path.join(dir,file+'.observations.json'),JSON.stringify(seen));
   results.push({file,program:program.name,kind,mode,bytes:buf.length,sha256:hash(buf),cases:cases.length,trapCases,normalCases:cases.length-trapCases,mismatches:0,fullMemoryComparedBytes:65536});
  }
 }
}
fs.writeFileSync(path.join(dir,'programs.json'),JSON.stringify(programs,null,2));
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify({seed:'0x3189defa',params,cases},null,2));fs.writeFileSync(path.join(dir,'initial-memory.bin'),base);
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,assembler:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),optimizer:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim(),initialMemorySha256:hash(base),results},null,2));
console.log(JSON.stringify({programs:programs.length,binaries:results.length,casesPerBinary:cases.length,executions:results.reduce((s,r)=>s+r.cases,0),traps:results.reduce((s,r)=>s+r.trapCases,0),mismatches:0,byProgram:results.filter(r=>r.kind==='native'&&r.mode==='raw').map(({program,normalCases,trapCases})=>({program,normalCases,trapCases}))},null,2));
