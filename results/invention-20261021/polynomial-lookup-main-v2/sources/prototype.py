"""Restricted static-list replacement. Polynomial representation is known."""
import argparse, importlib.util, json, struct, time
from pathlib import Path
from field import P, encode, evaluate, roots
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('lookup_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)

def quoted(data):return '"'+''.join('\\%02x'%x for x in data)+'"'

def unquote(s):
    out=bytearray();i=1
    while i<len(s)-1:
        if s[i]=='\\':
            if s[i+1] in '0123456789abcdefABCDEF' and s[i+2] in '0123456789abcdefABCDEF':
                out.append(int(s[i+1:i+3],16));i+=3
            else:out.append({'n':10,'t':9,'r':13,'"':34,'\\':92}[s[i+1]]);i+=2
        else:out.extend(s[i].encode('utf-8'));i+=1
    return bytes(out)

def list_text(items,layout=(0,4,8)):
    nxt,key,val=layout;data=bytearray(12*len(items))
    for i,(k,v) in enumerate(items):
        for off,x in ((nxt,64+12*(i+1) if i+1<len(items) else 0),(key,k),(val,v)):
            struct.pack_into('<I',data,12*i+off,x&0xffffffff)
    head=64 if items else 0
    return f'''(module (memory 1) (data (i32.const 64) {quoted(data)})
      (func (export "lookup") (param $key i32) (result i32) (local $p i32)
       (local.set $p (i32.const {head})) (block $done (loop $next
       (br_if $done (i32.eqz (local.get $p)))
       (if (i32.eq (i32.load offset={key} (local.get $p)) (local.get $key))
        (then (return (i32.load offset={val} (local.get $p)))))
       (local.set $p (i32.load offset={nxt} (local.get $p))) (br $next)))
       (i32.const 0)))'''

def data_memory(m):
    mem=bytearray(65536)
    for d in m[1:]:
        if d[0]!='data':continue
        if d[1][:1]!=['i32.const']:raise q.Unsupported('constant active data required')
        off=int(d[1][1])&0xffffffff;b=b''.join(unquote(x) for x in d[2:])
        if off+len(b)>len(mem):raise q.Unsupported('data out of bounds')
        mem[off:off+len(b)]=b
    return mem

def parse_list(m):
    if any(e[0] not in ('type','func','memory','export','data') for e in m[1:]):
        raise q.Unsupported('only closed static list supported')
    fs=[e for e in m[1:] if e[0]=='func'];ts=[e for e in m[1:] if e[0]=='type']
    if len(fs)!=1 or ts!=[['type',['func',['param','i32'],['result','i32']]]]:
        raise q.Unsupported('one lookup function required')
    if [e for e in m[1:] if e[0]=='export']!=[['export','"lookup"',['func','0']]]:
        raise q.Unsupported('only lookup export allowed')
    if [e for e in m[1:] if e[0]=='memory']!=[['memory','1']]:raise q.Unsupported('private one-page memory')
    f=fs[0];loads=[e for e in q.walk(f) if e[0]=='i32.load']
    if len(loads)!=3:raise q.Unsupported('list load profile')
    offsets=[]
    for e in loads:
        if len(e)==2:offsets.append(0)
        elif len(e)==3 and e[1].startswith('offset='):offsets.append(int(e[1][7:]))
        else:raise q.Unsupported('load profile')
    key,val,nxt=offsets
    if sorted(offsets)!=[0,4,8]:raise q.Unsupported('three distinct word fields')
    try: head=int(f[5][2][1])&0xffffffff
    except (IndexError,ValueError,TypeError):raise q.Unsupported('head profile')
    ld=lambda off:['i32.load',*([f'offset={off}'] if off else []),['local.get','1']]
    expected=['func',['type','0'],['param','i32'],['result','i32'],['local','i32'],
      ['local.set','1',['i32.const',str(head if head<2**31 else head-2**32)]],
      ['block',['loop',['br_if','1',['i32.eqz',['local.get','1']]],
       ['if',['i32.eq',ld(key),['local.get','0']],['then',['return',ld(val)]]],
       ['local.set','1',ld(nxt)],['br','0']]],['i32.const','0']]
    if f!=expected:raise q.Unsupported('function differs from static lookup profile')
    mem=data_memory(m);seen=set();items={};ptr=head
    while ptr:
        if ptr in seen:raise q.Unsupported('cyclic list')
        if ptr+12>65536:raise q.Unsupported('out-of-bounds node')
        if len(seen)>=512:raise q.Unsupported('512-node limit')
        seen.add(ptr);word=lambda off:struct.unpack_from('<I',mem,ptr+off)[0]
        items.setdefault(word(key),word(val));ptr=word(nxt)
    return sorted(items.items()),dict(nodes=len(seen),unique_keys=len(items),fields=offsets)

def array_text(items):
    b=b''.join(struct.pack('<II',k,v) for k,v in items)
    return f'''(module (memory 1) (data (i32.const 64) {quoted(b)})
      (func (export "lookup") (param $k i32) (result i32) (local $p i32)
       (local.set $p (i32.const 64)) (block $done (loop $scan
        (br_if $done (i32.ge_u (local.get $p) (i32.const {64+8*len(items)})))
        (if (i32.eq (i32.load (local.get $p)) (local.get $k))
          (then (return (i32.load offset=4 (local.get $p)))))
        (local.set $p (i32.add (local.get $p) (i32.const 8))) (br $scan))) (i32.const 0)))'''

def poly_text(items,prune=False):
    ordinary=[(k,v) for k,v in items if k<P];exception=dict((k,v) for k,v in items if k>=P)
    n=len(ordinary);a,b,c=encode(ordinary) if n else ([1],[],[])
    flags=sum(1<<(k-P) for k in exception)
    words=[n,flags,*[exception.get(P+i,0) for i in range(5)],*a,*b,*c]
    data=b''.join(struct.pack('<I',x) for x in words)
    high=f'(call $eval (i32.const {28+4*(2*n+1)}) (i32.const {n}) (local.get $x))'
    if prune and not any(c):high='(i64.const 0)'
    return f'''(module (memory 1) (data (i32.const 0) {quoted(data)})
     (func $eval (param $ptr i32) (param $len i32) (param $x i64) (result i64) (local $a i64)
      (block $done (loop $step (br_if $done (i32.eqz (local.get $len)))
        (local.set $len (i32.sub (local.get $len) (i32.const 1)))
        (local.set $a (i64.rem_u
          (i64.add (i64.mul (local.get $a) (local.get $x))
            (i64.load32_u (i32.add (local.get $ptr) (i32.shl (local.get $len) (i32.const 2)))))
          (i64.const {P}))) (br $step))) (local.get $a))
     (func (export "lookup") (param $key i32) (result i32) (local $x i64) (local $d i32)
      (local.set $x (i64.extend_i32_u (local.get $key)))
      (if (i64.ge_u (local.get $x) (i64.const {P})) (then
       (local.set $d (i32.sub (local.get $key) (i32.const {P})))
       (if (i32.and (i32.load (i32.const 4)) (i32.shl (i32.const 1) (local.get $d)))
         (then (return (i32.load (i32.add (i32.const 8) (i32.shl (local.get $d) (i32.const 2)))))))
       (return (i32.const 0))))
      (if (i64.eqz (call $eval (i32.const 28) (i32.const {n+1}) (local.get $x)))
       (then (return (i32.wrap_i64 (i64.add
         (call $eval (i32.const {28+4*(n+1)}) (i32.const {n}) (local.get $x))
         (i64.mul (i64.const {P}) {high}))))))
      (i32.const 0)))'''

def transform(src,dst,mode):
    t=time.perf_counter();items,info=parse_list(q.read(src));t1=time.perf_counter()
    text={'array':array_text,'poly':poly_text,'poly-pruned':lambda xs:poly_text(xs,True)}[mode](items);t2=time.perf_counter()
    q.compile(text,dst);t3=time.perf_counter()
    return dict(**info,mode=mode,read_ms=(t1-t)*1000,construct_ms=(t2-t1)*1000,
                compile_ms=(t3-t2)*1000,total_ms=(t3-t)*1000)

def recover(src,dst=None):
    t=time.perf_counter();m=q.read(src);mem=data_memory(m);t1=time.perf_counter()
    word=lambda a:struct.unpack_from('<I',mem,a)[0]
    n,flags=word(0),word(4)
    if n>512 or flags>31:raise q.Unsupported('polynomial data format')
    a=[word(28+4*i) for i in range(n+1)]
    b=[word(28+4*(n+1+i)) for i in range(n)]
    c=[word(28+4*(2*n+1+i)) for i in range(n)]
    if any(x>=P for x in a+b+c):raise q.Unsupported('not a field coefficient')
    ks,certificate=roots(a);items=[]
    for k in ks:
        lo,hi=evaluate(b,k),evaluate(c,k)
        if hi>1 or lo+P*hi>0xffffffff:raise q.Unsupported('invalid output quotient')
        items.append((k,lo+P*hi))
    items.extend((P+i,word(8+4*i)) for i in range(5) if flags>>i&1)
    t2=time.perf_counter()
    if dst is not None:q.compile(array_text(items),dst)
    return dict(items=items,certificate=certificate,read_ms=(t1-t)*1000,
                factor_and_evaluate_ms=(t2-t1)*1000,analysis_ms=(t2-t)*1000)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['transform','recover']);p.add_argument('src');p.add_argument('dst');p.add_argument('--mode',choices=['array','poly','poly-pruned'],default='poly');a=p.parse_args()
    r=transform(a.src,a.dst,a.mode) if a.action=='transform' else recover(a.src,a.dst)
    print(json.dumps(r,ensure_ascii=False))
