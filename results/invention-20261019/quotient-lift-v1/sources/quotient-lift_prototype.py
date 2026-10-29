"""Deterministic state covers; early research gate, not a novelty claim."""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import tempfile
import time

spec=importlib.util.spec_from_file_location('quotient_source',Path(__file__).resolve().parents[1]/'suffix-transport/prototype.py')
s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
w=s.w

def compile_wat(text,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[dst.with_suffix('.wat'),'--enable-multi-memory','-o',dst])
    w.tool('wasm-validate',[dst,'--enable-multi-memory'])

def table_wat(rows,start):
    if not 1<=len(rows)<=32768 or not 0<=start<len(rows):raise ValueError('State bounds')
    if any(len(r)!=3 or not 0<=r[0]<len(rows) or not 0<=r[1]<len(rows) or r[2] not in (0,1) for r in rows):raise ValueError('Rows')
    blob=b''.join(struct.pack('<III',*r) for r in rows);escaped=''.join('\\%02x'%b for b in blob)
    pages=(len(blob)+65535)//65536
    return f'''(module
      (memory (export "memory") 1 1) (memory {pages} {pages})
      (data (memory 1) (i32.const 0) "{escaped}")
      (func (export "run") (param i32 i32) (result i32) (local i32 i32 i32)
        (local.set 3 (i32.const {start}))
        (block (loop
          (br_if 1 (i32.ge_u (local.get 2) (local.get 1)))
          (local.set 4 (i32.and (i32.load8_u (i32.add (local.get 0) (local.get 2))) (i32.const 1)))
          (local.set 3 (i32.load 1 (i32.add (i32.mul (local.get 3) (i32.const 12)) (i32.shl (local.get 4) (i32.const 2)))))
          (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0)))
        (i32.load 1 offset=8 (i32.mul (local.get 3) (i32.const 12)))))'''

def source(src,parent):
    p=s.read(src);delta,final=s.source_model(p)
    with tempfile.TemporaryDirectory(prefix='source-check-',dir=parent) as td:
        f=Path(td)/'source.wasm';s.compile_wat(s.plain(delta,final),f)
        if s.read(f)['module']!=p['module']:raise ValueError('Source differs from verified scanner template')
    delta,final=s.canonical(delta,final)
    return [[delta[0][q],delta[1][q],(final>>q)&1] for q in range(len(delta[0]))]

def lift(rows,k,seed):
    n=len(rows)
    if k<1 or n*k>32768:raise ValueError('Expansion limit')
    rng=random.Random(seed);perm=list(range(n*k));rng.shuffle(perm)
    out=[[0,0,0] for _ in perm];projection=[0]*len(perm)
    for q,row in enumerate(rows):
        moves=[]
        for a in range(2):
            order=list(range(k));rng.shuffle(order);moves.append(order)
        for h in range(k):
            at=perm[q*k+h];projection[at]=q
            out[at]=[perm[row[a]*k+moves[a][h]] for a in range(2)]+[row[2]]
    assert all(out[z][2]==rows[projection[z]][2] and all(projection[out[z][a]]==rows[projection[z]][a] for a in range(2)) for z in range(len(out)))
    return out,perm[0]

