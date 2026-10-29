"""Reproducible generation of real binaries and non-destructive observer tests."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import prototype as k

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];p=k.p
fs=importlib.util.spec_from_file_location('reset_fixtures',ROOT/'research/logical-reset/fixtures.py')
fx=importlib.util.module_from_spec(fs);fs.loader.exec_module(fx)


def fixtures():
    for i,(pages,table) in enumerate([(0,0),(1,0),(1,2),(4,4)]):
        for extra in (False,True):
            item=fx.fixture(f'case-{i}-{int(extra)}',pages,8,table)
            source=item['wat']
            if extra:
                source=source[:-1]+'''(global (mut i64) (i64.const -9223372036854775808))
                (global (mut f32) (f32.const -0))
                (global (mut f64) (f64.const nan:0x8000000000012))
                (data "") (data "more") (elem func) (elem func 0 1)
                (func (export "drop_extra") data.drop 3 elem.drop 4)
                (func (export "float_write") (global.set 2 (f32.const nan:0x400001))
                  (global.set 3 (f64.const -0)))
                (func (export "nan_a") (global.set 2 (f32.const nan:0x400001)))
                (func (export "nan_b") (global.set 2 (f32.const nan:0x400002)))
                (func (export "nan_bits") (result i32) (i32.reinterpret_f32 (global.get 2))) )'''
            yield item['name'],source


def main(out):
    out.mkdir(parents=True,exist_ok=False);sources=out/'sources';sources.mkdir()
    for name in ('prototype.py','run.py','run.cjs','observer.cjs'):shutil.copy2(HERE/name,sources/name)
    rows=[];start=time.perf_counter()
    for name,wat in fixtures():
        raw=out/f'{name}-source.wasm';p.compile_wat(wat,raw)
        full=out/f'{name}-full.wasm';meta=k.transform(raw,full)
        num=out/f'{name}-numeric.wasm';nmeta=k.transform(raw,num,True)
        opt=out/f'{name}-full-O3.wasm'
        p.tool('wasm-opt',[full,'-O3','--enable-bulk-memory','--enable-reference-types','-o',opt])
        p.tool('wasm-validate',[opt])
        variants={}
        for mode in ('full','plain','no-bounds','no-drop'):
            dest=out/f'{name}-J-{mode}.wasm';p.compile_wat(p.w.emit(p.Reset(p.read(num),mode).output()),dest)
            variants[mode]=dest.name
        rows.append({'name':name,'source':raw.name,'full':full.name,'optimized':opt.name,'numeric':num.name,
                     'manifest':meta,'numericManifest':nmeta,'J':variants})
    manifest={'rows':rows,'generationSeconds':time.perf_counter()-start}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    cmd=['node',str(HERE/'run.cjs'),str(out.resolve())]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=180)
    (out/'node-log.json').write_text(json.dumps({'command':cmd,'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.relative_to(out).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()
         for x in out.rglob('*') if x.is_file() and x.name!='sha256.json'},indent=2),encoding='utf8')
    if run.returncode:raise RuntimeError(run.stderr)
    print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
