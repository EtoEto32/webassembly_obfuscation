"""Trap-frontier preserving store covers for a restricted Wasm writer family."""
import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import random
import time

spec=importlib.util.spec_from_file_location('frontier_common',Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
WIDTHS={'i32.store8':1,'i32.store16':2,'i32.store':4,'i64.store8':1,'i64.store16':2,'i64.store32':4,'i64.store':8}


def compile_wat(wat,path):
    path=Path(path)
    if path.exists() or path.with_suffix('.wat').exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.wat').write_text(wat,encoding='utf-8')
    w.tool('wat2wasm',[path.with_suffix('.wat'),'-o',path]);w.tool('wasm-validate',[path])


def read(path):
    w.tool('wasm-validate',[path]);mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in ('type','memory','func','export') for x in mod[1:]):raise ValueError('Module fields')
    fs=[x for x in mod[1:] if x[0]=='func'];mem=[x for x in mod[1:] if x[0]=='memory'];exports=[x for x in mod[1:] if x[0]=='export']
    if len(fs)!=1 or mem!=[['memory','1','1']]:raise ValueError('One function and fixed nonshared memory required')
    if sorted(exports)!=sorted([['export','"run"',['func','0']],['export','"memory"',['memory','0']]]):raise ValueError('Public API')
    f=fs[0];decl=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result','local')]
    params=[v for x in decl if x[0]=='param' for v in x[1:]];types=params+[v for x in decl if x[0]=='local' for v in x[1:]]
    if not 2<=len(params)<=32 or any(t!='i32' for t in params) or [x for x in decl if x[0]=='result']!=[['result','i32']]:raise ValueError('Function signature')
    if any(t not in ('i32','i64') for t in types):raise ValueError('Local types')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    if not body or body[-1]!=['i32.const','0']:raise ValueError('Return must be constant zero')
    return dict(params=len(params),types=types,body=body[:-1])


def immediate(x,key,default):
    vals=[int(t.split('=',1)[1],0) for t in x[1:] if isinstance(t,str) and t.startswith(key+'=')]
    if len(vals)>1:raise ValueError('Duplicate memarg')
    return vals[0] if vals else default


def store(x):
    if x[0] not in WIDTHS:raise ValueError('Expected store')
    if any(not (t.startswith('offset=') or t.startswith('align=')) for t in x[1:] if isinstance(t,str)):raise ValueError('Memory index or memarg')
    args=[t for t in x[1:] if isinstance(t,list)]
    if len(args)!=2 or args[0]!=['local.get','0']:raise ValueError('Common unmodified base required')
    offset=immediate(x,'offset',0);width=WIDTHS[x[0]]
    if not 0<=offset or offset+width>256:raise ValueError('Writer footprint limited to offsets below 256')
    return offset,width,args[1]


def source(path):
    p=read(path);ops=[]
    if len(p['types'])!=p['params']:raise ValueError('Source locals unsupported')
    for x in p['body']:
        offset,width,v=store(x)
        if x[0].startswith('i64') or len(v)!=2 or v[0]!='local.get' or not 1<=int(v[1])<p['params']:raise ValueError('Source value must be an i32 argument')
        ops.append(dict(offset=offset,bytes=[(int(v[1]),i) for i in range(width)]))
    if not ops:raise ValueError('No stores')
    return p['params'],ops


def frontiers(ops):
    groups=[];right=-1
    for op in ops:
        end=op['offset']+len(op['bytes'])
        if end>right:groups.append(dict(right=end,image={}));right=end
        groups[-1]['image'].update({op['offset']+i:v for i,v in enumerate(op['bytes'])})
    return groups


def runs(image):
    out=[]
    for i in sorted(image):
        if not out or i!=out[-1][1]:out.append([i,i+1])
        else:out[-1][1]+=1
    return out


def simple_cover(lo,hi):
    result=[]
    while hi>lo:
        width=next(k for k in (8,4,2,1) if k<=hi-lo);result.append((hi-width,width));hi-=width
    return result


