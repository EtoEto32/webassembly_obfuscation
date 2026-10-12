"""A cross-width SIMD layout primitive, NOT a claimed novel obfuscator."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TOOLS = Path(sys.argv[1]).resolve()
WAT = TOOLS / 'wabt-1.0.42/bin/wat2wasm.exe'
OPT = TOOLS / 'binaryen-version_133/bin/wasm-opt.exe'

def emit(mode):
    lines = ['(module',
      '(func (export "run") (param $a i32) (param $b i32) (param $c i32) (param $d i32) (param $u i32)',
      '(result i32 i32 i32 i32) (local $v v128) (local $k i32) (local $h i32) (local $t i32)',
      '(local.set $k (i32.and (local.get $u) (i32.const 15)))',
      '(local.set $h (i32.and (i32.shr_u (local.get $u) (i32.const 4)) (i32.const 7)))',
      '(local.set $t (i32.and (i32.shr_u (local.get $u) (i32.const 7)) (i32.const 3)))',
      '(local.set $v (v128.const i32x4 0 0 0 0))']
    for j, arg in enumerate('abcd'):
        lines.append(f'(local.set $v (i32x4.replace_lane {j} (local.get $v) (local.get ${arg})))')
    k='(local.get $k)'
    h='(i32.shl (local.get $h) (i32.const 1))'
    t='(i32.shl (local.get $t) (i32.const 2))'
    def shuffle(expr):
        lines.append('(local.set $v (i8x16.swizzle (local.get $v) (v128.xor '
          '(v128.const i8x16 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15) '
          f'(i8x16.splat {expr}))))')
    if mode != 'normal':
        shuffle(k)
        shuffle(k if mode == 'roundtrip' else f'(i32.xor {k} {h})')
    lines.append('(local.set $v (i16x8.extadd_pairwise_i8x16_u (local.get $v)))')
    if mode == 'roundtrip':
        shuffle(h)
    lines.append('(local.set $v (i16x8.add (i16x8.mul (local.get $v) (local.get $v)) (i16x8.splat (i32.const 37))))')
    if mode != 'normal':
        shuffle(h if mode == 'roundtrip' else f'(i32.xor {h} {t})')
    lines.append('(local.set $v (i32x4.extadd_pairwise_i16x8_u (local.get $v)))')
    if mode == 'roundtrip':
        shuffle(t)
    if mode != 'normal':
        shuffle(t)
    for j in range(4):
        lines.append(f'(i32x4.extract_lane {j} (local.get $v))')
    return '\n'.join(lines+['))\n'])

manifest = {'purpose':'primitive validation; novelty and resistance not established',
            'commands':[], 'binaries':[]}
for mode in ('normal','roundtrip','transport'):
    wat=ROOT/f'{mode}.wat'
    raw=ROOT/f'{mode}.wasm'
    opt=ROOT/f'{mode}.O2.wasm'
    wat.write_text(emit(mode),encoding='utf-8')
    for cmd in ([str(WAT),str(wat),'-o',str(raw)],
                [str(OPT),str(raw),'-O2','--enable-simd','--enable-multivalue','-o',str(opt)]):
        subprocess.run(cmd,check=True,capture_output=True,text=True)
        manifest['commands'].append(cmd)
    for path in (raw,opt):
        data=path.read_bytes()
        manifest['binaries'].append({'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
manifest['tools']={str(p):subprocess.check_output([str(p),'--version'],text=True).strip() for p in (WAT,OPT)}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest['binaries'],indent=2))
