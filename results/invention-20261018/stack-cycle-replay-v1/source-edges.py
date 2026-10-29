"""Supplemental scalar/stack profile checks, not protection benchmarks."""
import argparse
import json
from pathlib import Path
import subprocess
import transform as t
from experiment import save


def main(out):
    p=out/'edges';p.mkdir(exist_ok=False)
    programs={
      'i64':'(module (func (export "run") (param i64) (result i64) local.get 0 '+ 'i64.const 3 i64.mul i64.const 7 i64.rotl '*17+'))',
      'f32bits':'(module (func (export "run") (param i32) (result i32) local.get 0 f32.reinterpret_i32 '+'f32.neg '*17+'i32.reinterpret_f32))',
      'f64bits':'(module (func (export "run") (param i64) (result i64) local.get 0 f64.reinterpret_i64 '+'f64.neg '*17+'i64.reinterpret_f64))',
      'multiresult':'(module (func (export "run") (param i32 i64) (result i32 i64) local.get 0 local.get 1 '+'i64.const 3 i64.mul i64.const 7 i64.add '*17+'))',
      'select':'(module (func (export "run") (param i32 i32 i32) (result i32) local.get 0 '+'local.get 1 local.get 2 select i32.const 7 i32.add '*17+'))'
    }
    rows=[]
    for name,wat in programs.items():
        plain=p/(name+'-plain.wasm');plain.with_suffix('.wat').write_text(wat,encoding='utf-8')
        t.w.tool('wat2wasm',[plain.with_suffix('.wat'),'-o',plain])
        for mode in ('plain','payload','locals'):
            raw=plain if mode=='plain' else p/(name+'-'+mode+'.wasm')
            if mode!='plain':t.transform(plain,raw,mode,8)
            for opt in ('raw','O3'):
                file=raw if opt=='raw' else raw.with_name(raw.stem+'-O3.wasm')
                if opt!='raw':t.w.tool('wasm-opt',[raw,'--enable-multivalue','-O3','-o',file])
                rows.append({'name':name,'mode':mode,'opt':opt,'file':str(file.relative_to(out)).replace('\\','/')})
    bad={
      'loop':'(module (func (export "run") (param i32) (result i32) (loop (result i32) (local.get 0))))',
      'call':'(module (import "env" "f" (func (param i32) (result i32))) (func (export "run") (param i32) (result i32) (call 0 (local.get 0))))',
      'global':'(module (global i32 (i32.const 7)) (func (export "run") (result i32) (global.get 0)))',
      'grow':'(module (memory 1) (func (export "run") (param i32) (result i32) (memory.grow (local.get 0))))',
      'no-cuts':'(module (func (export "run") (param i32) (result i32) (local.get 0)))'
    }
    rejected=[]
    for name,wat in bad.items():
        wp=p/(name+'-unsupported.wat');wp.write_text(wat,encoding='utf-8');binary=wp.with_suffix('.wasm')
        t.w.tool('wat2wasm',[wp,'-o',binary]);t.w.tool('wasm-validate',[binary])
        try:t.transform(binary,p/(name+'-unexpected.wasm'))
        except ValueError as e:rejected.append({'name':name,'status':'explicitly_rejected','message':str(e)})
        else:raise AssertionError('Unsupported accepted '+name)
    save(out/'edge-manifest.json',rows);save(out/'unsupported.json',rejected)
    r=subprocess.run(['node',str(Path(__file__).with_name('edgecheck.cjs')),str(out)],capture_output=True,text=True,timeout=30)
    (out/'edges.log').write_text(r.stdout+r.stderr,encoding='utf-8');print(r.stdout.strip())
    if r.returncode:raise RuntimeError(r.stderr)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();main(a.output)
