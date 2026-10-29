"""Byte replay, second interpreter, negative controls and adaptive timings."""
import copy
import json
import platform
import re
import statistics
import subprocess
import sys
from pathlib import Path
import prototype as p
import recover
from run import model

main,rec,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
profiles=json.loads((rec/'profiles/profiles.json').read_text())
rows=json.loads((main/'manifest.json').read_text());fixed=json.loads((rec/'manifest.json').read_text())
fixtures=json.loads((main/'fixtures.json').read_text());replay=[];times=[]
for row in rows:
    dst=out/row['file']
    if row['opt']=='raw':p.transform(main/(row['kernel']+'-source.wasm'),dst,row['mode'],37)
    else:p.q.tool('wasm-opt',[out/row['file'].replace('-O3.','-raw.'),'-O3','-o',dst])
    assert dst.read_bytes()==(main/row['file']).read_bytes();replay.append(dst.name)
    if row['mode'] in ('grid0','shifted'):
        samples=[];read_samples=[]
        for _ in range(11):
            r=recover.recover(dst,profiles)
            samples.append(r['recovery_ms']);read_samples.append(r['read_ms'])
        times.append(dict(file=row['file'],median_ms=statistics.median(samples),samples_ms=samples,
                          read_median_ms=statistics.median(read_samples),read_samples_ms=read_samples))
        target=out/(dst.stem+'-recovered.wasm');recover.recover(dst,profiles,target)
        assert target.read_bytes()==(rec/target.name).read_bytes();replay.append(target.name)
p.q.save(out/'replay.json',replay);p.q.save(out/'attack-timing.json',times)
triples=[[0,0x80000000,0],[0x80000000,0x3f800000,0x80000000],
         [1,0x3f000000,0x80000000],[0x7f7fffff,0x7f7fffff,0xff800000],
         [0x7f800001,0x3f800000,0],[0x00800001,0x3f000000,0],
         [0x3f000000,0,0x0080ffff],[0x3f800001,0x3f7ffffe,0xbf800000]]
interpreter=[]
for row in rows+fixed:
    m=p.q.read(out/row['file']);idx=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
    count=len([x for x in m[1:] if x[0]=='func'])
    for j,t in enumerate(triples):
        m.extend([['func',['result','i32'],['call',idx,*[['i32.const',str(x)] for x in t]]],
                  ['export','"probe'+str(j)+'"',['func',str(count+j)]]])
    dst=out/('interp-'+row['file']);p.q.compile(p.q.w.emit(m),dst)
    stdout=p.q.w.tool('wasm-interp',[dst,'--run-all-exports'])
    (out/(dst.stem+'.log')).write_text(stdout,encoding='utf-8')
    got={int(j):int(v) for j,v in re.findall(r'probe(\d+)\(\) => i32:(\d+)',stdout)}
    f=fixtures[row['kernel']];want=[model.evaluate(f['nodes'],f['root'],t) for t in triples]
    assert len(got)==len(want) and all(got[j]==v for j,v in enumerate(want)),row
    interpreter.append(dict(file=row['file'],expected=want,actual=[got[j] for j in range(len(want))]))
p.q.save(out/'interpreter.json',dict(inputs=triples,calls=len(interpreter)*len(triples),rows=interpreter))
source=p.q.read(main/'multiply-add-source.wasm');rejections=[]
for name in ('memory','division','noncanonical'):
    m=copy.deepcopy(source)
    if name=='memory':m.append(['memory','1'])
    elif name=='division':next(e for e in p.q.walk(m) if e[0]=='f32.mul')[0]='f32.div'
    else:next(e for e in p.q.walk(m) if e==['i32.const','2143289344'])[1]='0'
    file=out/('reject-'+name+'.wasm');p.q.compile(p.q.w.emit(m),file)
    try:p.transform(file,out/('unexpected-'+name+'.wasm'))
    except p.base.Unsupported as e:rejections.append(dict(case=name,validated=True,rejected=True,reason=str(e)))
    else:raise AssertionError(name)
for name in ('rounding-bias','phase-mismatch'):
    m=p.q.read(main/'multiply-add-shifted-raw.wasm')
    if name=='rounding-bias':next(e for e in p.q.walk(m) if e==['i64.const','268435455'])[1]='268435456'
    else:
        call=next(e for e in p.q.walk(m) if e[0]=='call' and e[1]=='2');call[3][1]=str(int(call[3][1])-1)
    file=out/('attack-reject-'+name+'.wasm');p.q.compile(p.q.w.emit(m),file)
    try:recover.recover(file,profiles)
    except p.base.Unsupported as e:rejections.append(dict(case=name,validated=True,rejected=True,reason=str(e)))
    else:raise AssertionError(name)
p.q.save(out/'rejections.json',rejections)
# Removing intermediate rounding is not a correct replacement.
m=p.q.read(main/'multiply-add-shifted-raw.wasm')
def strip(e):
    if not isinstance(e,list):return e
    if e[0]=='call' and e[1]=='2':return strip(e[2])
    return [strip(x) for x in e]
m=strip(m);f=out/'negative-no-rounding.wasm';p.q.compile(p.q.w.emit(m),f)
js="const fs=require('fs');const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(e.run(0x3f800001,0x3f7ffffe,0xbf800000)>>>0)"
actual=int(subprocess.check_output(['node','-e',js,str(f)],text=True));expected=0
assert actual!=expected
p.q.save(out/'negative-no-rounding.json',dict(input=triples[-1],expected=expected,actual=actual))
file=main/'horner6-shifted-O3.wasm';isolated=out/'isolated-recovered.wasm'
proc=subprocess.run([sys.executable,str(Path(__file__).with_name('recover.py')),str(file),str(isolated),
                     '--profiles',str(rec/'profiles/profiles.json')],capture_output=True,text=True,timeout=30)
proc.check_returncode();assert isolated.read_bytes()==(rec/'horner6-shifted-O3-recovered.wasm').read_bytes()
p.q.save(out/'isolated-recovery.json',json.loads(proc.stdout))
p.q.save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,processor=platform.processor(),
    node=subprocess.check_output(['node','--version'],text=True).strip(),
    wabt=p.q.w.tool('wasm-validate',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip()))
print(json.dumps(dict(replay=len(replay),interpreter_calls=len(interpreter)*len(triples),rejections=len(rejections),negative_detected=True)))
