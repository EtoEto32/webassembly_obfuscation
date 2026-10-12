'use strict';
// Provisional compiler experiment, not a claim of established novelty.
// Original SHA WAT derives from sha.js 2.4.11; see ../sha256-research-baseline/vendor/LICENSE.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(path.join(__dirname,'../sha256-research-baseline/artifacts/plain.wat'));
assert.equal(sha(bytes),'73149cec6f2d3505113cfed1e6c9d29e346006beaf5ed06edd4758cbdf806101');
if(fs.existsSync(out))throw Error('Refuse overwrite '+out);
const gates=[],depths=Array(98).fill(0);
function gate(op,a,b){const r=98+gates.length;gates.push({op,a,b});depths.push(1+Math.max(depths[a],depths[b]));return r;}
const sigma=Array.from({length:32},(_,i)=>gate('xor',gate('xor',(i+2)%32,(i+13)%32),(i+22)%32));
const majority=Array.from({length:32},(_,i)=>{const ab=gate('and',i,32+i),ac=gate('and',i,64+i),bc=gate('and',32+i,64+i);return gate('xor',gate('xor',ab,ac),bc);});
let carry=96;const outputs=[];
for(let i=0;i<32;i++){const p=gate('xor',sigma[i],majority[i]);outputs.push(gate('xor',p,carry));if(i!==31)carry=gate('or',gate('and',sigma[i],majority[i]),gate('and',p,carry));}
const N=gates.length,D=Math.max(...depths),V=1060000,F=V+4*N,U=F+4*N;
assert.equal(N,381);assert.equal(D,67);assert.ok(U+4*N<17*65536);
function load(p,i){return `(i32.load offset=${4*i} ${p})`;}
function ref(r){if(r<96)return `(i32.and (i32.shr_u (local.get $${['a','b','c'][Math.floor(r/32)]}) (i32.const ${r%32})) (i32.const 1))`;if(r<98)return `(i32.const ${r-96})`;return load('(local.get $v)',r-98);}
function poly({op,a,b}){a=ref(a);b=ref(b);const product=`(i32.mul ${a} ${b})`;return op==='and'?product:`(i32.sub (i32.add ${a} ${b}) ${op==='xor'?`(i32.mul (i32.const 2) ${product})`:product})`;}
function helper(coefficient){
 const evals=gates.map((g,i)=>`(i32.store offset=${4*i} (i32.const ${F}) ${poly(g)})`).join('\n');
 const residual=i=>`(i32.sub ${load('(local.get $v)',i)} ${load(`(i32.const ${F})`,i)})`;
 const updates=gates.map((_,i)=>`(i32.store offset=${4*i} (local.get $u) (i32.sub ${load(`(i32.const ${F})`,i)} (i32.mul (i32.const ${coefficient}) (i32.add ${residual(i)} ${residual((i+1)%N)}))))`).join('\n');
 let result='(i32.const 0)';outputs.forEach((r,i)=>{result=`(i32.add ${result} (i32.shl ${load('(local.get $v)',r-98)} (i32.const ${i})))`;});
 return `(global $evaluations (export "evaluations") (mut i32) (i32.const 0))
 (func $settle (export "t2") (param $a i32) (param $b i32) (param $c i32) (result i32)
 (local $v i32) (local $u i32) (local $swap i32) (local $step i32)
 (global.set $evaluations (i32.add (global.get $evaluations) (i32.const 1)))
 (local.set $v (i32.const ${V})) (local.set $u (i32.const ${U}))
 (memory.fill (local.get $v) (i32.const 255) (i32.const ${4*N}))
 (loop $settle_loop
 ${evals}
 ${updates}
 (local.set $swap (local.get $v)) (local.set $v (local.get $u)) (local.set $u (local.get $swap))
 (local.set $step (i32.add (local.get $step) (i32.const 1)))
 (br_if $settle_loop (i32.lt_u (local.get $step) (i32.const ${D*32}))))
 ${result})`;
}
function transformed(coefficient){
 let source=bytes.toString();
 function once(old,replacement){assert.equal(source.split(old).length,2,'patch '+old);source=source.replace(old,replacement);}
 once('(func $compress (param $p i32)','(func $compress (param $p i32) (param $last i32)');
 once('(call $compress (i32.add (i32.const 1024) (local.get $pos)))','(call $compress (i32.add (i32.const 1024) (local.get $pos)) (i32.const 0))');
 once('(call $compress (i32.const 256))','(call $compress (i32.const 256) (i32.eq (local.get $tail) (i32.const 256)))');
 once('(call $compress (i32.const 320))','(call $compress (i32.const 320) (i32.const 1))');
 const ordinary='(i32.add (call $S0 (local.get $a)) (i32.or (i32.and (local.get $a) (local.get $b)) (i32.and (local.get $c) (i32.or (local.get $a) (local.get $b)))))';
 once(`(local.set $t2 ${ordinary})`,`(local.set $t2 (if (result i32) (i32.and (local.get $last) (i32.eq (local.get $j) (i32.const 63))) (then (call $settle (local.get $a) (local.get $b) (local.get $c))) (else ${ordinary})))`);
 assert.ok(source.trimEnd().endsWith(')'));
 source=source.trimEnd().slice(0,-1)+helper(coefficient)+'\n)\n';return source;
}
const wabt=path.resolve(__dirname,'../../.tools/wabt-1.0.42/bin');
const run=(name,args)=>cp.execFileSync(path.join(wabt,name+'.exe'),args,{encoding:'utf8',timeout:30000}).trim();
fs.mkdirSync(out,{recursive:true});
const manifest={status:'provisional; novelty unresolved',node:process.version,wabt:run('wat2wasm',['--version']),baseline_sha256:sha(bytes),build_sha256:sha(fs.readFileSync(__filename)),gates:N,depth:D,iterations:D*32,scratch:{v:V,f:F,u:U,end:U+4*N},files:[]};
for(const [mode,wat] of [['plain',bytes.toString()],['fixedpoint',transformed(2)],['bad-odd-mixing',transformed(1)]]){
 const stem=path.join(out,mode);fs.writeFileSync(stem+'.wat',wat);run('wat2wasm',[stem+'.wat','-o',stem+'.wasm']);run('wasm-validate',[stem+'.wasm']);
 const binary=fs.readFileSync(stem+'.wasm');manifest.files.push({mode,file:mode+'.wasm',bytes:binary.length,sha256:sha(binary),wat_sha256:sha(wat)});
}
fs.writeFileSync(path.join(out,'circuit.json'),JSON.stringify({gates,depths,outputs},null,2)+'\n');
manifest.circuit_sha256=sha(fs.readFileSync(path.join(out,'circuit.json')));
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest,null,2));
