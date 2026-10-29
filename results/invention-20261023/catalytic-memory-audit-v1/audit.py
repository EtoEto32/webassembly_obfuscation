# -*- coding: utf-8 -*-
"""Independent WABT execution and artifact replay for the restricted gate."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import gate as g


def main(source, output):
    src,out=Path(source),Path(output);out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((src/'manifest.json').read_text(encoding='utf8'))
    pins=json.loads((src/'sha256.json').read_text(encoding='utf8'))
    for file,digest in pins.items():assert hashlib.sha256((src/file).read_bytes()).hexdigest()==digest,file
    info={'pins_checked':len(pins),'replays':[],'interpreter':[],'rejections':[]}
    for name in ('and','mul','div'):
        dest=out/(name+'-replay.wasm');g.transform(src/(name+'-plain.wasm'),dest)
        assert dest.read_bytes()==(src/(name+'-borrowed.wasm')).read_bytes()
        info['replays'].append(dest.name)
    for j,t in enumerate(manifest['targets']):
        mod=g.w.parse(g.w.tool('wasm2wat',[src/t['file'],'--fold-exprs']))
        rows=[(0,0,1),(0xffffffff,0x80000000,7),(0x80000001,0xffffffff,0),(0x12345678,0x98765432,0xffffffff)]
        expected=[]
        for i,(x,y,z) in enumerate(rows):
            dirty=(0xace10293+1777*i)&g.MASK
            args=[x,y,z][:t['n']]
            call='(call 0 '+' '.join('(i32.const '+str(a)+')' for a in args)+')'
            code=f'(func (export "probe{i}") (result i32) (i32.store (i32.const 0) (i32.const {dirty})) {call})'
            mod.append(g.w.parse('(module '+code+')')[1])
            code=f'(func (export "state{i}") (result i32) (i32.eq (i32.load (i32.const 0)) (i32.const {dirty})))'
            mod.append(g.w.parse('(module '+code+')')[1])
            p=x&y if t['fixture']=='and' else x*y&g.MASK
            expected.append('trap' if t['fixture']=='div' and z==0 else p//z if t['fixture']=='div' else p)
        dest=out/('probe-'+str(j)+'.wasm');g.save(g.w.emit(mod),dest)
        result=g.w.tool('wasm-interp',[dest,'--run-all-exports'])
        (out/(dest.stem+'.txt')).write_text(result,encoding='utf8')
        for i,e in enumerate(expected):
            line=next(l for l in result.splitlines() if l.startswith('probe'+str(i)+'()'))
            if e=='trap':assert 'error:' in line and 'divide by zero' in line,line
            else:assert int(re.search(r'i32:(\d+)',line)[1])==e,line
            state=next(l for l in result.splitlines() if l.startswith('state'+str(i)+'()'))
            assert state.endswith('i32:1'),state
        info['interpreter'].append({'file':t['file'],'calls':4,'state_checks':4,'expected_traps':expected.count('trap')})
    # Output-equivalent normal execution alone must not authorize restoration
    # across an observable trap. Both binaries were rejected by the main run.
    for t in manifest['negative']:
        r=g.recover(src/t['file'],out/('must-not-exist-'+t['file']))
        assert r['status']=='trap_memory_changed'
        info['rejections'].append({'file':t['file'],**r})
    (out/'audit.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    shutil.copyfile(__file__,out/'audit.py')
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'pins_checked':len(pins),'byte_replays':3,'interpreter_calls':sum(r['calls'] for r in info['interpreter']),'memory_checks':sum(r['state_checks'] for r in info['interpreter']),'negative_rejections':len(info['rejections'])}))


if __name__=='__main__':main(*sys.argv[1:])
