'use strict';
// Derive SHA-224 from the pinned SHA-256 WAT; original expressions: sha.js 2.4.11.
// See ../sha256-research-baseline/vendor/LICENSE. No baseline files are modified.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,out=path.resolve(process.argv[2]||path.join(root,'artifacts'));
const base=path.resolve(root,'../sha256-research-baseline/artifacts/plain.wat');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(base),baseHash='73149cec6f2d3505113cfed1e6c9d29e346006beaf5ed06edd4758cbdf806101';
assert.equal(sha(bytes),baseHash,'Baseline changed; review patches before building');
if(fs.existsSync(out))throw Error('Refuse overwrite: '+out);
const wabt=path.resolve(root,'../../.tools/wabt-1.0.42/bin');
const run=(exe,args)=>cp.execFileSync(path.join(wabt,exe+'.exe'),args,{encoding:'utf8',timeout:30000}).trim();
let source=bytes.toString('utf8');
function once(old,replacement){assert.equal(source.split(old).length,2,'Patch must match once: '+old);source=source.replace(old,replacement);}
// FIPS 180-4 sections 5.3.2 and 6.3: distinct IV and first seven output words.
const iv256=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
const iv224=[0xc1059ed8,0x367cd507,0x3070dd17,0xf70e5939,0xffc00b31,0x68581511,0x64f98fa7,0xbefa4fa4];
iv256.forEach((v,i)=>once(`(i32.store (i32.const ${384+4*i}) (i32.const ${v|0}))`,`(i32.store (i32.const ${384+4*i}) (i32.const ${iv224[i]|0}))`));
once('(i32.store (i32.const 540) (call $swap (i32.load (i32.const 412))))','');
once('(func $compress (param $p i32)','(func $compress (param $p i32) (param $last i32)');
once('(call $compress (i32.add (i32.const 1024) (local.get $pos)))','(call $compress (i32.add (i32.const 1024) (local.get $pos)) (i32.const 0))');
once('(call $compress (i32.const 256))','(call $compress (i32.const 256) (i32.eq (local.get $tail) (i32.const 256)))');
once('(call $compress (i32.const 320))','(call $compress (i32.const 320) (i32.const 1))');
const correct='(local.set $h (i32.add (local.get $h) (i32.and (i32.xor (local.get $e) (i32.const -1)) (local.get $g))))\n';
const erase='(local.set $g (i32.const 0))';
const round63='(i32.eq (local.get $j) (i32.const 63))';
fs.mkdirSync(out,{recursive:true});
const manifest={node:process.version,wabt:run('wat2wasm',['--version']),baseline_sha256:baseHash,build_sha256:sha(fs.readFileSync(__filename)),files:[]};
for(const mode of ['plain','erasure','bad-no-compensation','bad-every-block']){
 const condition=mode==='bad-every-block'?round63:`(i32.and (local.get $last) ${round63})`;
 const insertion=mode==='plain'?'':`(if ${condition} (then ${mode==='bad-no-compensation'?'':correct}${erase}))\n`;
 assert.equal(source.split('(loop $round ').length,2);
 const wat=source.replace('(loop $round ','(loop $round '+insertion),stem=path.join(out,mode);
 fs.writeFileSync(stem+'.wat',wat);
 run('wat2wasm',[stem+'.wat','-o',stem+'.wasm']);
 run('wasm-validate',[stem+'.wasm']);
 const binary=fs.readFileSync(stem+'.wasm');
 manifest.files.push({mode,file:mode+'.wasm',bytes:binary.length,sha256:sha(binary),wat_sha256:sha(wat)});
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify(manifest,null,2));