def woven_cover(lo,hi,image,extra):
    # A bounded interval-cover DP. The first interval ends at the fault
    # frontier; the rest extend a covered prefix and may overlap each other.
    budget=len(simple_cover(lo,hi))+extra
    def score(start,width):
        return sum(image[j][0]!=image[j+1][0] for j in range(start,start+width-1))
    best=None
    for anchor_width in (1,2,4,8):
        if anchor_width>hi-lo:continue
        anchor=(hi-anchor_width,anchor_width)
        @lru_cache(None)
        def search(covered,left):
            if covered>=anchor[0]:return (0,())
            if left==0:return None
            answer=None
            for width in (1,2,4,8):
                for start in range(max(lo,covered-width+1),min(covered,hi-width)+1):
                    end=start+width
                    if end<=covered:continue
                    tail=search(end,left-1)
                    if tail is None:continue
                    candidate=(score(start,width)+tail[0],((start,width),)+tail[1])
                    if answer is None or (candidate[0],-len(candidate[1]),candidate[1])>(answer[0],-len(answer[1]),answer[1]):answer=candidate
            return answer
        tail=search(lo,budget-1)
        if tail is None:continue
        candidate=(score(*anchor)+tail[0],(anchor,)+tail[1])
        if best is None or (candidate[0],-len(candidate[1]),candidate[1])>(best[0],-len(best[1]),best[1]):best=candidate
    if best is None:raise AssertionError('No cover')
    return list(best[1])


def plan(groups,mode):
    ops=[]
    for group in groups:
        image=group['image'];chunks=[]
        for lo,hi in reversed(runs(image)):
            if mode=='byte':part=[(i,1) for i in range(hi-1,lo-1,-1)]
            elif mode=='coalesced':part=simple_cover(lo,hi)
            else:part=woven_cover(lo,hi,image,int(mode[-1]))
            chunks+=part
        assert chunks[0][0]+chunks[0][1]==group['right']
        # Fixed reproducible permutation of the already-safe remaining writes.
        if mode.startswith('woven'):
            tail=chunks[1:];random.Random(20261018+group['right']).shuffle(tail);chunks=chunks[:1]+tail
        ops += [dict(offset=start,bytes=[image[i] for i in range(start,start+width)]) for start,width in chunks]
    return ops


def byte_expr(origin):
    param,byte=origin
    value=f'(i32.shr_u (local.get {param}) (i32.const {8*byte}))' if byte else f'(local.get {param})'
    return f'(i64.extend_i32_u (i32.and {value} (i32.const 255)))'


def pack(origins):
    # Preserve contiguous source slices to avoid charging byte lowering to the
    # cover choice. Cross-field chunks still assemble several slices.
    pieces=[];i=0
    while i<len(origins):
        param,start=origins[i];j=i+1
        while j<len(origins) and origins[j]==(param,start+j-i):j+=1
        count=j-i;value=f'(local.get {param})'
        if start:value=f'(i32.shr_u {value} (i32.const {8*start}))'
        if count<4:value=f'(i32.and {value} (i32.const {(1<<(8*count))-1}))'
        value=f'(i64.extend_i32_u {value})'
        if i:value=f'(i64.shl {value} (i64.const {8*i}))'
        pieces.append(value);i=j
    result=pieces[0]
    for value in pieces[1:]:result=f'(i64.or {result} {value})'
    return result


def module(params,ops):
    body=[]
    for op in ops:
        size=len(op['bytes']);value=pack(op['bytes']);kind={1:'i32.store8',2:'i32.store16',4:'i32.store',8:'i64.store'}[size]
        if size<8:value=f'(i32.wrap_i64 {value})'
        body.append(f'({kind} offset={op["offset"]} align=1 (local.get 0) {value})')
    return '(module (memory (export "memory") 1 1) (func (export "run") (param '+' '.join(['i32']*params)+') (result i32) '+' '.join(body)+' (i32.const 0)))'


def plain(params,specs):
    body=' '.join('('+{1:'i32.store8',2:'i32.store16',4:'i32.store'}[width]+f' offset={offset} align=1 (local.get 0) (local.get {param}))' for offset,width,param in specs)
    return '(module (memory (export "memory") 1 1) (func (export "run") (param '+' '.join(['i32']*params)+') (result i32) '+body+' (i32.const 0)))'


