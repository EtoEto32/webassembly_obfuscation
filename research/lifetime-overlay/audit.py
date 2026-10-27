import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import prototype as p
import fixtures


def main(src,perf,out):
    src=Path(src);perf=Path(perf);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    verified={}
    for folder in (src,perf):
        pins=json.loads((folder/'pins.json').read_text())
        for file,h in pins.items():assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==h
        verified[folder.name]=len(pins)
    manifest=json.loads((src/'manifest.json').read_text())
    replay=[];interpreter=[];normalized=[]
    for row in manifest['targets']:
        if row.get('negative'):continue
        file=row['file'];target=src/file;dst=out/file
        if row['mode'].endswith('-recovered'):
            p.recover(src/file.replace('-recovered',''),dst)
        elif row['stage']=='O3':
            p.wat.tool('wasm-opt',[out/file.replace('-O3',''),'-O3','-o',dst])
        elif row['mode']=='plain':p.save(p.wat.parse(fixtures.FIXTURES[row['name']]()),dst)
        else:p.transform(out/(row['name']+'-plain.wasm'),dst,row['mode'])
        assert dst.read_bytes()==target.read_bytes(),file
        replay.append(file)
        # WABT execution uses wrapper exports, not the Node engine.
        m=p.wat.parse(p.wat.tool('wasm2wat',[target,'--fold-exprs']))
        for i,(x,y) in enumerate(((0,0),(1,2),(0xffffffff,0x80000000),(0x87654321,0x12345678))):
            m.append(['func',['export',f'"probe{i}"'],['result','i32'],['call','0',['i32.const',str(x)],['i32.const',str(y)]]])
        test=out/(target.stem+'-interpreter.wasm');p.save(m,test)
        text=p.wat.tool('wasm-interp',[test,'--run-all-exports'])
        interpreter.append({'file':file,'output':text})
        if row['mode'].endswith('-recovered'):
            opt=out/(target.stem+'-normalized.wasm');p.wat.tool('wasm-opt',[target,'-O3','-o',opt])
            normalized.append({'file':file,'sha256':hashlib.sha256(opt.read_bytes()).hexdigest(),'bytes':opt.stat().st_size})
    # Independent results from ordinary Node instantiations for the four probes.
    code="const fs=require('fs');const m=JSON.parse(fs.readFileSync(process.argv[1]));let r=[];for(const x of m.targets){if(x.negative)continue;const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]+'/'+x.file))).exports.run;r.push({file:x.file,values:[[0,0],[1,2],[0xffffffff,0x80000000],[0x87654321,0x12345678]].map(a=>f(...a)>>>0)});}process.stdout.write(JSON.stringify(r));"
    r=subprocess.run(['node','-e',code,str(src/'manifest.json'),str(src)],capture_output=True,text=True,check=True,timeout=30)
    node=json.loads(r.stdout)
    for n,w in zip(node,interpreter):
        assert n['file']==w['file']
        expected=[f'probe{i}() => i32:{v}' for i,v in enumerate(n['values'])]
        assert w['output'].strip().splitlines()==expected,w
    # Valid modules outside source assumptions must fail closed.
    base='(module (memory 1 1) {extra} (func (export "run") (param i32 i32) (result i32) {body}))'
    controls={
        'exported-memory':('', '(export "memory" (memory 0))','(i32.const 0)'),
        'entry-read':('', '', '(i32.load (i32.const 0))'),
        'out-of-bounds':('', '', '(i64.store (i32.const 65532) (i64.const 1)) (i32.const 0)'),
        'mixed-width-source':('', '', '(i64.store (i32.const 0) (i64.const 1)) (i32.load (i32.const 0))'),
        'dynamic-address':('', '', '(i32.store (local.get 0) (i32.const 1)) (i32.const 0)'),
        'loop':('', '', '(loop (nop)) (i32.const 0)')}
    rejects=[]
    for name,(_,extra,body) in controls.items():
        binary=out/('reject-'+name+'.wasm');p.save(p.wat.parse(base.format(extra=extra,body=body)),binary)
        try:p.transform(binary,out/('unexpected-'+name+'.wasm'),'conflict')
        except ValueError as e:rejects.append({'name':name,'reason':str(e)})
        else:raise AssertionError('Accepted '+name)
    regression={
        'tee-order':'(i32.add (local.get 0) (local.tee 0 (i32.const 17)))',
        'load-before-branch-store':'(i32.store (i32.const 0) (local.get 0)) (i32.add (i32.load (i32.const 0)) (if (result i32) (i32.and (local.get 1) (i32.const 1)) (then (i32.store (i32.const 0) (i32.const 7)) (i32.load (i32.const 0))) (else (i32.store (i32.const 0) (i32.const 11)) (i32.load (i32.const 0)))))',
        'signed-load':'(i32.store (i32.const 0) (local.get 0)) (i32.wrap_i64 (i64.shr_u (i64.load32_s (i32.const 0)) (i64.const 32)))',
        'condition-write':'(if (result i32) (local.tee 0 (local.get 1)) (then (i32.add (local.get 0) (i32.const 7))) (else (i32.const 11)))'}
    regressions=[]
    for name,body in regression.items():
        binary=out/('regression-'+name+'.wasm');dst=binary.with_stem(binary.stem+'-recovered')
        p.save(p.wat.parse(base.format(extra='',body=body)),binary);report=p.recover(binary,dst)
        regressions.append({'name':name,'source':binary.name,'recovered':dst.name,**report})
    (out/'controls.json').write_text(json.dumps({'rejects':rejects,'regressions':regressions},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(p.HERE/'audit.cjs'),str(out)],capture_output=True,text=True,check=True,timeout=30)
    (out/'control-checks.json').write_text(r.stdout,encoding='utf8')
    control_checks=json.loads(r.stdout)
    # Attack timing: random order, five repeats of each binary, file/compile cost separated.
    schedule=[(t,i) for t in manifest['targets'] if not t.get('negative') and not t['mode'].endswith('-recovered') for i in range(5)]
    random.Random(20261022).shuffle(schedule);timings=[]
    for t,i in schedule:
        r=p.recover(src/t['file'],out/(f'timed-{i}-'+t['file']))
        timings.append({'file':t['file'],'rep':i,**r})
    # Static allocation guard at the page end, including unaligned source boundaries.
    boundaries=[]
    for mode in ('first','conflict'):
        cells=[(65520,8),(65528,4),(65532,4)];adj={c:set(cells)-{c} for c in cells}
        placements=p.allocate(cells,adj,mode)
        assert all(a+w<=65536 for (_,w),a in placements.items())
        boundaries.append({'mode':mode,'placements':[(c,a) for c,a in placements.items()]})
    summary={'verified_pins':verified,'reproduced_binaries':replay,'interpreter_calls':len(interpreter)*4,
             'interpreter':interpreter,'normalized':normalized,'timings':timings,'rejects':rejects,'boundary':boundaries}
    (out/'audit.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    for file in ('audit.py','audit.cjs','prototype.py','fixtures.py'):
        shutil.copyfile(p.HERE/file,out/('source-'+file))
    shutil.copyfile(p.HERE.parent/'connectivity-elimination/prototype.py',out/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'reproduced':len(replay),'interpreter_calls':len(interpreter)*4,'timed_attacks':len(timings),'rejections':len(rejects),'regression_calls':sum(x['calls'] for x in control_checks['rows'])}))

if __name__=='__main__':main(*sys.argv[1:])
