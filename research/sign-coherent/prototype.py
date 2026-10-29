"""Exact finite-domain activation mixing; no novelty/security certification."""
import argparse,importlib.util,itertools,json,random,struct,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sign_tools',ROOT/'research/prefix-repair/prototype.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common);q=common.q
POINTS=[(x,y) for x in range(-128,128) for y in range(-128,128)]
SAMPLES=[POINTS[i] for i in [0,127,128,255,256,32639,32640,32767,32768,32895,32896,33024,65280,65407,65408,65535]]

def signature(row,points=POINTS):
    a,b,c=row
    return bytes(a*x+b*y+c>0 for x,y in points)

def groups(rows):
    found={}
    for i,row in enumerate(rows):found.setdefault(signature(row),[]).append(i)
    return list(found.values())

def validate(rows,weights):
    if len(rows)!=4 or len(weights)!=4 or any(len(row)!=3 for row in rows):raise ValueError('four affine channels')
    if any(not -2**31<=v<2**31 for row in rows for v in row) or any(not -2**31<=v<2**31 for v in weights):raise ValueError('i32 coefficient')
    if any(128*(abs(a)+abs(b))+abs(c)>=2**31 for a,b,c in rows):raise ValueError('signed preactivation overflow possible')

def source(rows,weights):
    validate(rows,weights)
    values=[row[j] for j in range(3) for row in rows]+list(weights)
    blob=''.join('\\'+format(v,'02x') for v in struct.pack('<16i',*values))
    return '''(module (memory 1 1)
      (func (export "run") (param i32 i32) (result i32) (local v128)
       (local.set 2 (i32x4.mul
        (i32x4.max_s (i32x4.add
         (i32x4.add
          (i32x4.mul (i32x4.splat (i32.extend8_s (local.get 0))) (v128.load (i32.const 0)))
          (i32x4.mul (i32x4.splat (i32.extend8_s (local.get 1))) (v128.load (i32.const 16))))
         (v128.load (i32.const 32))) (v128.const i32x4 0 0 0 0))
        (v128.load (i32.const 48))))
       (i32.add (i32.add (i32x4.extract_lane 0 (local.get 2)) (i32x4.extract_lane 1 (local.get 2)))
        (i32.add (i32x4.extract_lane 2 (local.get 2)) (i32x4.extract_lane 3 (local.get 2)))))
      (data (i32.const 0) "'''+blob+'"))'

def read(src):
    mod=q.read(src);image=bytearray(64)
    for e in mod[1:]:
        if e[0]!='data':continue
        if e[1][0]!='i32.const':raise ValueError('active data required')
        start=int(e[1][1]);segment=common.data_image(['module',['data',['i32.const','0'],*e[2:]]])
        if not 0<=start<=start+len(segment)<=64:raise ValueError('coefficient data outside 64 bytes')
        image[start:start+len(segment)]=segment
    vals=struct.unpack('<16i',image);rows=[[vals[i],vals[4+i],vals[8+i]] for i in range(4)];weights=list(vals[12:])
    validate(rows,weights)
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='sign-profile-') as td:
        ref=Path(td)/'ref.wasm';q.compile(source(rows,weights),ref)
        if q.read(ref)!=mod:
            opt=Path(td)/'opt.wasm';q.tool('wasm-opt',[ref,'-O3','--enable-simd','-o',opt])
            if q.read(opt)!=mod:raise ValueError('not a supported raw/O3 profile')
    return rows,weights

def transform(src,dst,mode='mix',seed=221022):
    start=time.perf_counter();rows,weights=read(src);gs=groups(rows);before=[list(row) for row in rows]
    rng=random.Random(seed);mixers=[]
    if mode=='perm':
        order=[2,0,3,1];rows=[rows[i] for i in order];weights=[weights[i] for i in order]
    elif mode in ('mix','bad'):
        selected=gs if mode=='mix' else [[0,2],[1,3]]
        for group in selected:
            if len(group)!=2:raise ValueError('experiment requires two-channel groups')
            i,j=group;s,t=rng.randint(1,3),rng.randint(1,3);a,b=rows[i],rows[j];u,v=weights[i],weights[j]
            rows[i]=[x+t*y for x,y in zip(a,b)]
            rows[j]=[s*x+(1+s*t)*y for x,y in zip(a,b)]
            weights[i]=u*(1+s*t)-v*s;weights[j]=v-u*t
            mixers.append(dict(group=group,matrix=[[1,t],[s,1+s*t]]))
    elif mode!='plain':raise ValueError(mode)
    validate(rows,weights);q.compile(source(rows,weights),dst)
    return dict(groups=gs,mixers=mixers,rows=rows,weights=weights,original_rows=before,mode=mode,
        transform_ms=(time.perf_counter()-start)*1000)

def scalar(row):
    a,b,c=row
    return f'(i32.add (i32.add (i32.mul (local.get 0) (i32.const {a&0xffffffff})) (i32.mul (local.get 1) (i32.const {b&0xffffffff}))) (i32.const {c&0xffffffff}))'

def recover(src,dst):
    start=time.perf_counter();rows,weights=read(src);loaded=time.perf_counter();gs=groups(rows);terms=[];proof=[]
    candidates=sorted([v for v in itertools.product(range(-2,3),repeat=3) if v!=(0,0,0)],key=lambda v:(sum(abs(x) for x in v),v))
    for group in gs:
        target=signature(rows[group[0]]);sample=signature(rows[group[0]],SAMPLES);chosen=None;attempts=0;full=0
        for candidate in candidates:
            attempts+=1
            if signature(candidate,SAMPLES)!=sample:continue
            full+=1
            if signature(candidate)==target:chosen=candidate;break
        if chosen is None:chosen=rows[group[0]]
        aggregate=[sum(weights[i]*rows[i][j] for i in group) for j in range(3)]
        terms.append(f'(select {scalar(aggregate)} (i32.const 0) (i32.gt_s {scalar(chosen)} (i32.const 0)))')
        proof.append(dict(group=group,predicate=chosen,aggregate=aggregate,candidates=attempts,full_signatures=full,domain=65536))
    # Canonical order makes byte identity across encodings a meaningful check.
    paired=sorted(zip(proof,terms),key=lambda pair:(tuple(pair[0]['predicate']),tuple(pair[0]['aggregate'])))
    terms=[x[1] for x in paired];proof=[x[0] for x in paired]
    result=terms[0]
    for term in terms[1:]:result=f'(i32.add {result} {term})'
    wat='(module (func (export "run") (param i32 i32) (result i32) (local.set 0 (i32.extend8_s (local.get 0))) (local.set 1 (i32.extend8_s (local.get 1))) '+result+'))'
    analyzed=time.perf_counter();q.compile(wat,dst)
    return dict(groups=proof,read_ms=(loaded-start)*1000,recovery_ms=(analyzed-loaded)*1000,sha256=q.digest(dst))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['plain','perm','mix'],default='mix');ap.add_argument('--seed',type=int,default=221022)
    a=ap.parse_args();q.save(str(a.output)+'.json',transform(a.source,a.output,a.mode,a.seed) if a.action=='transform' else recover(a.source,a.output))
