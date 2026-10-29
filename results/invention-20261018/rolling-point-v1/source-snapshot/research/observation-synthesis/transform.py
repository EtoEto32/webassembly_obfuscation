"""Wasm binary -> exact-profile expression resynthesis -> Wasm binary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import time
import core

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(os.environ.get('WASM_TOOLS_ROOT', ROOT/'.tools'))
WABT = TOOLS/'wabt-1.0.42/bin'


def tool(name, args):
    return subprocess.run([str(WABT/(name+'.exe')), *map(str,args)], check=True,
                          capture_output=True, text=True, timeout=30).stdout


def parse(s):
    tokens = [t for t in re.findall(r'"(?:\\.|[^"\\])*"|;;[^\n]*|\(;[\s\S]*?;\)|[()]|[^\s()]+',s)
              if not t.startswith(';;') and not t.startswith('(;')]
    p=0
    def one():
        nonlocal p
        t=tokens[p];p+=1
        if t!='(':
            return t
        a=[]
        while tokens[p]!=')':
            a.append(one())
        p+=1
        return a
    ast=one()
    if p!=len(tokens) or ast[0]!='module':
        raise ValueError('Expected WABT single module')
    return ast


def emit(n):
    return '('+' '.join(map(emit,n))+')' if isinstance(n,list) else n


def expression(n):
    if not isinstance(n,list):
        return None
    if n[0]=='local.get' and len(n)==2:
        return 'v'+n[1]
    if n[0]=='i32.const' and len(n)==2:
        return int(n[1],0)
    if n[0] in ('i32.add','i32.sub','i32.mul') and len(n)==3:
        a,b=expression(n[1]),expression(n[2])
        if a is not None and b is not None:
            return [n[0][4:],a,b]
    return None


def wat(t):
    if isinstance(t,int):
        n=t & core.MASK
        return ['i32.const',str(n if n<0x80000000 else n-(1<<32))]
    if isinstance(t,str):
        return ['local.get',t[1:]]
    return ['i32.'+t[0],wat(t[1]),wat(t[2])]


def transform(src,out,mode,seed=20261018):
    if out.exists() or Path(str(out)+'.json').exists():
        raise ValueError('Refuse overwrite')
    start=time.perf_counter();tool('wasm-validate',[src])
    module=parse(tool('wasm2wat',[src,'--fold-exprs']))
    records=[];rng=random.Random(seed)
    def walk(n):
        if not isinstance(n,list):
            return n
        e=expression(n)
        if e is not None and core.cost(e)>=3 and len(records)<32:
            wanted=core.target(e)
            if wanted is not None:
                pool,stats=core.generate(e)
                keep=core.frontier(pool)
                if mode=='output-only':
                    chosen=min(pool,key=lambda t:(core.cost(t),core.key(t)))
                elif mode=='random':
                    chosen=rng.choice(pool)
                else:
                    scored=[]
                    for t in keep:
                        rec=core.recover_two(t,wanted)
                        # No result under term limits is NOT a successful defense.
                        score=rec['cost'] if rec['cost'] is not None else (3 if rec['status'].startswith('not_found') else -1)
                        scored.append((-score,core.cost(t),core.key(t),t))
                    chosen=min(scored)[3]
                if core.polynomial(e)!=core.polynomial(chosen):
                    raise AssertionError('Not equivalent')
                records.append({'source':e,'target':wanted,'chosen':chosen,'search':stats,
                                'frontier_size':len(keep),'source_cost':core.cost(e),'chosen_cost':core.cost(chosen),
                                'recovery':core.recover_two(chosen,wanted),
                                'certificate':[[list(m),c] for m,c in sorted(core.polynomial(e).items())]})
                return wat(chosen)
        return list(map(walk,n))
    result=walk(module)
    out.parent.mkdir(parents=True,exist_ok=True)
    wp=Path(str(out)+'.wat');wp.write_text(emit(result)+'\n',encoding='utf-8')
    tool('wat2wasm',[wp,'-o',out]);tool('wasm-validate',[out])
    report={'mode':mode,'seed':seed,'inputSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'outputSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'elapsed_seconds':time.perf_counter()-start,
            'regions':records,'supported':'pure i32 add/sub/mul over local.get and i32.const; WABT folded text only',
            'limitations':['Finite bounded rewrite pool, not complete synthesis.',
                           'Selection uses algebraic 2-operation recovery only; not a resilience verdict.',
                           'Debug/custom sections not guaranteed preserved.',
                           'No post-optimizer scoring in this CLI version.'],
            'sourceSHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(core.__file__))}}
    Path(str(out)+'.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=('frontier','output-only','random'),default='frontier')
    args=ap.parse_args();r=transform(args.input,args.output,args.mode)
    print(json.dumps({'regions':len(r['regions']),'elapsed_seconds':r['elapsed_seconds'],'output':str(args.output)}))
