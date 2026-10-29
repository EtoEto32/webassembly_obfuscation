'use strict';
// SHA-256 round expressions adapted from sha.js 2.4.11. See vendor/LICENSE.
const fs=require('node:fs'), path=require('node:path'), cp=require('node:child_process'), crypto=require('node:crypto');
const root=__dirname, out=path.resolve(process.argv[2]||path.join(root,'artifacts'));
if(fs.existsSync(out)) throw Error('Refuse to overwrite: '+out);
fs.mkdirSync(out,{recursive:true});
const toolRoot=process.env.WASM_TOOLS_ROOT||path.resolve(root,'../../.tools');
const wabt=path.join(toolRoot,'wabt-1.0.42/bin'), opt=path.join(toolRoot,'binaryen-version_133/bin/wasm-opt.exe');
const run=(exe,args)=>cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000}).trim();
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(path.join(root,'vendor/sha256.js'),'utf8');
const K=source.match(/var K = \[([\s\S]*?)\]/)[1].match(/0x[0-9a-f]+/ig).map(Number);
const IV=[...source.matchAll(/this\._[a-h] = (0x[0-9a-f]+)/g)].map(m=>Number(m[1]));
if(K.length!==64||IV.length!==8)throw Error('Unexpected vendor constants');
const c=n=>`(i32.const ${n|0})`, g=n=>`(local.get $${n})`, set=(n,x)=>`(local.set $${n} ${x})`;
const bin=(op,a,b)=>`(i32.${op} ${a} ${b})`, sum=(...xs)=>xs.reduce((a,b)=>bin('add',a,b));
const load=p=>`(i32.load ${p})`, store=(p,x)=>`(i32.store ${p} ${x})`;
const call=(f,...args)=>`(call $${f} ${args.join(' ')})`;
const addr=(base,i)=>sum(c(base),bin('shl',i,c(2)));
const beLoad=p=>call('swap',load(p));
const swap=`(func $swap (param $x i32) (result i32)
 (i32.or (i32.and (i32.rotl ${g('x')} ${c(8)}) ${c(0x00ff00ff)})
 (i32.and (i32.rotl ${g('x')} ${c(24)}) ${c(0xff00ff00)})))`;
const sigma=(name,shifts,lastShift=false)=>`(func $${name} (param $x i32) (result i32)
 ${shifts.map((v,i)=>bin(lastShift&&i===2?'shr_u':'rotr',g('x'),c(v))).reduce((a,b)=>bin('xor',a,b))})`;
