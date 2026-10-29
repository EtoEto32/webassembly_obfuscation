'use strict';
// A falsification gate, not a claim of a novel obfuscator.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),os=require('node:os');
const root=path.resolve(__dirname,'../..');
const tools=process.env.WASM_TOOLS_ROOT||path.join(root,'.tools');
const wabt=path.join(tools,'wabt-1.0.42/bin');
const opt=path.join(tools,'binaryen-version_133/bin/wasm-opt.exe');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const run=(exe,args)=>cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000});
// Parsing WABT-generated text only. String tokens and comments are handled;
// arbitrary source WAT is deliberately not accepted by the CLI.
function parse(s){
 const tok=s.match(/"(?:\\.|[^"\\])*"|;;[^\n]*|\(;[\s\S]*?;\)|[()]|[^\s()]+/g).filter(t=>!t.startsWith(';;')&&!t.startsWith('(;'));
 let p=0;
 function one(){const t=tok[p++];if(t!=='(')return t;const a=[];while(tok[p]!==')'){if(p>=tok.length)throw Error('Unbalanced WAT');a.push(one());}p++;return a;}
 const ast=one();if(p!==tok.length||ast[0]!=='module')throw Error('Expected single module');return ast;
}
const print=x=>Array.isArray(x)?'('+x.map(print).join(' ')+')':x;
// t = x*(x+1) has even parity in Z/(2^32). The load at 65535+t%2
// is consequently in bounds in every memory with at least one page.
const parity=['i32.and',['i32.mul',['local.get','0'],['i32.add',['local.get','0'],['i32.const','1']]],['i32.const','1']];
const carrier=()=>['drop',['i32.load8_u',['i32.add',['i32.const','65535'],parity]]];
const pure=()=>['drop',parity];
function canonical(x){
 if(!Array.isArray(x))return x;
 const n=x.map(canonical);
 if(['i32.add','i32.mul','i32.and'].includes(n[0])&&n.length===3&&print(n[1])>print(n[2]))[n[1],n[2]]=[n[2],n[1]];
 return n;
}
function transform(input,output,mode){
 if(!['trap','pure','recover'].includes(mode))throw Error('Invalid mode');
 if(fs.existsSync(output))throw Error('Refuse overwrite '+output);
 run(path.join(wabt,'wasm-validate.exe'),[input]);
 const ast=parse(run(path.join(wabt,'wasm2wat.exe'),[input,'--fold-exprs']));
 if(ast.some(n=>Array.isArray(n)&&n[0]==='import'))throw Error('Imports unsupported');
 const mem=ast.filter(n=>Array.isArray(n)&&n[0]==='memory');
 if(mem.length!==1||mem[0].some(t=>t==='shared'||t==='i64')||!/^\d+$/.test(mem[0][1])||Number(mem[0][1])<1)throw Error('Requires one unshared memory32 of at least one page');
 let count=0;
 for(const f of ast.filter(n=>Array.isArray(n)&&n[0]==='func')){
  if(mode==='recover'){
   // Pattern recognition on unnamed binary disassembly; no transformation map.
   for(let i=f.length-1;i>=1;i--)if(print(canonical(f[i]))===print(canonical(carrier()))){f.splice(i,1);count++;}
  }else{
   const param=f.find(n=>Array.isArray(n)&&n[0]==='param');
   if(!param||param[1]!=='i32')continue;
   let at=1;while(at<f.length&&((typeof f[at]==='string'&&f[at].startsWith('$'))||(Array.isArray(f[at])&&['type','param','result','local','export'].includes(f[at][0]))))at++;
   f.splice(at,0,mode==='trap'?carrier():pure());count++;
  }
 }
 const wat=output+'.wat';fs.writeFileSync(wat,print(ast)+'\n');
 run(path.join(wabt,'wat2wasm.exe'),[wat,'-o',output]);run(path.join(wabt,'wasm-validate.exe'),[output]);
 return {count,inputSHA256:hash(fs.readFileSync(input)),outputSHA256:hash(fs.readFileSync(output))};
}
async function experiment(out){
 if(fs.existsSync(out))throw Error('Refuse overwrite '+out);fs.mkdirSync(out,{recursive:true});
 const plan={hypothesis:'A trap-sensitive unused load preserves an opaque arithmetic carrier under O2/O3, but its protection must survive an adaptive parity proof.',seed:0x59e271ab,randomInputs:4096,warmup:2000,trials:9,callsPerTrial:20000,scope:'MVP integer functions, one unshared memory32; no imports; finite regression, not equivalence proof',success:'Retaining a load alone is not success. If parity recognition removes the carrier with preserved behavior, reject this mechanism as protection.'};
 fs.writeFileSync(path.join(out,'plan.json'),JSON.stringify(plan,null,2));
 const benchmarks={
  arx:'(i32.xor (i32.rotl (local.get 0) (i32.const 7)) (i32.mul (local.get 0) (i32.const 2654435761)))',
  division:'(i32.div_s (i32.const -2147483648) (local.get 0))',
  memory:'(i32.store (i32.const 16) (local.get 0)) (i32.load (local.get 0))'
 };
 const inputs=[0,1,2,3,65532,65533,65535,65536,0x7fffffff,0x80000000,0xffffffff];
 let s=plan.seed;for(let i=0;i<plan.randomInputs;i++){s^=s<<13;s^=s>>>17;s^=s<<5;inputs.push(s>>>0);}
 fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs));
 const summary={planSHA256:hash(fs.readFileSync(path.join(out,'plan.json'))),sourceSHA256:hash(fs.readFileSync(__filename)),environment:{node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,platform:process.platform,wabt:run(path.join(wabt,'wat2wasm.exe'),['--version']).trim(),binaryen:run(opt,['--version']).trim()},rows:[]};
 for(const [bench,body]of Object.entries(benchmarks)){
  const base=path.join(out,bench+'-plain.wasm');fs.writeFileSync(base+'.wat',`(module (memory (export "memory") 1 1) (func (export "run") (param i32) (result i32) ${body}))`);run(path.join(wabt,'wat2wasm.exe'),[base+'.wat','-o',base]);
  const transforms={};for(const mode of ['pure','trap']){const t=performance.now();transforms[mode]=transform(base,path.join(out,bench+'-'+mode+'.wasm'),mode);transforms[mode].ms=performance.now()-t;}
  const variants=[];
  for(const mode of ['plain','pure','trap'])for(const level of ['raw','O2','O3']){
   const src=path.join(out,bench+'-'+mode+'.wasm'),file=path.join(out,bench+'-'+mode+'-'+level+'.wasm');
   if(level==='raw')fs.copyFileSync(src,file);else run(opt,[src,'-'+level,'-o',file]);
   variants.push({mode,level,file});
  }
  for(const level of ['raw','O2','O3']){
   const recovered=path.join(out,bench+'-recovered-'+level+'.wasm');const t=performance.now();const recovery=transform(path.join(out,bench+'-trap-'+level+'.wasm'),recovered,'recover');recovery.ms=performance.now()-t;
   variants.push({mode:'recovered',level,file:recovered,recovery});
  }
  const ref=(await WebAssembly.instantiate(fs.readFileSync(base))).instance.exports;
  function observe(e,x){new Uint8Array(e.memory.buffer).fill(0);let value=null,trap=null;try{value=e.run(x);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=err.message;}return {value,trap,memory:hash(Buffer.from(e.memory.buffer))};}
  const expected=inputs.map(x=>observe(ref,x));
  fs.writeFileSync(path.join(out,bench+'-expected.json'),JSON.stringify(expected));
  for(const v of variants){
   const bytes=fs.readFileSync(v.file);run(path.join(wabt,'wasm-validate.exe'),[v.file]);const e=(await WebAssembly.instantiate(bytes)).instance.exports;
   let mismatches=0,traps=0;const first=[];
   inputs.forEach((x,i)=>{const got=observe(e,x);if(got.trap)traps++;if(JSON.stringify(got)!==JSON.stringify(expected[i])){mismatches++;if(first.length<5)first.push({x,got,expected:expected[i]});}});
   const wat=run(path.join(wabt,'wasm2wat.exe'),[v.file,'--fold-exprs']);fs.writeFileSync(v.file+'.dis.wat',wat);
   const row={benchmark:bench,mode:v.mode,level:v.level,bytes:bytes.length,sha256:hash(bytes),validation:'passed',comparisons:inputs.length,mismatches,traps,first,load8Count:(wat.match(/i32\.load8_u/g)||[]).length,linearMemoryBytes:e.memory.buffer.byteLength,transform:transforms[v.mode]||null,recovery:v.recovery||null};
   // Normal inputs only for timing; trap-path correctness is tested above.
   const safe=bench==='division'?3:bench==='memory'?32:0x13579bdf;
   for(let i=0;i<plan.warmup;i++)e.run(safe);
   row.nsPerCall=[];let checksum=0;
   for(let j=0;j<plan.trials;j++){const start=performance.now();for(let i=0;i<plan.callsPerTrial;i++)checksum^=e.run(safe);row.nsPerCall.push((performance.now()-start)*1e6/plan.callsPerTrial);}
   row.checksum=checksum;row.medianNs=[...row.nsPerCall].sort((a,b)=>a-b)[4];summary.rows.push(row);
  }
 }
 summary.totalComparisons=summary.rows.reduce((n,r)=>n+r.comparisons,0);summary.mismatches=summary.rows.reduce((n,r)=>n+r.mismatches,0);
 // A near-match that CAN trap must never be stripped by the recognizer.
 const control=path.join(out,'negative-control.wasm');
 const bad=carrier();bad[1][1][2]=['i32.and',['local.get','0'],['i32.const','1']];
 fs.writeFileSync(control+'.wat',`(module (memory 1 1) (func (export "run") (param i32) (result i32) ${print(bad)} (local.get 0)))`);
 run(path.join(wabt,'wat2wasm.exe'),[control+'.wat','-o',control]);
 const controlOut=path.join(out,'negative-control-recovered.wasm');const cr=transform(control,controlOut,'recover');
 const ce=(await WebAssembly.instantiate(fs.readFileSync(controlOut))).instance.exports;
 let controlTraps=false;try{ce.run(1);}catch(e){controlTraps=e instanceof WebAssembly.RuntimeError;}
 summary.negativeControl={removed:cr.count,trapPreserved:controlTraps};
 if(cr.count!==0||!controlTraps)throw Error('Unsound recovery control');
 summary.limitations=['Single runtime; exact same-runtime trap messages checked, not cross-engine message equivalence.','Timing is a sequential microbenchmark including JS/Wasm boundary; no balanced ordering or CPU isolation.','Linear memory measured; process peak RSS and runtime stack not measured.','Recovery supports this identity and commutative operand permutations, not arbitrary opaque expressions.','Not a novel algorithm claim; complete evaluation and other candidates remain open.'];
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(summary,null,2));
 console.log(JSON.stringify({out,totalComparisons:summary.totalComparisons,mismatches:summary.mismatches,rows:summary.rows.map(({benchmark,mode,level,bytes,load8Count,medianNs})=>({benchmark,mode,level,bytes,load8Count,medianNs}))},null,2));
 if(summary.mismatches)process.exitCode=1;
}
if(require.main===module){const [command,...args]=process.argv.slice(2);if(command==='transform'){if(args.length!==3)throw Error('transform input.wasm output.wasm trap|pure|recover');console.log(JSON.stringify(transform(...args)));}else if(command==='experiment'){if(args.length!==1)throw Error('experiment fresh-output-dir');experiment(path.resolve(args[0])).catch(e=>{console.error(e);process.exitCode=1;});}else throw Error('Use transform or experiment');}