def transform(src,dst,mode):
    started=time.perf_counter();params,ops=source(src);groups=frontiers(ops);new=plan(groups,mode);compile_wat(module(params,new),dst)
    return dict(mode=mode,transform_ms=(time.perf_counter()-started)*1000,input_stores=len(ops),output_stores=len(new),frontiers=[g['right'] for g in groups])


class Bits:
    def __init__(self,program):
        self.env=[[(i,j) for j in range(32)] for i in range(program['params'])]+[[0]*(32 if t=='i32' else 64) for t in program['types'][program['params']:]]
    def ev(self,x):
        op=x[0];width=64 if op.startswith('i64') else 32
        if op=='local.get':return self.env[int(x[1])]
        if op in ('local.set','local.tee'):
            if int(x[1])==0 or len(x)!=3:raise ValueError('Base mutation or stack-only assignment')
            value=self.ev(x[2]);self.env[int(x[1])]=value;return value
        if op in ('i32.const','i64.const'):return [(int(x[1],0)>>i)&1 for i in range(width)]
        args=[self.ev(v) for v in x[1:] if isinstance(v,list)]
        if op=='i64.extend_i32_u':return args[0]+[0]*32
        if op=='i32.wrap_i64':return args[0][:32]
        if op in ('i32.shl','i64.shl','i32.shr_u','i64.shr_u'):
            if any(v not in (0,1) for v in args[1]):raise ValueError('Nonconstant shift')
            n=sum(v<<i for i,v in enumerate(args[1]))&(width-1)
            return ([0]*n+args[0])[:width] if op.endswith('shl') else (args[0]+[0]*n)[n:]
        if op in ('i32.and','i64.and','i32.or','i64.or','i32.xor','i64.xor','i32.add','i64.add'):
            result=[]
            for v,z in zip(*args):
                if op.endswith('and'):
                    if v==0 or z==0:r=0
                    elif v==1 or z==v:r=z
                    elif z==1:r=v
                    else:raise ValueError('Mixed symbolic AND')
                elif op.endswith('xor'):
                    if v==z:r=0
                    elif v==0:r=z
                    elif z==0:r=v
                    else:raise ValueError('Mixed symbolic XOR')
                else:
                    if v==0:r=z
                    elif z==0:r=v
                    elif op.endswith('or') and (v==z or v==1 or z==1):r=1 if 1 in (v,z) else v
                    else:raise ValueError('Carry or mixed symbolic OR')
                result.append(r)
            return result
        raise ValueError('Unsupported expression '+op)


def extract(program):
    machine=Bits(program);ops=[]
    for node in program['body']:
        if node[0]=='local.set':machine.ev(node);continue
        offset,width,value=store(node);bits=machine.ev(value);origins=[]
        for i in range(width):
            byte=bits[8*i:8*i+8]
            if not byte or not isinstance(byte[0],tuple):raise ValueError('Non-argument byte')
            param,bit=byte[0]
            if param==0 or bit%8 or byte!=[(param,bit+j) for j in range(8)]:raise ValueError('Mixed byte expression')
            origins.append((param,bit//8))
        ops.append(dict(offset=offset,bytes=origins))
    if not ops:raise ValueError('No stores')
    return frontiers(ops)


def signature(groups):return [(g['right'],sorted(g['image'].items())) for g in groups]


def recover(src,dst):
    start=time.perf_counter();program=read(src);parse_ms=(time.perf_counter()-start)*1000;start=time.perf_counter();groups=extract(program)
    analysis_ms=(time.perf_counter()-start)*1000;ops=plan(groups,'coalesced');compile_wat(module(program['params'],ops),dst)
    return dict(status='success',extract_ms=parse_ms,analysis_ms=analysis_ms,frontiers=[g['right'] for g in groups],stores=len(ops))


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    tr=sub.add_parser('transform');tr.add_argument('src',type=Path);tr.add_argument('dst',type=Path);tr.add_argument('--mode',choices=['byte','coalesced','woven0','woven1'],default='woven1')
    rec=sub.add_parser('recover');rec.add_argument('src',type=Path);rec.add_argument('dst',type=Path)
    args=ap.parse_args();print(json.dumps(transform(args.src,args.dst,args.mode) if args.cmd=='transform' else recover(args.src,args.dst),indent=2))


if __name__=='__main__':main()