def transform(src,dst,k=16,seed=20261019):
    begin=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    base=source(src,dst.parent);rows,start=lift(base,k,seed);compile_wat(table_wat(rows,start),dst)
    return dict(states=len(rows),source_states=len(base),k=k,seed=seed,start=start,
                private_pages=(12*len(rows)+65535)//65536,transform_ms=(time.perf_counter()-begin)*1000)

def quotient(rows,start=0):
    """Simple complete partition refinement, measured as such, not Hopcroft."""
    reach=[];todo=deque([start]);seen={start}
    while todo:
        q=todo.popleft();reach.append(q)
        for t in rows[q][:2]:
            if t not in seen:seen.add(t);todo.append(t)
    classes={q:rows[q][2] for q in reach};rounds=0
    while True:
        ids={};new={}
        for q in reach:
            key=(rows[q][2],classes[rows[q][0]],classes[rows[q][1]])
            new[q]=ids.setdefault(key,len(ids))
        rounds+=1
        if all(new[q]==classes[q] for q in reach):break
        classes=new
    reps={}
    for q in reach:reps.setdefault(classes[q],q)
    order=[];todo=deque([classes[start]]);mapping={classes[start]:0}
    while todo:
        c=todo.popleft();q=reps[c];order.append([classes[t] for t in rows[q][:2]]+[rows[q][2]])
        for t in order[-1][:2]:
            if t not in mapping:mapping[t]=len(mapping);todo.append(t)
    out=[[mapping[r[0]],mapping[r[1]],r[2]] for r in order]
    return out,dict(reachable=len(reach),rounds=rounds,states=len(out))

def equivalent(a,b,sa=0,sb=0):
    todo=deque([(sa,sb,'')]);seen={(sa,sb)}
    while todo:
        q,r,word=todo.popleft()
        if a[q][2]!=b[r][2]:return dict(equivalent=False,witness=word,product_states=len(seen))
        for c in range(2):
            nxt=a[q][c],b[r][c]
            if nxt not in seen:seen.add(nxt);todo.append((*nxt,word+str(c)))
    return dict(equivalent=True,product_states=len(seen))

def uleb(data,pos):
    ans=0;shift=0
    while True:
        b=data[pos];pos+=1;ans|=(b&127)<<shift
        if b<128:return ans,pos
        shift+=7
        if shift>35:raise ValueError('LEB overflow')

def extract(path,parent):
    """Reads binary data, infers start, then exact re-emission raw/O3 gate."""
    begin=time.perf_counter();w.tool('wasm-validate',[path,'--enable-multi-memory'])
    data=Path(path).read_bytes();pos=8;blobs=[]
    while pos<len(data):
        section=data[pos];size,at=uleb(data,pos+1);end=at+size
        if section==11:
            count,at=uleb(data,at)
            for _ in range(count):
                flags,at=uleb(data,at)
                if flags!=2:raise ValueError('Expected explicit private-memory segment')
                mem,at=uleb(data,at)
                if mem!=1 or data[at:at+3]!=b'\x41\x00\x0b':raise ValueError('Expected private-memory offset zero')
                at+=3;n,at=uleb(data,at);blobs.append(data[at:at+n]);at+=n
            if at!=end:raise ValueError('Data payload trailing bytes')
        pos=end
    if len(blobs)!=1 or len(blobs[0])%12:raise ValueError('Expected one complete transition table')
    rows=[list(r) for r in struct.iter_unpack('<III',blobs[0])]
    text=w.tool('wasm2wat',[path,'--enable-multi-memory','--fold-exprs','--no-debug-names']);mod=w.parse(text)
    f=next(x for x in mod[1:] if x[0]=='func')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    if body[0][0]!='local.set' or body[0][2][0]!='i32.const':raise ValueError('Start initialization unsupported')
    start=int(body[0][2][1]);matched=None
    with tempfile.TemporaryDirectory(prefix='recover-check-',dir=parent) as td:
        candidate=Path(td)/'raw.wasm';compile_wat(table_wat(rows,start),candidate)
        for opt in ('raw','O3'):
            fpath=candidate
            if opt=='O3':
                fpath=Path(td)/'optimized.wasm';w.tool('wasm-opt',[candidate,'-O3','--enable-multimemory','-o',fpath])
            expected=w.parse(w.tool('wasm2wat',[fpath,'--enable-multi-memory','--fold-exprs','--no-debug-names']))
            if mod==expected:matched=opt;break
    if matched is None:raise ValueError('Program outside verified table scanner family')
    return rows,start,dict(extraction_and_template_ms=(time.perf_counter()-begin)*1000,matched=matched)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--copies',type=int,default=16);ap.add_argument('--seed',type=int,default=20261019);a=ap.parse_args()
    if a.action=='transform':r=transform(a.source,a.output,a.copies,a.seed)
    else:
        Path(a.output).parent.mkdir(parents=True,exist_ok=True)
        rows,start,r=extract(a.source,Path(a.output).parent);t=time.perf_counter();small,stats=quotient(rows,start);r.update(stats);r['analysis_ms']=(time.perf_counter()-t)*1000
        if len(small)>16:raise ValueError('Packed clone exceeds 16 states')
        compile_wat(s.plain([[row[c] for row in small]+[0]*(16-len(small)) for c in range(2)],sum(row[2]<<i for i,row in enumerate(small))),a.output)
    print(json.dumps(r))

if __name__=='__main__':main()
