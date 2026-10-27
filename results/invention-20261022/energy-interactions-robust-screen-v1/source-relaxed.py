# -*- coding: utf-8 -*-
"""Revision gate: globally correct energy descent and public min-elimination.

This is an extension of energy-descent, not an independent invention claim.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

import prototype as p

ROOT = p.HERE.parents[1]
sys.path.insert(0, str(ROOT / '.tools/encoding-synthesis-python'))
import z3


def errors(I, gates, x, state):
    def v(a):
        return (x if a[0] == 'input' else state) >> a[1] & 1
    ops = {'and': lambda a,b:a&b, 'or':lambda a,b:a|b, 'xor':lambda a,b:a^b}
    return [(state >> i & 1) ^ ops[op](v(a),v(b)) for i,(op,a,b) in enumerate(gates)]


def symbolic(I, gates, weights):
    xs = z3.Bools(' '.join('x%d'%i for i in range(I)))
    zs = z3.Bools(' '.join('z%d'%i for i in range(len(gates))))
    def calc(state):
        def v(a):return (xs if a[0]=='input' else state)[a[1]]
        ops={'and':z3.And,'or':z3.Or,'xor':z3.Xor}
        es=[z3.Xor(state[i],ops[op](v(a),v(b))) for i,(op,a,b) in enumerate(gates)]
        return z3.Sum([z3.If(e,w,0) for e,w in zip(es,weights)]),es
    E,es=calc(zs)
    neighbors=[calc([z3.Not(a) if i==j else a for i,a in enumerate(zs)])[0] for j in range(len(gates))]
    return xs,zs,E,es,neighbors


def values(model, xs, zs):
    def bits(seq):return sum(int(z3.is_true(model.eval(a,model_completion=True)))<<i for i,a in enumerate(seq))
    return bits(xs),bits(zs)


def verify(I,gates,weights,timeout=15000):
    start=time.perf_counter();xs,zs,E,es,neighbors=symbolic(I,gates,weights)
    s=z3.Solver();s.set(timeout=timeout);s.add(E>0,*[v>=E for v in neighbors]);status=s.check()
    result={'status':str(status),'milliseconds':(time.perf_counter()-start)*1000}
    if status==z3.sat:
        x,state=values(s.model(),xs,zs);result['counterexample']={'x':x,'state':state,'errors':errors(I,gates,x,state)}
    elif status==z3.unknown:result['reason']=s.reason_unknown()
    result['smt2']=s.to_smt2()
    return result


def synthesize(I,gates,max_rounds=128):
    start=time.perf_counter();n=len(gates);weights=z3.Ints(' '.join('w%d'%i for i in range(n)))
    outer=z3.Optimize();outer.set(timeout=15000)
    # This finite search cap is a synthesis limit, not a protection property.
    outer.add(*[z3.And(w>=1,w<=65536) for w in weights]);outer.minimize(z3.Sum(weights))
    trace=[]
    for step in range(max_rounds):
        st=outer.check()
        if st!=z3.sat:return {'status':'outer-'+str(st),'trace':trace,'milliseconds':(time.perf_counter()-start)*1000}
        m=outer.model();ws=[m.eval(w).as_long() for w in weights];v=verify(I,gates,ws)
        trace.append({'weights':ws,**{k:a for k,a in v.items() if k!='smt2'}})
        if v['status']=='unsat':
            return {'status':'verified','weights':ws,'trace':trace,'smt2':v['smt2'],'milliseconds':(time.perf_counter()-start)*1000}
        if v['status']!='sat':return {'status':'inner-'+v['status'],'trace':trace,'milliseconds':(time.perf_counter()-start)*1000}
        c=v['counterexample'];x,state=c['x'],c['state'];before=c['errors']
        alternatives=[]
        for j in range(n):
            after=errors(I,gates,x,state^(1<<j))
            alternatives.append(z3.Sum([(b-a)*w for a,b,w in zip(before,after,weights)])<0)
        outer.add(z3.Or(alternatives))
    return {'status':'round-cap','trace':trace,'milliseconds':(time.perf_counter()-start)*1000}


def deviation(I,gates,weights):
    xs,zs,E,es,ns=symbolic(I,gates,weights);out={}
    for label,condition in [('strict',z3.Or(*[z3.Or(z3.And(e,q>E),z3.And(z3.Not(e),q<E)) for e,q in zip(es,ns)])),
                            ('tie',z3.Or(*[q==E for q in ns]))]:
        s=z3.Solver();s.set(timeout=15000);s.add(condition);st=s.check();r={'status':str(st)}
        if st==z3.sat:
            x,state=values(s.model(),xs,zs);r.update(x=x,state=state,errors=errors(I,gates,x,state),energy=s.model().eval(E).as_long(),neighbor_energies=[s.model().eval(q).as_long() for q in ns])
        elif st==z3.unknown:r['reason']=s.reason_unknown()
        out[label]=r
    return out


def build(I,gates,weights,gauge=True,seed=20261022):
    n=len(gates);order=list(range(n));flips=[0]*n;rng=random.Random(seed)
    if gauge:rng.shuffle(order);flips=[rng.randrange(2) for _ in range(n)]
    def var(a):
        if a[0]=='input':return {1<<a[1]:1}
        i=a[1];v={1<<(I+order[i]):1}
        return p.plus({0:1},p.scale(v,-1)) if flips[i] else v
    E={}
    for i,(op,a,b) in enumerate(gates):
        v=var(['gate',i]);f=p.boolean(op,var(a),var(b));err=p.plus(v,f,p.scale(p.product(v,f),-2))
        E=p.plus(E,p.scale(err,weights[i]))
    if sum(abs(c) for c in E.values())>=1<<62:raise ValueError('i64 coefficient bound')
    return {'inputs':I,'n':n,'output':order[-1],'flip':flips[-1],'terms':sorted(E.items())}


def render(record,probe=False):
    s=p.render(record)
    replacements=[('(local $t i32)','(local $t i32) (local $changed i32)'),
                  ('(loop $sweeps','(loop $sweeps (local.set $changed (i32.const 0))'),
                  ('(local.set $s (local.get $v))','(local.set $changed (i32.const 1)) (local.set $s (local.get $v))'),
                  (f'(br_if $sweeps (i32.lt_u (local.get $t) (i32.const {record["n"]})))','(br_if $sweeps (local.get $changed))')]
    if probe:
        replacements += [('(export "run") (param $x i32)','(export "run") (param $x i32) (param $initial i32)'),
                         ('(i32.shl (local.get $x)', '(i32.shl (local.get $initial)')]
    for old,new in replacements:
        if s.count(old)!=1:raise ValueError('Renderer anchor mismatch: '+old)
        s=s.replace(old,new)
    return s


def local_rule(E,j,total,cap=20):
    D={m^(1<<j):c for m,c in E.items() if m&(1<<j)}
    support=sorted({k for m in D for k in range(total) if m&(1<<k)})
    if len(support)>cap:return None
    truth=[];ties=0
    for a in range(1<<len(support)):
        state=sum(1<<k for q,k in enumerate(support) if a>>q&1)
        d=sum(c for m,c in D.items() if state&m==m);truth.append(int(d<0));ties+=d==0
    essential=[q for q in range(len(support)) if any(truth[a]!=truth[a^(1<<q)] for a in range(len(truth)) if not a>>q&1)]
    if len(essential)>5:return None
    args=[support[q] for q in essential]
    vals=[truth[sum(1<<q for t,q in enumerate(essential) if a>>t&1)] for a in range(1<<len(args))]
    coeff=vals[:]
    for bit in range(len(args)):
        for a in range(len(coeff)):
            if a>>bit&1:coeff[a]-=coeff[a^(1<<bit)]
    poly={sum(1<<k for q,k in enumerate(args) if a>>q&1):c for a,c in enumerate(coeff) if c}
    E0={m:c for m,c in E.items() if not m&(1<<j)}
    reduced=p.plus(E0,p.product(poly,D))
    return {'coordinate':j,'args':args,'truth':sum(t<<i for i,t in enumerate(vals)),
            'before_support':len(support),'rows':len(truth),'ties':ties,'reduced':reduced}


def eliminate(record):
    start=time.perf_counter();I,n=record['inputs'],record['n'];E=dict(record['terms']);pending=set(range(I,I+n));rules=[];work=0;trace=[]
    while pending:
        candidates=[]
        for j in sorted(pending):
            r=local_rule(E,j,I+n)
            if r is not None:candidates.append(r)
        if not candidates:raise ValueError('No coordinate fits the enumeration/rule caps')
        # Public greedy heuristic; no original graph, weights, or seed are used.
        r=min(candidates,key=lambda a:(len(a['reduced']),len(a['args']),a['coordinate']))
        work+=sum(a['rows'] for a in candidates)
        trace.append({'coordinate':r['coordinate'],'terms_before':len(E),'terms_after':len(r['reduced']),
                      'args':r['args'],'ties':r['ties'],'candidates':len(candidates)})
        E=r.pop('reduced');rules.append({k:v for k,v in r.items() if k not in ('rows','ties')});pending.remove(r['coordinate'])
    if E:raise ValueError('Residual minimum is not identically zero')
    return {'inputs':I,'n':n,'output':I+record['output'],'flip':record['flip'],'rules':list(reversed(rules)),
            'enumerated_candidate_rows':work,'trace':trace,'milliseconds':(time.perf_counter()-start)*1000}


def read_family(src,out):
    p.w.tool('wasm-validate',[src]);r=p.rawdata(p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs'])))
    family=Path(out).with_stem(Path(out).stem+'-family-check');p.save(render(r),family)
    if family.read_bytes()!=Path(src).read_bytes():
        opt=family.with_stem(family.stem+'-O3');p.w.tool('wasm-opt',[family,'-O3','-o',opt])
        if opt.read_bytes()!=Path(src).read_bytes():raise ValueError('Unsupported evaluator')
    return r


def recover(src,out):
    start=time.perf_counter();r=read_family(src,out);m=eliminate(r);p.save(p.recovered_wat(m),out)
    return {'milliseconds':(time.perf_counter()-start)*1000,'model':m,'family_checked':True}


def transform(src,out,mode='synth',gauge=True):
    start=time.perf_counter();I,gates=p.source(src)
    if mode=='synth':
        result=synthesize(I,gates)
        if result['status']!='verified':raise ValueError(json.dumps(result))
        weights=result['weights']
    elif mode=='dag':
        _,cert=p.build(I,gates,'dag',False);weights=cert['weights'];result={'status':'dominance-certified'}
    else:raise ValueError(mode)
    record=build(I,gates,weights,gauge);p.save(render(record),out)
    return {'milliseconds':(time.perf_counter()-start)*1000,'weights':weights,'synthesis':result,'record':record,
            'deviation':deviation(I,gates,weights)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['dag','synth'],default='synth');a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode) if a.action=='transform' else recover(a.source,a.output),indent=2))
