'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe');
const m=65537n,n=65539n,M=m*n;
let inv=1n;while((m*inv)%n!==1n)inv++;
const const64=x=>`(i64.const ${x})`,get=x=>`(local.get $${x})`,rem=(x,d)=>`(i64.rem_u ${x} ${const64(d)})`;
const crt=`(i32.wrap_i64 (i64.add ${get('a')} (i64.mul ${const64(m)} ${rem(`(i64.mul (i64.sub (i64.add ${get('b')} ${const64(n)}) ${get('a')}) ${const64(inv)})`,n)})))`;
const funcs=[];
for(const op of ['add','mul']){
 funcs.push(`(func (export "plain_${op}") (param $x i32)(param $y i32)(result i32)(i32.${op} ${get('x')} ${get('y')}))`);
 for(const kind of ['residue','normalized']){
  const value=d=>kind==='residue'?rem(`(i64.${op} ${rem('(i64.extend_i32_u (local.get $x))',d)} ${rem('(i64.extend_i32_u (local.get $y))',d)})`,d):rem(`(i64.extend_i32_u (i32.${op} ${get('x')} ${get('y')}))`,d);
  funcs.push(`(func (export "${kind}_${op}") (param $x i32)(param $y i32)(result i32)(local $a i64)(local $b i64)(local.set $a ${value(m)})(local.set $b ${value(n)})${crt})`);
 }
}
const wat='(module '+funcs.join('\n')+')';const wf=path.join(out,'probe.wat'),bf=path.join(out,'probe.wasm');fs.writeFileSync(wf,wat);cp.execFileSync(asm,[wf,'-o',bf]);
const bytes=fs.readFileSync(bf),ex=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const cases=[];for(const x of [0,1,2,65535,65536,65537,0x7fffffff,0x80000000,0xfffffffe,0xffffffff])for(const y of [0,1,2,65535,65536,65537,0x7fffffff,0x80000000,0xfffffffe,0xffffffff])cases.push([x,y]);
let seed=0x17ac2481;const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};for(let i=0;i<1024;i++)cases.push([rng(),rng()]);
const rows=[];
for(const op of ['add','mul'])for(const [x,y]of cases){const value=op==='add'?BigInt(x)+BigInt(y):BigInt(x)*BigInt(y),expected=Number(BigInt.asUintN(32,value));
 const actual={};for(const kind of ['plain','residue','normalized'])actual[kind]=ex[kind+'_'+op](x,y)>>>0;
 assert.equal(actual.plain,expected);assert.equal(actual.normalized,expected);assert.equal(actual.residue,Number(BigInt.asUintN(32,value%M)));
 rows.push({op,x,y,expected,...actual,integerResult:value.toString(),crossesM:value>=M,mismatch:actual.residue!==expected});}
// Small full-domain witness for closure failure: encoding itself fails to
// preserve addition in Z/256 when components use moduli 17 and 19.
let smallFailures=0;for(let x=0;x<256;x++)for(let y=0;y<256;y++){
 if([17,19].some(d=>((x+y)&255)%d!==((x%d+y%d)%d)))smallFailures++;
}
const summary={node:process.version,v8:process.versions.v8,assembler:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),moduli:[m.toString(),n.toString()],M:M.toString(),inverse:inv.toString(),seed:'0x17ac2481',sha256:crypto.createHash('sha256').update(bytes).digest('hex'),small8bit:{pairs:65536,encodingAdditionFailures:smallFailures},operations:['add','mul'].map(op=>{const r=rows.filter(x=>x.op===op);return {op,cases:r.length,residueMismatches:r.filter(x=>x.mismatch).length,firstCounterexample:r.find(x=>x.mismatch),plainMismatches:0,normalizedMismatches:0};})};
fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(rows,null,2));fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary,null,2));
