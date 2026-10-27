"""Restricted .wasm DFA scanner to source-certified NFA; no novelty claim.

The raw-binary recovery uses only the input Wasm, never the source DFA, merge
history or generator seed. Exact re-emission checks the supported template.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import model as m

spec=importlib.util.spec_from_file_location('suffix_common',Path(__file__).resolve().parents[1]/'suffix-transport/prototype.py')
s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
w=s.w


def dfa_wat(d):
    if d.n>16 or d.start!=0:raise ValueError('DFA source needs <=16 states, start 0')
    return s.plain([[row[a] for row in d.trans]+[0]*(16-d.n) for a in range(2)],d.final)


def fold_or(xs):
    if not xs:return '(i64.const 0)'
    if len(xs)==1:return xs[0]
    h=len(xs)//2
    return '(i64.or '+fold_or(xs[:h])+' '+fold_or(xs[h:])+')'


def nfa_wat(n):
    if not 1<=n.n<=64:raise ValueError('Backend supports 1..64 NFA states')
    terms=[]
    for i,row in enumerate(n.trans):
        # Keep both alphabet alternatives; optimization is measured separately.
        mask=f'(select (i64.const {s.signed64(row[1])}) (i64.const {s.signed64(row[0])}) (local.get 3))'
        active=f'(i64.ne (i64.and (local.get 4) (i64.const {s.signed64(1<<i)})) (i64.const 0))'
        terms.append(f'(select {mask} (i64.const 0) {active})')
    return f'''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32) (result i32) (local i32 i32 i64)
        (local.set 4 (i64.const {s.signed64(n.initial)}))
        (block (loop
          (br_if 1 (i32.ge_u (local.get 2) (local.get 1)))
          (local.set 3 (i32.and (i32.load8_u (i32.add (local.get 0) (local.get 2))) (i32.const 1)))
          (local.set 4 {fold_or(terms)})
          (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0)))
        (i64.ne (i64.and (local.get 4) (i64.const {s.signed64(n.final)})) (i64.const 0))))'''


def exact_template(program,wat,parent,opt='raw'):
    with tempfile.TemporaryDirectory(prefix='template-',dir=parent) as td:
        target=Path(td)/'expected.wasm';s.compile_wat(wat,target)
        if opt!='raw':
            optimized=Path(td)/'optimized.wasm';w.tool('wasm-opt',[target,'-'+opt,'-o',optimized]);target=optimized
        if s.read(target)['module']!=program['module']:
            raise ValueError('Input does not match the verified scanner template')


def source_dfa(program,parent):
    delta,final=s.source_model(program);exact_template(program,s.plain(delta,final),parent)
    delta,final=s.canonical(delta,final)
    return m.DFA(list(map(list,zip(*delta))),final)


def transform(src,dst,mode,seed=20261018,guard=3,rounds=12):
    started=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    program=s.read(src);d=source_dfa(program,dst.parent)
    n=m.trim(m.lift(d,m.universal(guard)));generation=dict(rounds=0,ms=0)
    if mode!='lift':n,generation=m.choose_merges(d,n,rounds,seed,mode)
    cert=m.certificate(d,n);assert cert['valid']
    s.compile_wat(nfa_wat(n),dst)
    return dict(mode=mode,seed=seed,guard=guard,source_sha256=hashlib.sha256(Path(src).read_bytes()).hexdigest(),
                transform_ms=(time.perf_counter()-started)*1000,dfa=asdict(d),nfa=asdict(n),certificate=cert,generation=generation)


def const(x):
    if x[0]!='i64.const':raise ValueError('Expected constant')
    return int(x[1])&((1<<64)-1)


def extract_raw(program,parent):
    """A syntactic parser followed by a full-template check, not finite probes."""
    if program['types']==['i32']*5:
        delta,final=s.source_model(program)
        exact_template(program,s.plain(delta,final),parent)
        delta,final=s.canonical(delta,final)
        return m.from_dfa(m.DFA(list(map(list,zip(*delta))),final))
    if program['types']!=['i32','i32','i32','i32','i64']:raise ValueError('Unsupported local types')
    body=program['body'];initial=const(body[0][2]);final=const(body[-1][1][2])
    updates=[x for node in body for x in s.descendants(node) if x[:2]==['local.set','4']]
    if len(updates)!=2:raise ValueError('Expected initialization and one state update')
    terms=[]
    def flatten(x):
        if x[0]=='i64.or':flatten(x[1]);flatten(x[2])
        else:terms.append(x)
    flatten(updates[1][2]);rows=[]
    for i,x in enumerate(terms):
        if x[0]!='select' or x[1][0]!='select':raise ValueError('Expected state and symbol selections')
        rows.append([const(x[1][2]),const(x[1][1])])
        active=x[3]
        if active!=['i64.ne',['i64.and',['local.get','4'],['i64.const',str(s.signed64(1<<i))]],['i64.const','0']]:
            raise ValueError('Unexpected active-state predicate')
    n=m.NFA(rows,initial,final)
    if max([initial,final]+[x for row in rows for x in row])>=1<<n.n:raise ValueError('Out-of-range bit')
    exact_template(program,nfa_wat(n),parent)
    return n


# A bit is an OR of input state bits, or the constant one (bit 64). This
# restricted algebra rejects conjunctions of two different state variables.
ONE=1<<64


def symbolic_extract(program,parent):
    types=program['types'];body=program['body']
    sets=[x for node in body for x in s.descendants(node) if x[0]=='local.set']
    carriers=[i for i,t in enumerate(types) if t=='i64' and sum(int(x[1])==i for x in sets)==2]
    if len(carriers)!=1:raise ValueError('One initialized and updated i64 state required')
    state=carriers[0];assigns=[x for x in sets if int(x[1])==state]
    initial=const(assigns[0][2]);step=assigns[1][2]
    def value(x,width):return tuple(ONE if (x>>i)&1 else 0 for i in range(width))
    def concrete(x):
        if any(v not in (0,ONE) for v in x):raise ValueError('Nonconstant value')
        return sum((v==ONE)<<i for i,v in enumerate(x))
    def disjoin(a,b):return ONE if ONE in (a,b) else a|b
    def conjoin(a,b):
        if not a or not b:return 0
        if a==ONE:return b
        if b==ONE or a==b:return a
        raise ValueError('Nonlinear state-bit conjunction')
    def evaluate(expr,letter):
        env=[value(0,64 if t=='i64' else 32) for t in types]
        env[state]=tuple(1<<i for i in range(64))
        # The raw symbol assignment is outside the update expression. In
        # optimized forms it is a local.tee evaluated inside the expression.
        loads=[x for node in body for x in s.descendants(node) if x[0] in ('local.set','local.tee')
               and any(y[0]=='i32.load8_u' for y in s.descendants(x[2])) and int(x[1])!=state]
        def ev(x):
            op=x[0];width=64 if op.startswith('i64.') else 32
            if op in ('i32.const','i64.const'):return value(int(x[1]),width)
            if op=='local.get':return env[int(x[1])]
            if op in ('local.set','local.tee'):
                v=ev(x[2]);env[int(x[1])]=v;return v
            if op=='i32.load8_u':return value(letter,32)
            if op=='select':
                a,b,c=[ev(y) for y in x[1:]]
                try:return a if concrete(c) else b
                except ValueError:pass
                condition=0
                for bit in c:condition=disjoin(condition,bit)
                if all(bit==0 for bit in b):return tuple(conjoin(bit,condition) for bit in a)
                raise ValueError('Unsupported symbolic selection')
            args=[ev(y) for y in x[1:] if isinstance(y,list)]
            if op in ('i64.and','i32.and','i64.or','i32.or'):
                fn=conjoin if op.endswith('and') else disjoin
                return tuple(fn(a,b) for a,b in zip(*args))
            if op=='i32.wrap_i64':return args[0][:32]
            if op=='i64.extend_i32_u':return args[0]+(0,)*32
            if op in ('i64.ne','i32.ne') and all(b==0 for b in args[1]):
                bit=0
                for a in args[0]:bit=disjoin(bit,a)
                return (bit,)+(0,)*31
            raise ValueError('Unsupported transition opcode '+op)
        for x in loads:ev(x)
        return ev(expr)
    columns=[]
    for letter in (0,1):
        output=evaluate(step,letter)
        if any(v&ONE for v in output):raise ValueError('Nonzero affine constant in transition')
        columns.append([m.union(1<<j for j,v in enumerate(output) if (v>>i)&1) for i in range(64)])
    # The return predicate must have the direct nonzero(mask & state) form;
    # complete template comparison below also checks the rest of the program.
    out=body[-1]
    if out[0]!='i64.ne' or out[1][0]!='i64.and' or out[1][1]!=['local.get',str(state)] or const(out[2])!=0:
        raise ValueError('Unsupported final-state predicate')
    final=const(out[1][2]);used=initial|final
    for i in range(64):
        if columns[0][i] or columns[1][i]:used|=1<<i|columns[0][i]|columns[1][i]
    n=m.NFA([[columns[a][i] for a in (0,1)] for i in range(max(1,used.bit_length()))],initial,final)
    errors=[]
    for opt in ('raw','O2','O3'):
        try:exact_template(program,nfa_wat(n),parent,opt);return n,opt
        except ValueError as e:errors.append(str(e))
    raise ValueError('No matching raw/O2/O3 full-program template')


def extract(program,parent):
    try:return extract_raw(program,parent),'raw'
    except (ValueError,IndexError,TypeError):pass
    if any(t=='i64' for t in program['types']):return symbolic_extract(program,parent)
    # Plain optimized scanner: extract its finite table and verify the exact
    # regenerated compiler output; finite probes alone are not the proof.
    delta,final=s.scanner_model(program)
    for opt in ('O2','O3'):
        try:
            exact_template(program,s.plain(delta,final),parent,opt)
            delta,final=s.canonical(delta,final)
            return m.from_dfa(m.DFA(list(map(list,zip(*delta))),final)),opt
        except ValueError:pass
    raise ValueError('Unsupported optimized scanner template')


def attack(n,method,limit=100000):
    t=time.perf_counter();source=m.bisimulation(n) if method=='bisimulation' else m.simulation(n) if method=='simulation' else m.reverse(n) if method=='reverse' else n
    d,report=m.determinize(source,limit)
    report['reduced_nfa_states']=source.n
    if d is not None:
        d=m.minimize(d)
        if method=='reverse':
            d,r=m.determinize(m.reverse(m.from_dfa(d)),limit);report['second_states']=r['states']
            if d is not None:d=m.minimize(d)
            else:report['status']=r['status']
        if d is not None:
            # Canonical BFS numbers are needed by the source-code emitter.
            delta,final=s.canonical([[row[a] for row in d.trans] for a in range(2)],d.final,d.start)
            d=m.DFA(list(map(list,zip(*delta))),final);report['minimal_states']=d.n
    report.update(method=method,analysis_ms=(time.perf_counter()-t)*1000)
    return d,report


def recover(src,dst,method='subset'):
    t=time.perf_counter();program=s.read(src);parse=program['parse_validate_ms']
    n,opt=extract(program,Path(dst).resolve().parent);extract_ms=(time.perf_counter()-t)*1000-parse
    d,report=attack(n,method)
    if d is None:return report
    s.compile_wat(dfa_wat(d),dst)
    report.update(parse_validate_ms=parse,extract_verify_ms=extract_ms,nfa_states=n.n,template=opt)
    return report


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    tr=sub.add_parser('transform');tr.add_argument('src',type=Path);tr.add_argument('dst',type=Path)
    tr.add_argument('--mode',choices=['lift','random','overlap'],default='overlap');tr.add_argument('--seed',type=int,default=20261018)
    tr.add_argument('--guard',type=int,default=3);tr.add_argument('--rounds',type=int,default=12)
    rec=sub.add_parser('recover');rec.add_argument('src',type=Path);rec.add_argument('dst',type=Path)
    rec.add_argument('--method',choices=['subset','bisimulation','simulation','reverse'],default='subset')
    a=ap.parse_args()
    result=transform(a.src,a.dst,a.mode,a.seed,a.guard,a.rounds) if a.cmd=='transform' else recover(a.src,a.dst,a.method)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
