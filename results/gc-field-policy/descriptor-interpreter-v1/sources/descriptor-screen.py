"""A bounded semantic screen, not an implementation of a new protection scheme."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from workload import ROOT,HERE,command

TYPES='''(rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct)))'''
LIB=f'''(module {TYPES}
 (global $a (ref (exact $D)) (struct.new $D))
 (global $b (ref (exact $D)) (struct.new $D))
 (func (export "get-a") (result anyref) (struct.new_desc $T (i32.const 17) (global.get $a)))
 (func (export "get-b") (result anyref) (struct.new_desc $T (i32.const 29) (global.get $b)))
 (func (export "accept-a") (param $x anyref) (result i32)
  (struct.get $T 0 (ref.cast_desc_eq (ref $T) (local.get $x) (global.get $a)))))'''
IMPORTS='''(import "lib" "get-a" (func $get-a (result anyref)))
 (import "lib" "get-b" (func $get-b (result anyref)))
 (import "lib" "accept-a" (func $accept-a (param anyref) (result i32)))'''
CASES={
 'original':('(call $accept-a (call $get-a))',dict(type='return',value=17)),
 'different-brand':('(call $accept-a (call $get-b))',dict(type='trap')),
 'fresh-descriptor':('(call $accept-a (struct.new_desc $T (i32.const 77) (struct.new $D)))',dict(type='trap')),
 'copied-descriptor':('(call $accept-a (struct.new_desc $T (i32.const 77) (ref.get_desc $T (ref.cast (ref (exact $T)) (call $get-a)))))',dict(type='return',value=77)),
}


def main(out):
    out.mkdir(parents=True,exist_ok=False);commands=[];cases=[]
    binaryen=ROOT/'.tools/binaryen-version_133/bin';flags=['--mvp-features','--enable-reference-types','--enable-gc','--enable-custom-descriptors']
    for name,source in [('library',LIB)]+[(n,f'(module {TYPES} {IMPORTS} (func (export "run") (result i32) {body}))') for n,(body,_) in CASES.items()]:
        wat=out/f'{name}.wat';binary=out/f'{name}.wasm';wat.write_text(source)
        c=command([binaryen/'wasm-as.exe',wat,*flags,'-o',binary]);commands.append(c);(out/'commands.json').write_text(json.dumps(commands,indent=2));assert c['code']==0,c
        if name!='library':cases.append(dict(name=name,path=str(binary.resolve()),expected=CASES[name][1]))
    spec=out/'spec.json';spec.write_text(json.dumps(dict(library=str((out/'library.wasm').resolve()),cases=cases),indent=2))
    c=command(['node','--experimental-wasm-custom-descriptors',HERE/'descriptor-screen.mjs',spec]);commands.append(c);(out/'commands.json').write_text(json.dumps(commands,indent=2));assert c['code']==0,c
    result=json.loads(c['stdout']);assert all(r['result']==r['expected'] for r in result['rows']),result
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'descriptor-screen.py',HERE/'descriptor-screen.mjs',HERE/'next-direction-screen.md'):shutil.copyfile(p,sources/p.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