let transformCount=0;
function generate(mode){
 transformCount=0;
 // Helper parameters evaluate each operand once, including a memory load.
 const add=(...xs)=>xs.reduce((a,b)=>{transformCount++;return mode==='plain'?bin('add',a,b):call('mba_add',a,b)});
 const w=i=>load(c(i*4));
 const schedule=Array.from({length:64},(_,i)=>store(c(i*4),i<16?beLoad(sum(g('p'),c(i*4))):add(call('s1',w(i-2)),w(i-7),call('s0',w(i-15)),w(i-16)))).join('\n');
 const vars='abcdefgh'.split('');
 const init=vars.map((v,i)=>set(v,load(c(384+i*4)))).join('\n');
 const finish=vars.map((v,i)=>store(c(384+i*4),add(load(c(384+i*4)),g(v)))).join('\n');
 const ch=bin('xor',g('g'),bin('and',g('e'),bin('xor',g('f'),g('g'))));
 const maj=bin('or',bin('and',g('a'),g('b')),bin('and',g('c'),bin('or',g('a'),g('b'))));
 const t1=set('t1',add(g('h'),call('S1',g('e')),ch,load(addr(768,g('j'))),load(addr(0,g('j')))));
 const t2=set('t2',add(call('S0',g('a')),maj));
 const updates=[set('h',g('g')),set('g',g('f')),set('f',g('e')),set('e',add(g('d'),g('t1'))),set('d',g('c')),set('c',g('b')),set('b',g('a')),set('a',add(g('t1'),g('t2')))].join('\n');
 const kb=Buffer.alloc(256);K.forEach((k,i)=>kb.writeUInt32LE(k,i*4));
 return `(module
 (memory (export "memory") 17 17)
 (data ${c(768)} "${[...kb].map(b=>'\\'+b.toString(16).padStart(2,'0')).join('')}")
 ${swap}
 ${sigma('s0',[7,18,3],true)} ${sigma('s1',[17,19,10],true)}
 ${sigma('S0',[2,13,22])} ${sigma('S1',[6,11,25])}
 ${mode==='mba-add'?`(func $mba_add (param $x i32) (param $y i32) (result i32)
 (i32.add (i32.xor ${g('x')} ${g('y')}) (i32.shl (i32.and ${g('x')} ${g('y')}) ${c(1)})))`:''}
 (func $compress (param $p i32) ${[...vars,'j','t1','t2'].map(v=>`(local $${v} i32)`).join(' ')}
 ${schedule} ${init}
 (loop $round ${t1} ${t2} ${updates}
 ${set('j',sum(g('j'),c(1)))} (br_if $round (i32.lt_u ${g('j')} ${c(64)})))
 ${finish})
 (func (export "hash") (param $len i32) (result i32) (local $pos i32) (local $rem i32) (local $i i32) (local $tail i32)
 (if (i32.gt_u ${g('len')} ${c(1048576)}) (then unreachable))
 ${IV.map((v,i)=>store(c(384+i*4),c(v))).join('\n')}
 (block $done (loop $blocks
 (br_if $done (i32.lt_u (i32.sub ${g('len')} ${g('pos')}) ${c(64)}))
 ${call('compress',sum(c(1024),g('pos')))} ${set('pos',sum(g('pos'),c(64)))} (br $blocks)))
 ${set('rem',bin('sub',g('len'),g('pos')))}
 (loop $zero (i32.store8 ${sum(c(256),g('i'))} ${c(0)}) ${set('i',sum(g('i'),c(1)))}
 (br_if $zero (i32.lt_u ${g('i')} ${c(128)})))
 ${set('i',c(0))}
 (block $copied (loop $copy (br_if $copied (i32.ge_u ${g('i')} ${g('rem')}))
 (i32.store8 ${sum(c(256),g('i'))} (i32.load8_u ${sum(c(1024),g('pos'),g('i'))}))
 ${set('i',sum(g('i'),c(1)))} (br $copy)))
 (i32.store8 ${sum(c(256),g('rem'))} ${c(128)})
 ${set('tail',`(select ${c(320)} ${c(256)} (i32.ge_u ${g('rem')} ${c(56)}))`)}
 ${store(sum(g('tail'),c(60)),call('swap',bin('shl',g('len'),c(3))))}
 ${call('compress',c(256))}
 (if (i32.eq ${g('tail')} ${c(320)}) (then ${call('compress',c(320))}))
 ${vars.map((v,i)=>store(c(512+i*4),call('swap',load(c(384+i*4))))).join('\n')}
 ${c(512)}))\n`;
}
const manifest={node:process.version,wabt:run(path.join(wabt,'wat2wasm.exe'),['--version']),binaryen:run(opt,['--version']),build_sha256:sha(fs.readFileSync(__filename)),plan_sha256:sha(fs.readFileSync(path.join(root,'plan.json'))),vendor:{},files:[]};
for(const f of fs.readdirSync(path.join(root,'vendor')))manifest.vendor[f]=sha(fs.readFileSync(path.join(root,'vendor',f)));
for(const mode of ['plain','mba-add']){
 const wat=generate(mode), stem=path.join(out,mode);fs.writeFileSync(stem+'.wat',wat);
 const replacements=mode==='mba-add'?transformCount:0;
 run(path.join(wabt,'wat2wasm.exe'),[stem+'.wat','-o',stem+'.raw.wasm']);
 for(const optimization of ['raw','O2','O3']){
  const file=mode+'.'+optimization+'.wasm', dest=path.join(out,file);
  if(optimization!=='raw')run(opt,[stem+'.raw.wasm','-'+optimization,'-o',dest]);
  run(path.join(wabt,'wasm-validate.exe'),[dest]);
  run(path.join(wabt,'wasm2wat.exe'),[dest,'-o',dest.replace(/\.wasm$/,'.wat')]);
  const bytes=fs.readFileSync(dest);
  manifest.files.push({mode,optimization,file,bytes:bytes.length,sha256:sha(bytes),source:mode+'.wat',source_sha256:sha(wat),replacements});
 }
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify(manifest.files,null,2));
