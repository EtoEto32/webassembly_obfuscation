'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=__dirname,bin=path.resolve(process.argv[2]),out=path.join(root,'artifacts');fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const modes=['structured','int-static','int-rotating','gc-static','gc-rotating'];
const get=n=>`(local.get $${n})`, con=n=>`(i32.const ${n})`, op=(o,a,b)=>`(i32.${o} ${a}${b===undefined?'':' '+b})`;
function wat(kernel,mode){
  const gc=mode.startsWith('gc'),rot=mode.endsWith('rotating'),x=get('x'),y=get('y'),n=get('n'),e=get('e');
  const stop=kernel==='gcd'?op('or',op('eqz',n),op('or',op('eqz',x),op('eqz',y))):op('eqz',n);
  const pred=kernel==='gcd'?op('ge_u',x,y):op('and',x,con(1));
  const arms=kernel==='gcd'?[`(local.set $x ${op('sub',x,y)})`,`(local.set $y ${op('sub',y,x)})`]:[
    `(local.set $x ${op('add',op('rotl',op('xor',x,y),con(5)),op('mul',n,con(73244475)))})
     (local.set $y ${op('xor',y,op('mul',x,con(33)))})`,
    `(local.set $x ${op('add',op('mul',x,x),y)})
     (local.set $y ${op('add',op('rotl',y,con(7)),x)})`];
  const dec=`(local.set $n ${op('sub',n,con(1))})`;
  const encode=s=>rot?op('xor',s,e):s;
  const set=s=>gc?`(local.set $pc (call $token ${encode(s)}))`:`(local.set $pc ${encode(s)})`;
  const test=s=>gc?(rot?`(if (result i32) ${e} (then (ref.test (ref $T${s^3}) (local.get $pc))) (else (ref.test (ref $T${s}) (local.get $pc))))`:`(ref.test (ref $T${s}) (local.get $pc))`):op('eq',get('pc'),encode(con(s)));
  const finish=`${dec} ${rot?`(local.set $e ${op('xor',e,con(3))})`:''} ${set(con(0))} (br $dispatch)`;
  let body;
  if(mode==='structured')body=`(block $exit (loop $dispatch (br_if $exit ${stop})
    (if ${pred} (then ${arms[0]}) (else ${arms[1]})) ${dec} (br $dispatch)))`;
  else body=`${set(con(0))} (block $exit (loop $dispatch
    (if ${test(0)} (then (br_if $exit ${stop})
      ${set(`(if (result i32) ${pred} (then ${con(1)}) (else ${con(2)}))`)} (br $dispatch)))
    (if ${test(1)} (then ${arms[0]} ${finish}))
    (if ${test(2)} (then ${arms[1]} ${finish}))
    (unreachable)))`;
  let types='';
  if(gc){
    for(let i=0;i<4;i++)types+=`(type $T${i} (struct ${'(field i32) '.repeat(i)}))
      (global $t${i} (ref $T${i}) (struct.new $T${i} ${'(i32.const 0) '.repeat(i)}))\n`;
    const choose=i=>i===3?'(global.get $t3)':`(if (result (ref eq)) (i32.eq (local.get $s) (i32.const ${i})) (then (global.get $t${i})) (else ${choose(i+1)}))`;
    types+=`(func $token (param $s i32) (result (ref eq)) ${choose(0)})`;
  }
  return `(module ${types}
  (func $run (export "run") (param $x i32) (param $y i32) (param $n i32) (result i64)
    ${mode==='structured'?'':`(local $pc ${gc?'(ref null eq)':'i32'})`} ${rot?'(local $e i32)':''}
    (local.set $n (i32.and (local.get $n) (i32.const 63))) ${body}
    (i64.or (i64.extend_i32_u (local.get $x)) (i64.shl (i64.extend_i32_u (local.get $y)) (i64.const 32))))
  (func (export "batch") (param $count i32) (param $seed i32) (result i64)
    (local $i i32) (local $sum i64)
    (block $done (loop $more (br_if $done (i32.ge_u (local.get $i) (local.get $count)))
      (local.set $sum (i64.xor (local.get $sum) (call $run
        (i32.add (local.get $seed) (i32.mul (local.get $i) (i32.const 1664525)))
        (i32.xor (local.get $seed) (i32.mul (local.get $i) (i32.const 1013904223)))
        (i32.add (i32.and (local.get $i) (i32.const 31)) (i32.const 16)))))
      (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $more))) (local.get $sum)))`;
}
const flags=['--enable-gc','--enable-reference-types','--enable-multivalue'];
const logs=[],files=[];
function tool(name,args){const r=cp.spawnSync(path.join(bin,name+'.exe'),args,{encoding:'utf8',timeout:30000});logs.push({name,args,status:r.status,stdout:r.stdout,stderr:r.stderr,error:r.error?.message});fs.writeFileSync(path.join(out,'build-log.json'),JSON.stringify(logs,null,2)+'\n');if(r.status!==0)throw Error(name+' failed: '+r.stderr);return r.stdout;}
const version=tool('wasm-as',['--version']).trim();
for(const kernel of ['mix','gcd'])for(const mode of modes){
  const base=kernel+'-'+mode,source=path.join(out,base+'.wat');fs.writeFileSync(source,wat(kernel,mode)+'\n');
  const raw=path.join(out,base+'-raw.wasm');tool('wasm-as',[source,...flags,'-o',raw]);
  for(const optimization of ['raw','O2']){
    const name=base+'-'+optimization,dest=path.join(out,name+'.wasm');
    if(optimization==='O2')tool('wasm-opt',[raw,...flags,'-O2','-o',dest]);
    tool('wasm-dis',[dest,'-o',path.join(out,name+'.dis.wat')]);
    const metrics=tool('wasm-opt',[dest,...flags,'--metrics']);fs.writeFileSync(path.join(out,name+'.metrics.txt'),metrics);
    const bytes=fs.readFileSync(dest);if(!WebAssembly.validate(bytes))throw Error('engine rejected '+name);
    files.push({name,kernel,mode,optimization,file:path.basename(dest),bytes:bytes.length,sha256:sha(bytes),source:path.basename(source),source_sha256:sha(fs.readFileSync(source)),metrics});
  }
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({node:process.version,v8:process.versions.v8,binaryen:version,flags,generator_sha256:sha(fs.readFileSync(__filename)),files},null,2)+'\n');
console.log(JSON.stringify({built:files.length,binaryen:version}));
