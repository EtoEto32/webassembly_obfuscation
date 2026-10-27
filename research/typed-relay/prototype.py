"""Typed shared-call relay gate. Known CPS-like mechanism, not a novelty claim."""
import argparse
from collections import deque
import copy
import importlib.util
import json
from pathlib import Path
import time

spec = importlib.util.spec_from_file_location('common', Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
FLAGS = ['--enable-function-references']
OPS = {'i32.add','i32.sub','i32.mul','i32.and','i32.or','i32.xor',
       'i32.shl','i32.shr_u','i32.shr_s','i32.rotl','i32.rotr'}
DECL = {'type','param','result','local','export'}


def nodes(x):
    if not isinstance(x,list): return
    yield x
    for c in x: yield from nodes(c)


def compile_wat(text,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() or path.with_suffix('.wat').exists(): raise FileExistsError(path)
    path.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[path.with_suffix('.wat'),*FLAGS,'-o',path])
    w.tool('wasm-validate',[path,*FLAGS])


def load(path):
    t=time.perf_counter()
    w.tool('wasm-validate',[path,*FLAGS])
    m=w.parse(w.tool('wasm2wat',[path,*FLAGS,'--fold-exprs','--no-debug-names']))
    return m,(time.perf_counter()-t)*1000


def body(f): return [x for x in f[1:] if isinstance(x,list) and x[0] not in DECL]
def decl(f,k): return [x for x in f[1:] if isinstance(x,list) and x[0]==k]


def check_module(m,source=False):
    allowed={'type','func','memory','export'} | (set() if source else {'elem'})
    if any(x[0] not in allowed for x in m[1:]): raise ValueError('Unsupported module section')
    fs=[x for x in m[1:] if x[0]=='func']
    if source and len(fs)!=1: raise ValueError('Source must have one function')
    if [x for x in m[1:] if x[0]=='memory'] != [['memory','1','1']]:
        raise ValueError('Exactly one fixed public memory required')
    ex=[x for x in m[1:] if x[0]=='export']
    run=[x for x in ex if x[1]=='"run"' and x[2][0]=='func']
    if len(ex)!=2 or len(run)!=1 or ['export','"memory"',['memory','0']] not in ex:
        raise ValueError('Only run and memory exports supported')
    entry=int(run[0][2][1]);f=fs[entry]
    if decl(f,'result')!=[['result','i32']]: raise ValueError('i32 result required')
    if any(t!='i32' for k in ('param','local') for x in decl(f,k) for t in x[1:]):
        raise ValueError('i32 arguments and locals required')
    if source:
        bad={'call','call_indirect','call_ref','return_call','return_call_ref','return_call_indirect',
             'memory.grow','global.get','global.set'}
        if any(x[0] in bad or str(x[0]).startswith(('table.','ref.')) for x in nodes(f)):
            raise ValueError('Source calls, globals, references or growing memory unsupported')
    return fs,entry


def transform(src,dst,mode='tail4'):
    t=time.perf_counter();m,_=load(src);fs,entry=check_module(m,True)
    used=sorted({x[0] for x in nodes(fs[entry]) if x[0] in OPS})
    if not used: raise ValueError('No supported binary expressions')
    op_type=sum(x[0]=='type' for x in m[1:]);relay_type=op_type+1
    leaves={op:1+i for i,op in enumerate(used)}
    depth=0 if mode=='ref' else int(mode[4:] if mode.startswith('tail') else mode[4:])
    if mode!='ref' and not (mode.startswith(('tail','call')) and 1<=depth<=64): raise ValueError(mode)
    first=1+len(used);count=0
    def visit(x):
        nonlocal count
        if not isinstance(x,list): return x
        if x[0] in OPS:
            if len(x)!=3 or not all(isinstance(c,list) for c in x[1:]):
                raise ValueError('Stack-based arithmetic is outside this folded-expression input subset')
            count+=1;a,b=map(visit,x[1:]);ref=['ref.func',str(leaves[x[0]])]
            return ['call_ref',str(op_type),a,b,ref] if mode=='ref' else ['call',str(first+depth-1),a,b,ref]
        return [visit(c) for c in x]
    newf=visit(fs[entry]);m[m.index(fs[entry])]=newf
    # Append type definitions: type/function index spaces are independent of section order in text.
    m.extend([['type',['func',['param','i32','i32'],['result','i32']]],
              ['type',['func',['param','i32','i32',['ref',str(op_type)]],['result','i32']]]])
    for op in used:
        m.append(['func',['type',str(op_type)],['param','i32','i32'],['result','i32'],
                  [op,['local.get','0'],['local.get','1']]])
    for j in range(depth):
        args=[['local.get',str(k)] for k in range(3)]
        tail=mode.startswith('tail')
        call=[('return_call_ref' if tail else 'call_ref'),str(op_type),*args] if j==0 else [
            ('return_call' if tail else 'call'),str(first+j-1),*args]
        m.append(['func',['type',str(relay_type)],['param','i32','i32',['ref',str(op_type)]],['result','i32'],call])
    m.append(['elem','declare','func',*map(str,leaves.values())])
    compile_wat(w.emit(m),dst)
    return dict(mode=mode,depth=depth,operators=used,sites=count,transform_ms=(time.perf_counter()-t)*1000)


def recover(m):
    """Verify pure helper summaries, substitute actual arguments, reconstruct module.

    Neither source nor generator metadata is used. Unknown helpers fail closed.
    Summary forms are operator(a,b) or call_ref(formal_ref,a,b).
    """
    t=time.perf_counter();fs,entry=check_module(m);cache={};visiting=set();visits=0
    def summary(i):
        nonlocal visits
        if i in cache:return cache[i]
        if i==entry or i in visiting:raise ValueError('Recursive/unproved helper')
        visiting.add(i);f=fs[i];b=body(f);visits+=1
        params=[a for x in decl(f,'param') for a in x[1:]]
        if decl(f,'local') or decl(f,'result')!=[['result','i32']] or len(b)!=1:
            raise ValueError('Helper has locals, effects, or an unsupported body')
        def get(x):
            if not isinstance(x,list) or x[0]!='local.get' or len(x)!=2:raise ValueError('Nonformal helper operand')
            n=int(x[1])
            if not 0<=n<len(params):raise ValueError('Bad formal operand')
            return n
        x=b[0]
        if x[0] in OPS and len(x)==3 and params==['i32','i32']:
            s=('op',x[0],get(x[1]),get(x[2]))
        elif x[0] in ('call_ref','return_call_ref') and len(x)==5 and len(params)==3:
            a,b,r=map(get,x[2:]);types=[z for z in m[1:] if z[0]=='type']
            ot=int(x[1]);expected=['type',['func',['param','i32','i32'],['result','i32']]]
            if types[ot]!=expected or params[a]!='i32' or params[b]!='i32' or params[r]!=['ref',str(ot)]:
                raise ValueError('Unproved reference/type signature')
            s=('ref',r,a,b)
        elif x[0] in ('call','return_call'):
            callee=summary(int(x[1]));indices=list(map(get,x[2:]))
            # Validated Wasm already checks arity and actual parameter types.
            s=(callee[0],callee[1],indices[callee[2]],indices[callee[3]]) if callee[0]=='op' else (
                'ref',indices[callee[1]],indices[callee[2]],indices[callee[3]])
        else:raise ValueError('Unproved helper instruction: '+str(x[0]))
        visiting.remove(i);cache[i]=s;return s
    replacements=0;bound_targets={}
    def apply(s,args,site):
        if s[0]=='op':
            if list(s[2:])!=list(range(len(args))):raise ValueError('Nonlinear or reordered leaf operands')
            return [s[1],args[s[2]],args[s[3]]]
        r=args[s[1]]
        if not isinstance(r,list) or r[0]!='ref.func' or len(r)!=2:raise ValueError('Nonconstant reference at source call')
        j=int(r[1]);bound_targets.setdefault(site,set()).add(j)
        leaf=summary(j)
        if leaf[0]!='op':raise ValueError('Reference does not target a proved operator')
        return apply(leaf,[args[s[2]],args[s[3]]],('indirect',j))
    def visit(x):
        nonlocal replacements
        if not isinstance(x,list):return x
        if x[0] in ('call','return_call'):
            if x[0]=='return_call':raise ValueError('Entry tail call not supported by this gate')
            s=summary(int(x[1]));args=list(map(visit,x[2:]));replacements+=1
            # Helpers must use arguments exactly once and in source order. Otherwise
            # substitution could drop/reorder trapping or side-effecting expressions.
            used=list(s[2:]) if s[0]=='op' else list(s[2:])+[s[1]]
            if used!=list(range(len(args))):raise ValueError('Nonlinear or reordered actual operands')
            return apply(s,args,int(x[1]))
        if x[0]=='call_ref':
            if len(x)!=5:raise ValueError('Unsupported call_ref arity')
            args=list(map(visit,x[2:]));replacements+=1
            return apply(('ref',2,0,1),args,('direct',str(x[1])))
        return [visit(a) for a in x]
    entryf=visit(fs[entry]);
    # Verify every extra function, including helpers no longer reached after optimization.
    for i in range(len(fs)):
        if i!=entry:summary(i)
    if any(x[0] in ('ref.func','call_ref','return_call_ref','call','return_call') for x in nodes(entryf)):
        raise ValueError('Residual reference or helper call')
    out=['module']
    for x in m[1:]:
        if x[0] in ('func','elem'):continue
        y=copy.deepcopy(x)
        if y[0]=='export' and y[2][0]=='func':y[2][1]='0'
        out.append(y)
    out.append(entryf)
    return dict(module=out,analysis_ms=(time.perf_counter()-t)*1000,helper_summaries=visits,
                replacements=replacements,target_sets={str(k):sorted(v) for k,v in bound_targets.items()})


def reference_flow(m,k):
    """Finite call-string analysis of reference arguments for this restricted gate.

    All syntactic calls are considered reachable. Numeric/path constraints are
    ignored. Ref operands must be constants or formals, not heap-loaded values.
    This is not a whole-Wasm points-to analyzer or an implementation of Lu's CFA.
    """
    t=time.perf_counter();fs,entry=check_module(m)
    params=[[a for d in decl(f,'param') for a in d[1:]] for f in fs]
    calls=[[(i,x) for i,x in enumerate(nodes(f)) if x[0] in ('call','return_call','call_ref','return_call_ref')] for f in fs]
    states={(entry,()):[set() for _ in params[entry]]};queue=deque([(entry,())]);pending={(entry,())};targets={};steps=0
    while queue:
        key=queue.popleft();pending.discard(key);fi,context=key;env=states[key];steps+=1
        def refs(x):
            if x[0]=='ref.func':return {int(x[1])}
            if x[0]=='local.get':
                n=int(x[1]);return env[n] if n<len(env) else set()
            return set()
        for si,x in calls[fi]:
            site=(fi,si);ctx=(context+(site,))[-k:] if k else ()
            if x[0] in ('call','return_call'):
                callees={int(x[1])};args=x[2:]
            else:
                callees=refs(x[-1]);args=x[2:-1]
                targets.setdefault((fi,context,si),set()).update(callees)
            for callee in callees:
                ck=(callee,ctx);fresh=ck not in states
                if fresh:states[ck]=[set() for _ in params[callee]]
                changed=fresh
                for i,arg in enumerate(args):
                    vs=refs(arg);old=len(states[ck][i]);states[ck][i].update(vs)
                    changed=changed or len(states[ck][i])!=old
                if changed and ck not in pending:queue.append(ck);pending.add(ck)
    sizes=[len(v) for v in targets.values()]
    return dict(k=k,contexts=len(states),worklist_steps=steps,indirect_contexts=len(sizes),
                max_targets=max(sizes,default=0),ambiguous_contexts=sum(x>1 for x in sizes),
                total_target_facts=sum(sizes),analysis_ms=(time.perf_counter()-t)*1000)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('src',type=Path)
    ap.add_argument('dst',type=Path);ap.add_argument('--mode',default='tail4',choices=['ref','tail1','tail4','tail8','call4'])
    a=ap.parse_args()
    if a.action=='transform':r=transform(a.src,a.dst,a.mode)
    else:
        m,parse=load(a.src);r=recover(m);compile_wat(w.emit(r.pop('module')),a.dst);r['parse_validate_ms']=parse
    print(json.dumps(r))


if __name__=='__main__':main()
