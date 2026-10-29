"""Actual Wasm transform for a fixed four-state polynomial scanner family."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import algebra as a

spec=importlib.util.spec_from_file_location('carrier_common',Path(__file__).resolve().parents[1]/'suffix-transport/prototype.py')
s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
w=s.w


def i32(x):return x if x<1<<31 else x-(1<<32)
def sum_expr(terms,op,zero):
    if not terms:return zero
    if len(terms)==1:return terms[0]
    k=len(terms)//2;return '('+op+' '+sum_expr(terms[:k],op,zero)+' '+sum_expr(terms[k:],op,zero)+')'
def poly_expr(p,variables):
    terms=[]
    for k,c in sorted(p.items()):
        factors=[variables[i] for i in k]
        if c!=1 or not factors:factors.insert(0,f'(i32.const {i32(c)})')
        terms.append(sum_expr(factors,'i32.mul','(i32.const 1)'))
    return sum_expr(terms,'i32.add','(i32.const 0)')
def vector_expr(f,local):
    variables=[f'(i32x4.extract_lane {i} (local.get {local}))' for i in range(4)]+['(local.get 3)']
    terms=[]
    for k in sorted(set().union(*(set(p) for p in f))):
        monomial=poly_expr({k:1},variables);coeff=' '.join(str(i32(p.get(k,0))) for p in f)
        terms.append(f'(i32x4.mul (v128.const i32x4 {coeff}) (i32x4.splat {monomial}))')
    return sum_expr(terms,'i32x4.add','(v128.const i32x4 0 0 0 0)')
def linear_map(matrix,local):return vector_expr([a.dot(row,[a.var(i) for i in range(4)]) for row in matrix],local)


def scalar_wat(f):
    variables=[f'(local.get {4+i})' for i in range(4)]+['(local.get 3)']
    step=' '.join(f'(local.set {8+i} {poly_expr(p,variables)})' for i,p in enumerate(f))
    step+=' '+' '.join(f'(local.set {4+i} (local.get {8+i}))' for i in range(4))
    return f'''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32) (result i32) (local i32 i32 i32 i32 i32 i32 i32 i32 i32 i32)
        (block (loop (br_if 1 (i32.ge_u (local.get 2) (local.get 1)))
          (local.set 3 (i32.load8_u (i32.add (local.get 0) (local.get 2))))
          {step}
          (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (local.get 4)))'''


def vector_wat(f,mode,matrix):
    inv=a.inverse(matrix);p,c=a.conjugate(f,matrix)
    if mode=='identity':p,c=f,[1,0,0,0]
    if mode=='decode':
        step=f'(local.set 5 {linear_map(inv,4)}) (local.set 5 {vector_expr(f,5)}) (local.set 4 {linear_map(matrix,5)})'
    else:step=f'(local.set 4 {vector_expr(p,4)})'
    output=poly_expr(a.dot(c,[a.var(i) for i in range(4)]),[f'(i32x4.extract_lane {i} (local.get 4))' for i in range(4)])
    return f'''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32) (result i32) (local i32 i32 v128 v128)
        (block (loop (br_if 1 (i32.ge_u (local.get 2) (local.get 1)))
          (local.set 3 (i32.load8_u (i32.add (local.get 0) (local.get 2))))
          {step}
          (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) {output}))'''


class PolynomialMachine:
    def __init__(self,types,carrier):
        self.env=[([{} for _ in range(4)] if t=='v128' else {}) for t in types]
        if isinstance(carrier,int):self.env[carrier]=[a.var(i) for i in range(4)]
        else:
            for i,j in enumerate(carrier):self.env[j]=a.var(i)
    def ev(self,x):
        op=x[0]
        if op=='i32.const':return a.const(int(x[1],0))
        if op=='local.get':return self.env[int(x[1])]
        if op in ('local.set','local.tee'):
            v=self.ev(x[2]);self.env[int(x[1])]=v;return v
        if op=='i32.load8_u':return a.var(4)
        if op=='v128.const':
            shape=x[1];width=int(shape[1:shape.index('x')]);raw=b''.join((int(v,0)&((1<<width)-1)).to_bytes(width//8,'little') for v in x[2:])
            return [a.const(int.from_bytes(raw[i:i+4],'little')) for i in range(0,16,4)]
        args=[self.ev(y) for y in x[1:] if isinstance(y,list)]
        if op=='i32x4.splat':return [args[0]]*4
        if op=='i32x4.extract_lane':return args[0][int(x[1])]
        if op=='i32x4.replace_lane':
            out=list(args[0]);out[int(x[1])]=args[1];return out
        if op=='i8x16.shuffle':
            indices=list(map(int,x[1:17]));out=[];both=args[0]+args[1]
            for i in range(0,16,4):
                j=indices[i]
                if j%4 or indices[i:i+4]!=list(range(j,j+4)):raise ValueError('Non-word shuffle')
                out.append(both[j//4])
            return out
        if op in ('i32.add','i32.sub','i32.mul','i32x4.add','i32x4.sub','i32x4.mul'):
            fn={'add':a.add,'sub':lambda x,y:a.add(x,a.scale(y,-1)),'mul':a.mul}[op.split('.')[1]]
            return [fn(x,y) for x,y in zip(*args)] if op.startswith('i32x4') else fn(*args)
        if op in ('i32.shl','i32x4.shl'):
            if any(k for k in args[1]):raise ValueError('Nonconstant shift')
            c=1<<(args[1].get((),0)&31)
            return [a.scale(p,c) for p in args[0]] if op.startswith('i32x4') else a.scale(args[0],c)
        raise ValueError('Unsupported polynomial opcode '+op)


def scanner_control(program):
    body=program['body'];loads=[x for node in body for x in s.descendants(node) if x[0]=='i32.load8_u']
    if len(loads)!=1 or len(loads[0])!=2:raise ValueError('One unoffset byte load required')
    address=loads[0][1]
    if address[0]!='i32.add' or len(address)!=3 or any(x[0]!='local.get' for x in address[1:]):raise ValueError('Load address')
    ids=[int(x[1]) for x in address[1:]]
    if 0 not in ids:raise ValueError('Pointer argument missing')
    counter=next(i for i in ids if i!=0)
    if counter<2:raise ValueError('Counter local')
    assignments=[x for node in body for x in s.descendants(node) if x[0] in ('local.set','local.tee')]
    if any(int(x[1])<2 for x in assignments):raise ValueError('Input argument mutation')
    updates=[x for x in assignments if int(x[1])==counter]
    expected=['local.set',str(counter),['i32.add',['local.get',str(counter)],['i32.const','1']]]
    if updates!=[expected]:raise ValueError('Counter update')
    if len(body)!=2:raise ValueError('Unexpected initialization or suffix effects')
    top=body[0];guard=['i32.ge_u',['local.get',str(counter)],['local.get','1']]
    if top[0]=='block' and len(top)==2 and top[1][0]=='loop':
        sequence=top[1][1:]
        if sequence[0]!=['br_if','1',guard] or sequence[-1]!=['br','0']:raise ValueError('Raw loop guard')
        statements=sequence[1:-1]
    elif top[0]=='loop' and len(top)==2 and top[1][0]=='if':
        node=top[1];condition=['i32.eqz',['i32.le_u',['local.get','1'],['local.get',str(counter)]]]
        if len(node)!=3 or node[1]!=condition or node[2][0]!='then' or node[2][-1]!=['br','1']:raise ValueError('Optimized loop guard')
        statements=node[2][1:-1]
    else:raise ValueError('Unsupported loop control')
    if any(x[0]!='local.set' for x in statements):raise ValueError('Unexpected body side effect')
    # Expression whitelist prevents calls, writes, nested branches and extra
    # loads from being hidden under assignments or the returned expression.
    allowed={'local.get','local.set','local.tee','i32.const','v128.const','i32.add','i32.sub','i32.mul','i32.shl',
             'i32x4.add','i32x4.sub','i32x4.mul','i32x4.shl','i32x4.splat','i32x4.extract_lane','i32x4.replace_lane','i8x16.shuffle','i32.load8_u'}
    for root in statements+[body[-1]]:
        if any(x[0] not in allowed for x in s.descendants(root)):raise ValueError('Unsupported expression/effect')
    if any(x[0] in ('local.set','local.tee','i32.load8_u') for x in s.descendants(body[-1])):raise ValueError('Impure observation')
    return statements,counter


def extract(program):
    """One loop update in the generated family; complete structural validation
    is separate. An extracted model alone is not a semantic proof of any Wasm."""
    statements,counter=scanner_control(program)
    loops=[x for node in program['body'] for x in s.descendants(node) if x[0]=='loop']
    if len(loops)!=1:raise ValueError('One loop required')
    vectors=[i for i,t in enumerate(program['types']) if t=='v128']
    writes=[x for x in s.descendants(loops[0]) if x[0]=='local.set']
    if vectors:
        # State is the vector visible in the final observation, after the loop.
        observed={int(x[1]) for x in s.descendants(program['body'][-1]) if x[0]=='local.get' and int(x[1]) in vectors}
        if len(observed)!=1:raise ValueError('One observed carried vector required')
        carrier=observed.pop()
    else:
        written=set();live=set()
        def visit(x):
            if x[0]=='local.get':
                i=int(x[1])
                if i not in written:live.add(i)
            else:
                for y in x[1:]:
                    if isinstance(y,list):visit(y)
                if x[0] in ('local.set','local.tee'):written.add(int(x[1]))
        for x in statements:visit(x)
        carrier=sorted(live-{0,1,counter})
        if len(carrier)!=4:raise ValueError('Four carried scalar states required')
    machine=PolynomialMachine(program['types'],carrier)
    output=machine.ev(program['body'][-1]);before=dict(output)
    # Only assignment roots, avoiding nested tees being applied out of order.
    def assignments(x):
        if x[0]=='local.set':yield x;return
        for y in x[1:]:
            if isinstance(y,list):yield from assignments(y)
    for x in statements:
        # The loop counter update is irrelevant to the state polynomial.
        if x[2][0]=='i32.add' and any(y==['i32.const','1'] for y in x[2][1:]) and int(x[1]) not in (carrier if isinstance(carrier,list) else [carrier]):
            # Do not skip polynomial temporaries containing +1.
            if x[2][1]==['local.get',x[1]]:continue
        machine.ev(x)
    f=machine.env[carrier] if isinstance(carrier,int) else [machine.env[i] for i in carrier]
    if any(len(k)!=1 or k[0]>=4 for k in before):raise ValueError('Observation must be linear in state')
    c=[before.get((i,),0) for i in range(4)]
    return f,c


def source(src,parent):
    program=s.read(src)
    if program['types']!=['i32']*12:raise ValueError('Exact scalar source family required')
    f,c=extract(program)
    if c!=[1,0,0,0] or any(len(k)>2 for p in f for k in p):raise ValueError('Source degree or observation')
    with tempfile.TemporaryDirectory(prefix='template-',dir=parent) as td:
        expected=Path(td)/'expected.wasm';s.compile_wat(scalar_wat(f),expected)
        if s.read(expected)['module']!=program['module']:raise ValueError('Source template mismatch')
    return f


def transform(src,dst,mode,seed=20261018):
    t=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);f=source(src,dst.parent)
    matrix=a.basis(seed);s.compile_wat(vector_wat(f,mode,matrix),dst);p,c=a.conjugate(f,matrix)
    return dict(mode=mode,seed=seed,transform_ms=(time.perf_counter()-t)*1000,matrix=matrix,
                source=a.serial(f),expanded=a.serial(p),observation=c,source_terms=sum(map(len,f)),expanded_terms=sum(map(len,p)))


def recover(src,dst):
    t=time.perf_counter();program=s.read(src);f,c=extract(program);parse=(time.perf_counter()-t)*1000;t=time.perf_counter()
    recovered,report=a.observe_recover(f,c);method='linear_preimage'
    if recovered is None:recovered,report=a.factor_recover(f,c);method='known_factor'
    report.update(method=method,extract_ms=parse,analysis_ms=(time.perf_counter()-t)*1000)
    if recovered is not None:s.compile_wat(scalar_wat(recovered),dst)
    return report


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    tr=sub.add_parser('transform');tr.add_argument('src',type=Path);tr.add_argument('dst',type=Path);tr.add_argument('--mode',choices=['identity','decode','fused'],default='fused');tr.add_argument('--seed',type=int,default=20261018)
    rec=sub.add_parser('recover');rec.add_argument('src',type=Path);rec.add_argument('dst',type=Path)
    x=ap.parse_args();print(json.dumps(transform(x.src,x.dst,x.mode,x.seed) if x.cmd=='transform' else recover(x.src,x.dst),indent=2))


if __name__=='__main__':main()
