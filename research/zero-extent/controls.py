import argparse
import json
from pathlib import Path
import subprocess
import prototype as p
import models
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    c=p.c;g=p.g;op=p.op;iff=models.iff;cases=[]
    def pair(name,good,bad,args,pages):
        for tag,body in [('good',good),('bad',bad)]:p.compile_wat(p.w.emit(models.module(body)),out/(name+'.'+tag+'.wasm'))
        cases.append(dict(name=name,args=args,pages=pages,good=name+'.good.wasm',bad=name+'.bad.wasm'))
    pair('zero-address',[iff(g(4),[models.store(1,g(0),g(3))])],
         [op('memory.fill',g(0),g(3),p.boolean(g(4)))],[0xffffffff,0,0,0x12345678,0],0)
    pair('partial-trap',[iff(g(4),[models.store(4,g(0),g(3))])],
         [op('memory.fill',op('i32.add',g(0),c(i)),op('i32.shr_u',g(3),c(i*8)),c(1)) for i in range(4)],
         [65534,0,0,0x12345678,1],1)
    pair('offset-wrap',[iff(g(4),[models.store(1,g(0),g(3),1)])],
         [op('memory.fill',op('i32.add',g(0),c(1)),g(3),c(1))],[0xffffffff,0,0,0x12345678,1],1)
    pair('public-dummy',[iff(g(4),[models.store(1,g(0),g(3))])],
         [models.store(1,p.choose(g(0),c(0),g(4)),g(3))],[123,0,0,0x12345678,0],1)
    # Two value-flow controls for the normalizer. First makes a previously
    # Boolean local unbounded in an earlier operand; second branches the bound.
    n=5
    f=['func',['export','"run"'],['param',*['i32']*5],['result','i32'],['local','i32'],
       op('local.set',str(n),c(1)),op('memory.fill',op('local.tee',str(n),g(0)),g(3),g(n)),c(0)]
    m=['module',['memory','0','2'],['export','"memory"',['memory','0']],f]
    p.compile_wat(p.w.emit(m),out/'operand-order.before.wasm')
    actual,_,_=p.read(out/'operand-order.before.wasm');rec,stats=p.normalize(actual)
    assert stats['byte_fills']==0,stats
    p.compile_wat(p.w.emit(rec),out/'operand-order.after.wasm')
    controls=dict(cases=cases,normalizer=dict(before='operand-order.before.wasm',after='operand-order.after.wasm',stats=stats))
    rejections=[]
    for name,body in [('load',[iff(g(4),[models.store(1,g(0),op('i32.load',g(1)))])]),
                      ('division',[iff(g(4),[models.store(1,g(0),op('i32.div_u',g(2),g(3)))])])]:
        src=out/(name+'.wasm');p.compile_wat(p.w.emit(models.module(body)),src)
        try:p.transform(src,out/(name+'.transformed.wasm'));raise AssertionError('Accepted '+name)
        except ValueError as err:rejections.append(dict(name=name,reason=str(err)))
    controls['rejections']=rejections;(out/'manifest.json').write_text(json.dumps(controls,indent=2),encoding='utf-8')
    r=subprocess.run(['node',str(Path(__file__).with_name('controls.cjs')),str(out)],capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(r.stderr)
    (out/'checks.json').write_text(r.stdout,encoding='utf-8');print(r.stdout)
if __name__=='__main__':main()
