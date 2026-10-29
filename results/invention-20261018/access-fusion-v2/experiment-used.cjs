'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),toolRoot=process.env.WASM_TOOLS_ROOT||path.join(root,'.tools');
const wabt=path.join(toolRoot,'wabt-1.0.42/bin'),opt=path.join(toolRoot,'binaryen-version_133/bin/wasm-opt.exe');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const run=(exe,args)=>cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000});
const emit=n=>Array.isArray(n)?'('+n.map(emit).join(' ')+')':n;
function parse(s){const ts=s.match(/"(?:\\.|[^"\\])*"|;;[^\n]*|\(;[\s\S]*?;\)|[()]|[^\s()]+/g).filter(x=>!x.startsWith('(;')&&!x.startsWith(';;'));let p=0;function expr(){const t=ts[p++];if(t!=='(')return t;const a=[];while(ts[p]!==')'){if(p>=ts.length)throw Error('Unbalanced');a.push(expr());}p++;return a;}const ast=expr();if(p!==ts.length||ast[0]!=='module')throw Error('Not a module');return ast;}
const get=['local.get','0'],shift=['i64.shr_u',get,['i64.const','32']];
const opNames=['xor','add','sub'];
function body(op,mode){
 if(mode==='wide-split')return ['i32.'+op,['i32.wrap_i64',get],['i32.wrap_i64',shift]];
 return ['i32.wrap_i64',['i64.'+op,get,shift]];
}
function loadInfo(n){
 if(!Array.isArray(n)||n[0]!=='i32.load')return null;
 const address=n[n.length-1];
 if(!Array.isArray(address)||address[0]!=='local.get'||address.length!==2)return null;
 let offset=0;
 for(const a of n.slice(1,-1)){if(typeof a!=='string')return null;if(a.startsWith('offset='))offset=Number(a.slice(7));else if(!a.startsWith('align='))return null;}
 if(!Number.isSafeInteger(offset)||offset<0||offset>0xffffffff)return null;
 return {offset,address};
}
function rewrite(input,output,mode){
 if(!['wide-split','wide-fused','recover'].includes(mode))throw Error('Mode');
 if(fs.existsSync(output))throw Error('Refuse overwrite');
 const ast=parse(run(path.join(wabt,'wasm2wat.exe'),[input,'--fold-exprs']));
 if(ast.some(n=>Array.isArray(n)&&n[0]==='import'))throw Error('Imports unsupported');
 const memories=ast.filter(n=>Array.isArray(n)&&n[0]==='memory');
 if(memories.length!==1||memories[0].some(x=>x==='shared'||x==='i64'))throw Error('One unshared memory32 required');
 const funcs=ast.filter(n=>Array.isArray(n)&&n[0]==='func');
 const helpers=new Map(),used=new Set();
 if(mode==='recover')funcs.forEach((f,index)=>{
  const instructions=f.filter(n=>Array.isArray(n)&&!['type','param','result','local','export'].includes(n[0]));
  const params=f.filter(n=>Array.isArray(n)&&n[0]==='param');
  const results=f.filter(n=>Array.isArray(n)&&n[0]==='result');
  if(emit(params)!==emit([['param','i64']])||emit(results)!==emit([['result','i32']])||instructions.length!==1)return;
  for(const op of opNames)for(const m of ['wide-split','wide-fused'])if(emit(instructions[0])===emit(body(op,m)))helpers.set(String(index),op);
 });
 let count=0;
 function visit(n){
  if(!Array.isArray(n))return n;
  if(mode==='recover'&&n[0]==='call'&&helpers.has(n[1])&&n.length===3){
   const wide=n[2];if(Array.isArray(wide)&&wide[0]==='i64.load'){
    const info=loadInfo(['i32.load',...wide.slice(1)]);
    if(info&&info.offset<=0xfffffffb){count++;return ['i32.'+helpers.get(n[1]),['i32.load','offset='+info.offset,info.address],['i32.load','offset='+(info.offset+4),info.address]];}
   }
  }
  if(mode!=='recover'&&n.length===3&&opNames.includes(String(n[0]).slice(4))&&String(n[0]).startsWith('i32.')){
   const a=loadInfo(n[1]),b=loadInfo(n[2]);
   if(a&&b&&b.offset===a.offset+4&&emit(a.address)===emit(b.address)){
    const op=n[0].slice(4);used.add(op);count++;
    return ['call','$access_fusion_'+op,['i64.load','offset='+a.offset,'align=1',a.address]];
   }
  }
  return n.map(visit);
 }
 const rewritten=visit(ast);
 for(const op of used)rewritten.push(['func','$access_fusion_'+op,['param','i64'],['result','i32'],body(op,mode)]);
 fs.writeFileSync(output+'.wat',emit(rewritten)+'\n');run(path.join(wabt,'wat2wasm.exe'),[output+'.wat','-o',output]);run(path.join(wabt,'wasm-validate.exe'),[output]);
 return {mode,count,inputSHA:sha(fs.readFileSync(input)),outputSHA:sha(fs.readFileSync(output))};
}
async function experiment(out){
 if(fs.existsSync(out))throw Error('Refuse overwrite');fs.mkdirSync(out,{recursive:true});
 const plan={date:'2026-10-18',seed:0x7438ac91,gate:'Demand-fused wide loads: validate exact footprint, and attempt static recovery before adopting this as obfuscation.',success:'Widening or fewer scalar intermediates alone is insufficient. Reject the primitive if a binary-only projection recognizer reconstructs source load pairs.',variants:['plain','wide-split','wide-fused'],levels:['raw','O2','O3'],scope:'Two adjacent i32.load operands of i32 xor/add/sub with identical local.get addresses; no imports, shared memory, volatile accesses, or concurrent mutation.'};
 fs.writeFileSync(path.join(out,'plan.json'),JSON.stringify(plan,null,2));
 const programs=[{name:'xor',op:'xor',offset:0},{name:'sum',op:'add',offset:4},{name:'difference',op:'sub',offset:1},{name:'overflow-offset',op:'xor',offset:0xfffffff8}];
 const results={sourceSHA:sha(fs.readFileSync(__filename)),planSHA:sha(fs.readFileSync(path.join(out,'plan.json'))),node:process.version,v8:process.versions.v8,wabt:run(path.join(wabt,'wat2wasm.exe'),['--version']).trim(),binaryen:run(opt,['--version']).trim(),rows:[],recovery:[]};
 let s=plan.seed;const rand=()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return s>>>0;};
 const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=rand()&255;fs.writeFileSync(path.join(out,'initial.bin'),initial);
 for(const prog of programs){
  const prefix=path.join(out,prog.name),base=prefix+'-plain.wasm';
  const wat=`(module (memory (export "memory") 1 1) (func (export "run") (param i32) (result i32) (i32.store (i32.const 32) (local.get 0)) (i32.${prog.op} (i32.load offset=${prog.offset} (local.get 0)) (i32.load offset=${prog.offset+4} (local.get 0)))))`;
  fs.writeFileSync(base+'.wat',wat);run(path.join(wabt,'wat2wasm.exe'),[base+'.wat','-o',base]);
  const variants=[];
  for(const mode of plan.variants){
   const src=prefix+'-'+mode+'.wasm';let transformation=null;
   if(mode!=='plain'){const start=performance.now();transformation=rewrite(base,src,mode);transformation.ms=performance.now()-start;}
   for(const level of plan.levels){const file=prefix+'-'+mode+'-'+level+'.wasm';if(level==='raw')fs.copyFileSync(src,file);else run(opt,[src,'-'+level,'-o',file]);variants.push({mode,level,file,transformation});}
  }
  const inputs=[0,1,3,4,24,25,28,31,32,33,65520,65524,65527,65528,65529,65530,65531,65532,65535,65536,0x7fffffff,0xfffffff8,0xffffffff];
  for(let i=0;i<512;i++)inputs.push(rand()%65536);for(let i=0;i<512;i++)inputs.push(rand());
  fs.writeFileSync(prefix+'-inputs.json',JSON.stringify(inputs));
  const ref=(await WebAssembly.instantiate(fs.readFileSync(base))).instance.exports;
  function observe(e,x){new Uint8Array(e.memory.buffer).set(initial);let value=null,trap=null;try{value=e.run(x);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=err.message;}return {value,trap,memory:Buffer.from(new Uint8Array(e.memory.buffer))};}
  const expected=inputs.map(x=>observe(ref,x));
  for(const mode of ['wide-split','wide-fused']){
   const file=prefix+'-'+mode+'-recovered.wasm';const rec=rewrite(prefix+'-'+mode+'-raw.wasm',file,'recover');results.recovery.push({program:prog.name,...rec});variants.push({mode:mode+'-recovered',level:'raw',file});
  }
  for(const v of variants){
   const bytes=fs.readFileSync(v.file);run(path.join(wabt,'wasm-validate.exe'),[v.file]);const e=(await WebAssembly.instantiate(bytes)).instance.exports;
   let mismatches=0,traps=0;const witnesses=[];
   for(let i=0;i<inputs.length;i++){const a=observe(e,inputs[i]),b=expected[i];if(a.trap)traps++;if(a.value!==b.value||a.trap!==b.trap||!a.memory.equals(b.memory)){mismatches++;if(witnesses.length<4)witnesses.push({input:inputs[i],got:{value:a.value,trap:a.trap,memory:sha(a.memory)},expected:{value:b.value,trap:b.trap,memory:sha(b.memory)}});}}
   const dis=run(path.join(wabt,'wasm2wat.exe'),[v.file,'--fold-exprs']);fs.writeFileSync(v.file+'.dis.wat',dis);
   results.rows.push({program:prog.name,mode:v.mode,level:v.level,bytes:bytes.length,sha:sha(bytes),validation:'pass',comparisons:inputs.length,traps,mismatches,witnesses,linearMemoryBytes:e.memory.buffer.byteLength,load32:(dis.match(/i32\.load\b/g)||[]).length,load64:(dis.match(/i64\.load\b/g)||[]).length,transformation:v.transformation||null});
  }
 }
 results.comparisons=results.rows.reduce((n,r)=>n+r.comparisons,0);results.mismatches=results.rows.reduce((n,r)=>n+r.mismatches,0);
 results.limitations=['No NotDec or StackSight execution; no resilience claim against either.','Adaptive recovery implemented only for raw helper form.','No performance or process-memory benchmark in this feasibility gate.','Access cover selection and whole-region consumer fusion are not implemented.'];
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({out,comparisons:results.comparisons,mismatches:results.mismatches,recovery:results.recovery},null,2));if(results.mismatches)process.exitCode=1;
}
if(require.main===module){const [cmd,...args]=process.argv.slice(2);if(cmd==='transform'){if(args.length!==3)throw Error('transform input output wide-split|wide-fused|recover');console.log(JSON.stringify(rewrite(...args)));}else if(cmd==='experiment'){if(args.length!==1)throw Error('experiment fresh-output-directory');experiment(path.resolve(args[0])).catch(e=>{console.error(e);process.exitCode=1;});}else throw Error('Unknown command');}
