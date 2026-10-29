"""Early gate for observation pullback across Wasm memory.copy.

Lazy copy/read forwarding is known. This restricted experiment is not a claim
of a new obfuscation primitive. Private scratch is unobservable between calls.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('range_common',HERE.parent/'mutation-quotient/prototype.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
q=c.q
SIZE=65536


def render(data,plan,mode='plain',checks=True):
    n=3*len(plan)+1;query=n-1
    if not 1<=len(plan)<=16 or sorted(v for row in plan for v in row)!=list(range(n-1)):raise ValueError('parameter permutation')
    if len(data)!=4096:raise ValueError('initial bytes')
    get=lambda i:f'(local.get {i})'
    if mode=='plain':
        segment='(data '+c.token(data)+')'
        body=f'(memory.fill (i32.const 0) (i32.const 0) (i32.const {SIZE})) (memory.init 0 (i32.const 0) (i32.const 0) (i32.const {len(data)})) '
        body+=' '.join('(memory.copy %s %s %s)'%tuple(map(get,row)) for row in plan)
    elif mode=='pullback':
        segment='(data (i32.const 0) '+c.token(data)+')';body=''
        if checks:
            for d,src,length in plan:
                for x in (d,src):
                    body+=f'(if (i64.gt_u (i64.add (i64.extend_i32_u {get(x)}) (i64.extend_i32_u {get(length)})) (i64.const {SIZE})) (then unreachable)) '
        # A query outside memory must trap even if arithmetic wrapping would
        # accidentally map it inside a previous source range.
        body+=f'(if (i32.ge_u {get(query)} (i32.const {SIZE})) (then unreachable)) '
        for d,src,length in reversed(plan):
            body+=f'''(if (i32.lt_u (i32.sub {get(query)} {get(d)}) {get(length)})
              (then (local.set {query} (i32.add {get(src)} (i32.sub {get(query)} {get(d)}))))) '''
    else:raise ValueError('mode')
    return f'''(module (memory 1 1) {segment}
      (func (export "run") (param {' '.join(['i32']*n)}) (result i32)
      {body} (i32.load8_u {get(query)})))'''


def data_of(m):
    segments=[e for e in m[1:] if e[0]=='data']
    if len(segments)!=1:raise ValueError('one data segment')
    return bytes().join(c.decode(x) for x in segments[0][1:] if isinstance(x,str) and x.startswith('"'))


def contract(m):
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=1:raise ValueError('one function')
    params=[v for x in fs[0][1:] if isinstance(x,list) and x[0]=='param' for v in x[1:]]
    if not params or any(v!='i32' for v in params) or (len(params)-1)%3:raise ValueError('parameters')
    return fs[0],len(params)


def profile(src,data,plan,mode):
    m=q.read(src)
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as td:
        raw=Path(td)/'raw.wasm';q.compile(render(data,plan,mode),raw)
        if q.read(raw)==m:return
        opt=Path(td)/'O3.wasm';q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',opt])
        if q.read(opt)!=m:raise ValueError('not a validated raw/O3 profile')


def source(src):
    m=q.read(src);f,n=contract(m);plan=[]
    for e in q.walk(f):
        if e[0]=='memory.copy':
            if len(e)!=4 or any(x[0]!='local.get' for x in e[1:]):raise ValueError('dynamic copy parameters')
            plan.append(tuple(int(x[1]) for x in e[1:]))
    data=data_of(m);profile(src,data,plan,'plain');return data,plan


def transform(src,dst):
    t=time.perf_counter();data,plan=source(src);q.compile(render(data,plan,'pullback'),dst)
    return dict(ms=(time.perf_counter()-t)*1000,copies=len(plan))


def extract(src):
    """Find the reversed range updates; never read the source or its plan."""
    m=q.read(src);f,n=contract(m);reversed_plan=[]
    env={i:('arg',i) for i in range(n)}
    extra=sum(len(x)-1 for x in f[1:] if isinstance(x,list) and x[0]=='local')
    env.update({n+i:('i32.const',0) for i in range(extra)})
    def choose(cond,yes,no):
        if yes==no:return yes
        if cond[0]=='i32.gt_u':cond=('i32.lt_u',cond[2],cond[1])
        if cond[0]=='i32.lt_u' and cond[1][0]=='i32.sub' and yes[0]=='i32.add':
            delta,length=cond[1:];value,d=delta[1:]
            if no==value and delta in yes[1:] and d[0]=='arg' and length[0]=='arg':
                src_=yes[2] if yes[1]==delta else yes[1]
                if src_[0]=='arg':
                    reversed_plan.append((d[1],src_[1],length[1]))
                    return ('mapped',value,d,src_,length)
        return ('if',cond,yes,no)
    def sequence(code,state,stack):
        for e in code:
            value=evaluate(e,state,stack)
            if value[0] not in ('void','trap'):stack.append(value)
    def evaluate(e,state,stack):
        op=e[0]
        if op=='local.get':return state[int(e[1])]
        if op in ('local.set','local.tee'):
            v=evaluate(e[2],state,stack) if len(e)==3 else stack.pop();state[int(e[1])]=v
            return v if op=='local.tee' else ('void',)
        if op in ('i32.const','i64.const'):return (op,int(e[1]))
        if op=='unreachable':return ('trap',)
        if op=='if':
            parts=e[1:]
            returns=parts[0][0]=='result'
            if returns:parts=parts[1:]
            cond=evaluate(parts[0],state,stack)  # left-to-right, including pending stack operands
            true_state=state.copy();false_state=state.copy()
            ts=stack[:];fs=stack[:];sequence(parts[1][1:],true_state,ts)
            if len(parts)==3:sequence(parts[2][1:],false_state,fs)
            yes=ts.pop() if returns else ('void',);no=fs.pop() if returns else ('void',)
            if len(ts)!=len(fs):raise ValueError('branch stack shape')
            stack[:]=[choose(cond,a,b) for a,b in zip(ts,fs)]
            for i in state:state[i]=choose(cond,true_state[i],false_state[i])
            return choose(cond,yes,no)
        if op in ('i32.add','i32.sub','i32.lt_u','i32.gt_u','i32.ge_u','i64.add','i64.gt_u','i64.extend_i32_u','i32.load8_u'):
            arity=1 if op in ('i64.extend_i32_u','i32.load8_u') else 2
            values=[evaluate(x,state,stack) for x in e[1:]];missing=arity-len(values)
            if missing:
                if len(stack)<missing:raise ValueError('missing stack operands')
                values=stack[-missing:]+values;del stack[-missing:]
            return (op,*values)
        raise ValueError('unsupported symbolic operation '+op)
    sequence([x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')],env,[])
    plan=list(reversed(reversed_plan));data=data_of(m)
    profile(src,data,plan,'pullback');return data,plan


def recover(src,dst):
    t=time.perf_counter();data,plan=extract(src);analysis=(time.perf_counter()-t)*1000
    q.compile(render(data,plan),dst)
    return dict(status='recovered',analysis_including_profile_ms=analysis,total_ms=(time.perf_counter()-t)*1000,copies=len(plan))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['transform','recover']);a.add_argument('source');a.add_argument('output');a=a.parse_args()
    print(json.dumps(transform(a.source,a.output) if a.command=='transform' else recover(a.source,a.output)))
