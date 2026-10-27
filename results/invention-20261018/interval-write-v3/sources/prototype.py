"""Byte comparison -> private bulk-memory updates; binary-only read-over-write recovery."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

spec = importlib.util.spec_from_file_location('common', Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
REFERENCE_TABLE = bytes(int(a<b) for a in range(256) for b in range(256))


def c(x): return ['i32.const', str(x)]
def var(i): return ['local.get', str(i)]
def byte(i): return ['i32.and', var(i), c(255)]
def lt(a, b): return ['i32.lt_u', byte(a), byte(b)]


def compile_wat(text, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.with_suffix('.wat').exists():
        raise FileExistsError(path)
    path.with_suffix('.wat').write_text(text, encoding='utf-8')
    w.tool('wat2wasm', [path.with_suffix('.wat'), '-o', path])
    w.tool('wasm-validate', [path])


def load(path):
    started = time.perf_counter()
    w.tool('wasm-validate', [path])
    m = w.parse(w.tool('wasm2wat', [path, '--fold-exprs', '--no-debug-names']))
    return m, (time.perf_counter()-started)*1000


def module(n, expression, private=False, data=None, prefix=()):
    m = ['module', ['memory', ['export', '"memory"'], '1', '1']]
    if private: m.append(['memory', '1', '1'])
    if data is not None: m.append(['data', ['memory', '1'], c(0), '"'+''.join('\\%02x'%x for x in data)+'"'])
    m.append(['func', ['export', '"run"'], ['param']+['i32']*n, ['result', 'i32'], *prefix, expression])
    return w.emit(m)


def fields(m):
    if any(x[0] not in ('type','memory','func','export','data') for x in m[1:]):
        raise ValueError('Unsupported module section')
    funcs = [x for x in m[1:] if x[0]=='func']
    memories = [x for x in m[1:] if x[0]=='memory']
    exports = [x for x in m[1:] if x[0]=='export']
    if len(funcs)!=1 or not 1<=len(memories)<=2 or any(x!=['memory','1','1'] for x in memories):
        raise ValueError('One pure function and fixed memories required')
    if sorted(exports)!=sorted([['export','"run"',['func','0']], ['export','"memory"',['memory','0']]]):
        raise ValueError('Exact public exports required')
    f=funcs[0]
    params=[t for x in f[1:] if isinstance(x,list) and x[0]=='param' for t in x[1:]]
    locals_=[t for x in f[1:] if isinstance(x,list) and x[0]=='local' for t in x[1:]]
    if not 1<=len(params)<=64 or any(t!='i32' for t in params+locals_):
        raise ValueError('i32 arguments/locals required')
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='result'] != [['result','i32']]:
        raise ValueError('i32 result required')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','local','result')]
    return len(params),len(locals_),body,len(memories)


def input_tree(m):
    n,l,body,mem=fields(m)
    if l or mem!=1 or len(body)!=1 or any(x[0]=='data' for x in m[1:]):
        raise ValueError('Source must be one pure expression without data')
    def arg(x):
        for i in range(n):
            if x==byte(i): return i
        raise ValueError('Comparison operands must be masked parameters')
    def visit(x):
        if x[0]=='i32.lt_u': return ('lt',arg(x[1]),arg(x[2]))
        if x[0] in ('i32.and','i32.or','i32.xor'):
            return (x[0][4:],visit(x[1]),visit(x[2]))
        if x in (c(0),c(1)): return ('const',int(x[1]))
        raise ValueError('Unsupported source expression')
    return n,visit(body[0])


def original(t):
    if t[0]=='lt': return lt(t[1],t[2])
    if t[0]=='const': return c(t[1])
    return ['i32.'+t[0], original(t[1]),original(t[2])]


def transform(src,dst,mode):
    started=time.perf_counter()
    m,_=load(src); n,t=input_tree(m)
    slots={}; fills=[]; comparisons=0
    def write(slot,b):
        return [['memory.fill','1',c(slot),c(0),c(256)],
                ['memory.fill','1',c(slot),c(1),byte(b)]]
    def visit(x):
        nonlocal comparisons
        if x[0]=='lt':
            comparisons+=1
            a,b=x[1:]
            if mode=='table':
                address=['i32.or',['i32.shl',byte(a),c(8)],byte(b)]
                return ['i32.load8_u','1',address]
            if mode=='individual':
                return ['block',['result','i32'],*write(0,b),['i32.load8_u','1',byte(a)]]
            if mode=='shared':
                if b not in slots:
                    slots[b]=256*len(slots)
                    fills.extend(write(slots[b],b))
                return ['i32.load8_u','1','offset='+str(slots[b]),byte(a)]
            raise ValueError(mode)
        if x[0]=='const': return c(x[1])
        return ['i32.'+x[0],visit(x[1]),visit(x[2])]
    expression=visit(t)
    data=REFERENCE_TABLE if mode=='table' else None
    compile_wat(module(n,expression,True,data,fills),dst)
    return dict(mode=mode,comparisons=comparisons,slots=len(slots) if mode=='shared' else 1,
                scratch_bytes=len(slots)*256 if mode=='shared' else (65536 if mode=='table' else 256),
                allocated_private_bytes=65536,transform_ms=(time.perf_counter()-started)*1000,
                source_sha256=hashlib.sha256(Path(src).read_bytes()).hexdigest())


def op(name,*args):
    if name in ('and','or','xor'):
        args=tuple(sorted(args,key=repr))
        if args[0]==args[1]: return ('const',0) if name=='xor' else args[0]
        if ('const',0) in args:
            return ('const',0) if name=='and' else next(x for x in args if x!=('const',0))
        if ('const',1) in args:
            if name=='or': return ('const',1)
            if name=='and': return next(x for x in args if x!=('const',1))
    return (name,*args)


def canon(t):
    if t[0] in ('lt','const'): return t
    return op(t[0],canon(t[1]),canon(t[2]))


def recover(m):
    start=time.perf_counter()
    n,l,body,memories=fields(m)
    env=[('arg',i) for i in range(n)]+[('num',0)]*l
    writes=[]; reads=0; matches=0
    stack=[]
    data=[x for x in m[1:] if x[0]=='data']
    table=False
    if data:
        if len(data)!=1 or memories!=2: raise ValueError('Unsupported data layout')
        d=data[0]
        if d[1:3]!=[['memory','1'],c(0)]: raise ValueError('Table address')
        raw=d[3][1:-1]
        # WABT printable bytes cannot occur in the Boolean table; others rejected.
        if len(raw)!=3*65536 or raw[::3]!='\\'*65536:
            raise ValueError('Unsupported table encoding')
        values=bytes.fromhex(raw.replace('\\',''))
        table=values==REFERENCE_TABLE
        if not table: raise ValueError('Table is not the claimed comparison relation')

    def number(t):
        if t[0]!='num': raise ValueError('Expected static number')
        return t[1]

    def operands(x, count):
        for node in x[1:]:
            if isinstance(node,list):
                value=evaluate(node)
                if value is not None: stack.append(value)
        if len(stack)<count: raise ValueError('Operand stack underflow')
        args=stack[-count:]
        del stack[-count:]
        return args

    def evaluate(x):
        nonlocal reads,matches
        if x[0]=='i32.const': return ('num',int(x[1])&0xffffffff)
        if x[0]=='local.get': return env[int(x[1])]
        if x[0] in ('local.set','local.tee'):
            v=operands(x,1)[0]; env[int(x[1])]=v
            return v if x[0]=='local.tee' else None
        if x[0]=='block':
            height=len(stack)
            for node in x[1:]:
                if isinstance(node,list) and node[0]!='result':
                    value=evaluate(node)
                    if value is not None: stack.append(value)
            arity=1 if ['result','i32'] in x else 0
            if len(stack)!=height+arity: raise ValueError('Unsupported block stack effect')
            return stack.pop() if arity else None
        if x[0]=='memory.fill':
            if x[1]!='1' or memories!=2: raise ValueError('Non-private memory write')
            dest,val,length=operands(x,3)
            base=number(dest); value=number(val)
            if value not in (0,1): raise ValueError('Non-Boolean fill')
            upper=number(length) if length[0]=='num' else (255 if length[0]=='byte' else None)
            if upper is None or base+upper>65536: raise ValueError('Unproved fill bounds')
            writes.append((base,value,length)); return None
        if x[0]=='i32.load8_u':
            if memories!=2 or x[1]!='1': raise ValueError('Non-private or unsupported load')
            offset=0
            for a in x[2:]:
                if isinstance(a,list): continue
                if isinstance(a,str) and a.startswith('offset='): offset=int(a[7:])
                elif not (isinstance(a,str) and a.startswith('align=')): raise ValueError('Load attribute')
            address=operands(x,1)[0]; reads+=1
            if table:
                if offset or writes or address[0] not in ('or','add'): raise ValueError('Table index')
                parts=address[1:]
                hi=next((a for a in parts if a[0]=='shl' and a[2]==('num',8)),None)
                lo=next((a for a in parts if a[0]=='byte'),None)
                if hi is None or lo is None or hi[1][0]!='byte': raise ValueError('Table index parts')
                matches+=1; return ('lt',hi[1][1],lo[1])
            if address[0]!='byte' or offset+255>=65536:
                raise ValueError('Unproved byte address')
            # Last-write reduction. The generated pattern is recognized only when
            # the entire 256-byte cell was reset before its last partial fill.
            partial=None
            for base,value,length in reversed(writes):
                upper=length[1] if length[0]=='num' else 255
                if base+upper<=offset or base>=offset+256: continue
                if base!=offset: raise ValueError('Partially crossing cells')
                if partial is None and value==1 and length[0]=='byte':
                    partial=length; continue
                if value==0 and length==('num',256):
                    if partial is None: return ('const',0)
                    matches+=1; return ('lt',address[1],partial[1])
                raise ValueError('Unsupported last-writer relation')
            raise ValueError('Missing per-call reset: memory may depend on earlier calls')
        if x[0] in ('i32.and','i32.or','i32.xor','i32.lt_u','i32.gt_u','i32.shl','i32.add'):
            name=x[0][4:]; a,b=operands(x,2)
            if name=='and' and (a==('num',255) or b==('num',255)):
                v=b if a==('num',255) else a
                if v[0]=='arg': return ('byte',v[1])
                if v[0]=='byte': return v
            if name=='lt_u' and a[0]==b[0]=='byte': return ('lt',a[1],b[1])
            if name=='gt_u' and a[0]==b[0]=='byte': return ('lt',b[1],a[1])
            if name in ('and','or','xor'):
                def boolean(t):
                    if t[0] in ('lt','const'): return True
                    return t[0] in ('and','or','xor') and all(boolean(v) for v in t[1:])
                aa=('const',a[1]) if a[0]=='num' and a[1] in (0,1) else a
                bb=('const',b[1]) if b[0]=='num' and b[1] in (0,1) else b
                return op(name,aa,bb) if boolean(aa) and boolean(bb) else (name,a,b)
            if name in ('shl','add'): return (name,a,b)
        raise ValueError('Unsupported operation: '+w.emit(x))
    for node in body:
        value=evaluate(node)
        if value is not None: stack.append(value)
    if len(stack)!=1: raise ValueError('Final stack shape')
    result=stack.pop()
    if result[0]=='num' and result[1] in (0,1): result=('const',result[1])
    def valid(t):
        if t[0]=='lt': return 0<=t[1]<n and 0<=t[2]<n
        if t[0]=='const': return t[1] in (0,1)
        return t[0] in ('and','or','xor') and valid(t[1]) and valid(t[2])
    if not valid(result): raise ValueError('Result outside Boolean comparison grammar')
    return dict(n=n,tree=result,private_reads=reads,relations_recovered=matches,
                writes=len(writes),analysis_ms=(time.perf_counter()-start)*1000)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['table','individual','shared','recover'])
    ap.add_argument('input',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args()
    if a.mode=='recover':
        m,parse=load(a.input); result=recover(m)
        compile_wat(module(result['n'],original(result['tree'])),a.output)
        result['parse_validate_ms']=parse
    else: result=transform(a.input,a.output,a.mode)
    print(json.dumps(result))


if __name__=='__main__': main()
