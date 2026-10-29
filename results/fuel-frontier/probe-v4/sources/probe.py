"""Reproducible fixture construction and independent source interpreter."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import transform as t

HERE=Path(__file__).resolve().parent
MASK=2**32-1


def step():
    return ['local.set','2',['i32.add',['i32.mul',['i32.xor',['local.get','2'],['i32.const','13']],['i32.const','1664525']],['i32.const','1013904223']]]


def blocks(counts):
    out=[]
    for i,c in enumerate(counts):
        out.extend(step() for _ in range(c))
        if i<len(counts)-1: out.append(['call','0',['i32.const',str(100+i)]])
    return out


def module(kind):
    if kind=='swap': arms=[blocks([12,1]),blocks([1,12])]
    elif kind=='three': arms=[blocks([20,1,1]),blocks([1,1,20])]
    elif kind=='equal': arms=[blocks([4,4]),blocks([4,4])]
    elif kind=='noevent': arms=[blocks([14]),blocks([14])]
    elif kind=='asymmetric':
        # Additional neutral arithmetic is charged but preserves the public result.
        arms=[blocks([1,8]),blocks([1,8])]
        arms[0][0:0]=[['local.set','2',['i32.xor',['local.get','2'],['i32.const','0']]]]*7
    elif kind=='nested':
        alt=['if',['i32.and',['local.get','0'],['i32.const','2']],
             ['then',*blocks([2,10,1])],['else',*blocks([10,1,2])]]
        arms=[[alt],blocks([1,2,10])]
    elif kind=='many': arms=[blocks([2]*12+[20]),blocks([20]+[2]*12)]
    else: raise ValueError(kind)
    return ['module',['type',['func',['param','i32']]],
      ['import','"env"','"mark"',['func',['type','0']]],
      ['func',['param','i32','i32'],['result','i32'],['local','i32'],
       ['local.set','2',['local.get','1']],
       ['if',['i32.and',['local.get','0'],['i32.const','1']],['then',*arms[0]],['else',*arms[1]]],
       ['local.get','2']],['export','"run"',['func','1']]]


def oracle(tree,args):
    """Direct AST interpreter; does not call transform's analysis/cost functions."""
    f=next(x for x in tree[1:] if x[0]=='func')
    locals_=list(args)+[0]*sum(len(x)-1 for x in f[1:] if x[0]=='local');spent=0;events=[];prefix=[]
    class Branch(Exception):
        def __init__(self,depth):self.depth=depth
    class Returned(Exception):
        def __init__(self,value):self.value=value
    def ex(x):
        nonlocal spent
        spent+=1;op=x[0]
        if op=='i32.const': return int(x[1]) & MASK
        if op=='local.get': return locals_[int(x[1])]
        if op=='i32.eqz':return int(ex(x[1])==0)
        a=ex(x[1]);b=ex(x[2])
        return {'i32.add':lambda:(a+b)&MASK,'i32.mul':lambda:(a*b)&MASK,
                'i32.xor':lambda:a^b,'i32.and':lambda:a&b,
                'i32.shr_u':lambda:a>>(b&31)}[op]()
    def seq(xs):
        nonlocal spent
        result=None
        for x in xs:
            op=x[0]
            if op=='local.set': spent+=1;locals_[int(x[1])]=ex(x[2])
            elif op=='if':
                spent+=1; c=ex(x[1])
                try:seq(x[2][1:] if c else (x[3][1:] if len(x)==4 else []))
                except Branch as jump:
                    if jump.depth:jump.depth-=1;raise
            elif op=='block':
                try:seq(x[1:])
                except Branch as jump:
                    if jump.depth:jump.depth-=1;raise
            elif op=='br':spent+=1;raise Branch(int(x[1]))
            elif op=='br_if':
                spent+=1
                if ex(x[2]):raise Branch(int(x[1]))
            elif op=='nop':spent+=1
            elif op=='call':
                spent+=1;values=[ex(v) for v in x[2:]];events.append(values[0] if len(values)==1 else values);prefix.append(spent)
            elif op=='return':spent+=1;raise Returned(ex(x[1]))
            else: result=ex(x)
        return result
    try:value=seq([x for x in f[1:] if x[0] not in ('param','result','local','type')])
    except Returned as result:value=result.value
    return {'value':value,'events':events,'prefix':prefix+[spent]}


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('probe.py','transform.py','acyclic.py','run.cjs','plan.md','screening.md'):
        shutil.copy2(HERE/name,out/'sources'/name)
    records=[];commands=[]
    try:
        rng=random.Random(2026102405)
        for name in ('swap','three','equal','noevent','asymmetric','nested','many'):
            folder=out/name;folder.mkdir();tree=module(name)
            src=folder/'original.wasm';wp=folder/'original.wat';wp.write_text(t.w.emit(tree),encoding='utf8')
            t.w.tool('wat2wasm',[wp,'-o',src]);t.w.tool('wasm-validate',[src])
            modes={}
            for mode in t.MODES:
                modes[mode]=t.transform(src,folder/(mode+'.wasm'),mode)
                t.w.tool('wasm-opt',[folder/(mode+'.wasm'),'-O3','-o',folder/(mode+'-O3.wasm')])
                t.w.tool('wasm-validate',[folder/(mode+'-O3.wasm')])
            samples=[0,1,2,0x7fffffff,0x80000000,0xffffffff]+[rng.getrandbits(32) for _ in range(32)]
            inputs=[{'args':[secret,payload],'expected':oracle(tree,[secret,payload])} for secret in range(4) for payload in samples]
            records.append({'name':name,'modes':modes,'inputs':inputs})
        # Unsupported syntax must never be silently certified.
        bad={
          'secret_marker':'(module (import "env" "mark" (func (param i32))) (func (export "run") (param i32) (result i32) (call 0 (local.get 0)) (i32.const 0)))',
          'different_word':'(module (import "env" "mark" (func (param i32))) (func (export "run") (param i32) (result i32) (if (local.get 0) (then (call 0 (i32.const 1))) (else (call 0 (i32.const 2)))) (i32.const 0)))',
          'trap':'(module (import "env" "mark" (func (param i32))) (func (export "run") (param i32) (result i32) (drop (i32.div_u (i32.const 1) (local.get 0))) (i32.const 0)))',
          'loop':'(module (import "env" "mark" (func (param i32))) (func (export "run") (result i32) (loop (br 0)) (i32.const 0)))',
          'memory_access':'(module (import "env" "mark" (func (param i32))) (memory 1) (func (export "run") (result i32) (i32.load (i32.const 0))))',
        }
        rejected=[]
        for name,wat in bad.items():
            wp=out/(name+'.wat');src=out/(name+'.wasm');wp.write_text(wat,encoding='utf8')
            t.w.tool('wat2wasm',[wp,'-o',src])
            try: t.transform(src,out/(name+'-unexpected.wasm'),'frontier')
            except ValueError as exc: rejected.append({'case':name,'reason':str(exc)})
            else: raise AssertionError('bad module accepted: '+name)
        manifest={'seed':2026102405,'platform':platform.platform(),'python':platform.python_version(),'fixtures':records,'rejected':rejected}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'run.cjs'),str(out)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        commands.append({'args':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf8')
        if r.returncode: raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        pins={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'}
        (out/'sha256.json').write_text(json.dumps(pins,indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
