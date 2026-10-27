"""CNF predicate -> input-dependent Wasm validation query. Research hypothesis."""
import argparse,copy,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('validation_common',ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)

def compile(wat,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(wat,encoding='utf8')
    w.tool('wat2wasm',[dst.with_suffix('.wat'),'-o',dst]);w.tool('wasm-validate',[dst])

def read(src):
    w.tool('wasm-validate',[src]);return w.parse(w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names']))

def uleb(n):
    out=[]
    while n>=128:out.append((n&127)|128);n>>=7
    return bytes(out+[n])

def template(lengths):
    body=bytearray([0]);groups=[]
    for n in lengths:
        body.extend([2,64]);groups.append(list(range(len(body),len(body)+n)));body.extend([1]*n);body.extend([0x6a,0x1a,0x0b])
    body.append(0x0b);code=uleb(1)+uleb(len(body))
    prefix=b'\0asm\x01\0\0\0'+bytes([1,4,1,0x60,0,0,3,2,1,0,10])+uleb(len(code)+len(body))+code
    return bytes(prefix+body),[[len(prefix)+p for p in g] for g in groups]

def fold(op,values):
    if not values:return ['i32.const','1' if op=='i32.and' else '0']
    out=values[0]
    for v in values[1:]:out=[op,out,v]
    return out

def literal(v):
    word,bit,neg=v;e=['i32.and',['i32.shr_u',['local.get',str(word)],['i32.const',str(bit)]],['i32.const','1']]
    return ['i32.xor',e,['i32.const','1']] if neg else e

def expression(clauses):return fold('i32.and',[fold('i32.or',[literal(v) for v in clause]) for clause in clauses])

def source(clauses):return w.emit(['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],expression(clauses)]])

def flatten(e,op):return flatten(e[1],op)+flatten(e[2],op) if e[0]==op else [e]

def parse_literal(e):
    neg=0
    if e[0]=='i32.xor' and e[2]==['i32.const','1']:neg=1;e=e[1]
    if e[0]!='i32.and' or e[2]!=['i32.const','1']:raise ValueError('expected bit literal')
    sh=e[1]
    if sh[0]!='i32.shr_u' or sh[1][0]!='local.get' or sh[2][0]!='i32.const':raise ValueError('expected constant bit shift')
    word=int(sh[1][1]);bit=int(sh[2][1],0)
    if word not in (0,1) or not 0<=bit<32:raise ValueError('literal index out of profile')
    return word,bit,neg

def extract(m):
    if any(x[0] not in ('func','type','export') for x in m[1:]):raise ValueError('pure module required')
    fs=[x for x in m[1:] if x[0]=='func'];ex=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise ValueError('one run function required')
    f=fs[0]
    if [x for x in f[1:] if x[0]=='param']!=[['param','i32','i32']] or [x for x in f[1:] if x[0]=='result']!=[['result','i32']]:raise ValueError('two i32 inputs and one i32 result required')
    body=[x for x in f[1:] if x[0] not in ('type','param','result')]
    if len(body)!=1:raise ValueError('one pure CNF expression required')
    def conjuncts(e):
        try:parse_literal(e);return [e]
        except ValueError:pass
        return conjuncts(e[1])+conjuncts(e[2]) if e[0]=='i32.and' else [e]
    clauses=[[parse_literal(v) for v in flatten(c,'i32.or')] for c in conjuncts(body[0])]
    if len(clauses)>256 or sum(map(len,clauses))>4096:raise ValueError('profile limit')
    return clauses

def transform(src,dst):
    start=time.perf_counter();clauses=extract(read(src));data,groups=template(list(map(len,clauses)))
    if len(data)>65536:raise ValueError('query exceeds fixed memory')
    writes=[]
    for clause,g in zip(clauses,groups):
        for v,pos in zip(clause,g):writes.append(['i32.store8',['i32.const',str(pos)],['i32.xor',literal(v),['i32.const','1']]])
    m=['module',['import','"env"','"validate"',['func','$validate',['param','i32','i32'],['result','i32']]],
       ['memory','1','1'],['export','"memory"',['memory','0']],
       ['data',['i32.const','0'],'"'+''.join('\\%02x'%b for b in data)+'"'],
       ['func',['export','"run"'],['param','i32','i32'],['result','i32'],*writes,['call','$validate',['i32.const','0'],['i32.const',str(len(data))]]]]
    compile(w.emit(m),dst)
    return dict(clauses=len(clauses),literals=sum(map(len,clauses)),query_bytes=len(data),bytes=Path(dst).stat().st_size,transform_ms=(time.perf_counter()-start)*1000)

def decode_string(t):
    t=t[1:-1];out=bytearray();i=0
    while i<len(t):
        if t[i]=='\\':
            if t[i+1] in '0123456789abcdefABCDEF' and t[i+2] in '0123456789abcdefABCDEF':out.append(int(t[i+1:i+3],16));i+=3
            else:out.append({'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}[t[i+1]]);i+=2
        else:out.extend(t[i].encode('utf8'));i+=1
    return bytes(out)

def groups_from_bytes(data):
    if data[:8]!=b'\0asm\x01\0\0\0':raise ValueError('header')
    def var(pos):
        value=0;shift=0
        while True:
            b=data[pos];pos+=1;value|=(b&127)<<shift
            if not b&128:return value,pos
            shift+=7
            if shift>35:raise ValueError('LEB too long')
    pos=8;sections={}
    while pos<len(data):
        tag=data[pos];length,start=var(pos+1);sections[tag]=(start,start+length);pos=start+length
    if pos!=len(data) or set(sections)!={1,3,10}:raise ValueError('sections')
    if data[slice(*sections[1])]!=bytes([1,0x60,0,0]) or data[slice(*sections[3])]!=bytes([1,0]):raise ValueError('signature')
    pos,end=sections[10];count,pos=var(pos);size,pos=var(pos)
    if count!=1 or pos+size!=end or data[pos]!=0:raise ValueError('function body')
    pos+=1;groups=[]
    while pos<end-1:
        if data[pos:pos+2]!=bytes([2,64]):raise ValueError('block prefix')
        pos+=2;g=[]
        while data[pos] in (0,1):g.append(pos);pos+=1
        if data[pos:pos+3]!=bytes([0x6a,0x1a,0x0b]):raise ValueError('block suffix')
        groups.append(g);pos+=3
    if pos!=end-1 or data[pos]!=0x0b:raise ValueError('end')
    return groups

def recover(src,dst):
    start=time.perf_counter();m=read(src)
    if [x for x in m[1:] if x[0]=='import']!=[['import','"env"','"validate"',['func',['type','0']]]]:raise ValueError('expected validator import')
    ds=[x for x in m[1:] if x[0]=='data'];fs=[x for x in m[1:] if x[0]=='func']
    if not ds or len(fs)!=1:raise ValueError('template and one run required')
    def walk(x):
        if isinstance(x,list):
            yield x
            for v in x[1:]:yield from walk(v)
    calls=[x for x in walk(fs[0]) if x[0]=='call']
    if len(calls)!=1 or calls[0][1]!='0' or calls[0][2]!=['i32.const','0'] or calls[0][3][0]!='i32.const':raise ValueError('fixed query call required')
    size=int(calls[0][3][1],0)
    if not 0<size<=65536:raise ValueError('query range')
    image=bytearray(65536)
    for segment in ds:
        if segment[1][0]!='i32.const':raise ValueError('constant data offset required')
        off=int(segment[1][1],0);chunk=b''.join(decode_string(t) for t in segment[2:])
        if off<0 or off+len(chunk)>65536:raise ValueError('data range')
        image[off:off+len(chunk)]=chunk
    data=bytes(image[:size]);groups=groups_from_bytes(data)
    locals_={0:['local.get','0'],1:['local.get','1']};writes={};called=False
    def evaluate(x):
        nonlocal called
        op=x[0]
        if op in ('type','param','result','local'):return None
        if op=='block':
            result=None
            for v in x[1:]:
                if isinstance(v,list):result=evaluate(v)
            return result
        if op=='local.get':return copy.deepcopy(locals_.get(int(x[1]),['i32.const','0']))
        if op in ('local.set','local.tee'):
            value=evaluate(x[2]);locals_[int(x[1])]=value;return value if op=='local.tee' else None
        if op=='i32.const':return x
        if op in ('i32.and','i32.or','i32.xor','i32.shr_u','i32.shl','i32.add','i32.sub','i32.eqz'):
            return [op,*[evaluate(v) for v in x[1:]]]
        if op=='i32.store8':
            args=[v for v in x[1:] if isinstance(v,list)];addr=evaluate(args[0]);value=evaluate(args[1]);offset=0
            for v in x[1:]:
                if isinstance(v,str) and v.startswith('offset='):offset=int(v.split('=')[1])
            if addr[0]!='i32.const' or called:raise ValueError('dynamic/late write')
            pos=(int(addr[1],0)&0xffffffff)+offset
            if pos in writes:raise ValueError('duplicate write')
            writes[pos]=value;return None
        if op=='call':
            if x[1]!='0' or called or [evaluate(v) for v in x[2:]]!=[['i32.const','0'],['i32.const',str(len(data))]]:raise ValueError('validator call shape')
            called=True;return ['i32.const','0']
        if op=='return':return evaluate(x[1])
        raise ValueError('unsupported recovery opcode '+op)
    for x in fs[0][1:]:evaluate(x)
    if not called or set(writes)!={pos for g in groups for pos in g}:raise ValueError('patch coverage')
    # In the admitted producer, every patch is a Boolean byte. This precondition
    # is checked by the symbolic grammar: bit extraction, constants and bitwise ops.
    def boolean(e):
        if e[0]=='i32.const':return int(e[1],0) in (0,1)
        if e[0]=='i32.eqz':return True
        if e[0]=='i32.shr_u' and e[2][0]=='i32.const' and int(e[2][1],0)%32==31:return True
        if e[0]=='i32.and' and ['i32.const','1'] in e[1:]:return True
        return e[0] in ('i32.and','i32.or','i32.xor') and all(boolean(v) for v in e[1:])
    if not all(boolean(v) for v in writes.values()):raise ValueError('unproved Boolean byte')
    expr=fold('i32.and',[fold('i32.or',[['i32.eqz',writes[pos]] for pos in g]) for g in groups])
    compile(w.emit(['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],expr]]),dst)
    return dict(clauses=len(groups),literals=len(writes),oracle_calls=0,recover_ms=(time.perf_counter()-start)*1000,bytes=Path(dst).stat().st_size)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('input');ap.add_argument('output');a=ap.parse_args()
    print(json.dumps(globals()[a.action](a.input,a.output),indent=2))
