"""Recognize broadcast-u16 min/saturating-add Wasm; emit a flat SIMD frontier.

Research prototype. No obfuscation-resistance claim.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
import transform as wasm
M=65535
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def items(n,k):return [a for a in n if isinstance(a,list) and a[0]==k]
def write(p,wat):
    if p.exists():raise ValueError('Refuse overwrite')
    Path(str(p)+'.wat').write_text(wat,encoding='utf-8')
    wasm.tool('wat2wasm',[str(p)+'.wat','-o',p]);wasm.tool('wasm-validate',[p])
def recognize(src):
    m=wasm.parse(wasm.tool('wasm2wat',[src,'--fold-exprs']))
    if any(a[0] not in ('type','func','export') for a in m[1:] if isinstance(a,list)):raise ValueError('effects unsupported')
    fs=items(m,'func')
    if len(fs)!=1 or items(m,'export')!=[['export','"run"',['func','0']]]:raise ValueError('one export required')
    f=fs[0];params=items(f,'param');results=items(f,'result')
    if len(params)!=1 or any(p!='i32' for p in params[0][1:]) or results!=[['result','i32']] or items(f,'local'):raise ValueError('signature')
    n=len(params[0])-1
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result')]
    if len(body)!=1 or body[0][:2]!=['i16x8.extract_lane_u','0']:raise ValueError('only lane zero result')
    def parse(x):
        if x[0]=='i16x8.splat' and len(x)==2:
            v=x[1]
            if v[0]=='local.get' and len(v)==2 and 0<=int(v[1])<n:return ['var',int(v[1])]
            if v[0]=='i32.const' and len(v)==2:return ['const',int(v[1])&M]
        if x[0] in ('i16x8.min_u','i16x8.add_sat_u') and len(x)==3:return ['min' if x[0]=='i16x8.min_u' else 'add',parse(x[1]),parse(x[2])]
        raise ValueError('unsupported node '+str(x[0]))
    return n,parse(body[0][2])
def prune(terms):
    dedup={}
    for a,c in terms:
        if c==M:a=(0,)*len(a)
        dedup[a]=min(c,dedup.get(a,M))
    rows=sorted(dedup.items());out=[]
    for a,c in rows:
        if not any((b,d)!=(a,c) and d<=c and all(u<=v for u,v in zip(b,a)) for b,d in rows):out.append((a,c))
    return out
def expand(e,n):
    if e[0]=='var':return [(tuple(int(i==e[1]) for i in range(n)),0)]
    if e[0]=='const':return [((0,)*n,e[1])]
    a,b=expand(e[1],n),expand(e[2],n)
    if len(a)*len(b)>65536:raise ValueError('expansion budget')
    out=prune(a+b if e[0]=='min' else [(tuple(x+y for x,y in zip(u,v)),min(M,c+d)) for u,c in a for v,d in b])
    if len(out)>256 or any(max(a)>16 for a,c in out):raise ValueError('output budget')
    return out
def vec(values):return '(v128.const i16x8 '+' '.join(str(v) for v in values)+')'
def source_expr(e):
    if e[0]=='var':return f'(i16x8.splat (local.get {e[1]}))'
    if e[0]=='const':return f'(i16x8.splat (i32.const {e[1]}))'
    return f'({"i16x8.min_u" if e[0]=="min" else "i16x8.add_sat_u"} {source_expr(e[1])} {source_expr(e[2])})'
def source(n,e):return '(module (func (export "run") (param '+' '.join(['i32']*n)+') (result i32) (i16x8.extract_lane_u 0 '+source_expr(e)+')))'
def emit(n,terms):
    # n = accumulator vector, n+1 = current pack, n+2 = horizontally reduced vector
    lines=[f'(local.set {n} {vec([M]*8)})']
    for off in range(0,len(terms),8):
        pack=terms[off:off+8]+[((0,)*n,M)]*(8-len(terms[off:off+8]))
        lines.append(f'(local.set {n+1} {vec([c for a,c in pack])})')
        for j in range(n):
            for k in range(max(a[j] for a,c in pack)):
                mask=vec([M if a[j]>k else 0 for a,c in pack])
                lines.append(f'(local.set {n+1} (i16x8.add_sat_u (local.get {n+1}) (v128.and (i16x8.splat (local.get {j})) {mask})))')
        lines.append(f'(local.set {n} (i16x8.min_u (local.get {n}) (local.get {n+1})))')
    for shift in (4,2,1):
        # Each 16-bit lane rotates cyclically; min reductions cover all eight lanes.
        indices=' '.join(str(2*((i+shift)%8)+b) for i in range(8) for b in (0,1))
        lines.append(f'(local.set {n} (i16x8.min_u (local.get {n}) (i8x16.shuffle {indices} (local.get {n}) (local.get {n}))))')
    lines.append(f'(i16x8.extract_lane_u 0 (local.get {n}))')
    return '(module (func (export "run") (param '+' '.join(['i32']*n)+') (result i32) (local v128 v128) '+'\n'.join(lines)+'))'
def transform(src,dst):
    start=time.perf_counter();n,e=recognize(src);terms=expand(e,n);write(dst,emit(n,terms))
    return {'inputs':n,'terms':len(terms),'frontier':terms,'transformationSeconds':time.perf_counter()-start,'inputSHA256':sha(src),'sha256':sha(dst)}
def bench():
    v=lambda i:['var',i];a=lambda x,y:['add',x,y];mi=lambda x,y:['min',x,y]
    return {
      'two-choices':(4,a(mi(v(0),v(1)),mi(v(2),v(3)))),
      'four-choices':(8,a(a(mi(v(0),v(1)),mi(v(2),v(3))),a(mi(v(4),v(5)),mi(v(6),v(7))))),
      'shared-input':(4,a(mi(v(0),v(1)),mi(a(v(0),v(2)),a(v(1),v(3))))),
      'cost-offset':(4,mi(a(mi(a(v(0),['const',17]),v(1)),mi(v(2),a(v(3),['const',29]))),a(v(0),v(3))))}
def build(out):
    out.mkdir();rows=[];expressions={}
    for name,(n,e) in bench().items():
        expressions[name]=e;src=out/(name+'-plain.wasm');write(src,source(n,e))
        rows.append({'kernel':name,'mode':'plain','file':src.name,'sha256':sha(src),'inputs':n,'bytes':src.stat().st_size})
        dst=out/(name+'-frontier.wasm');info=transform(src,dst)
        rows.append({'kernel':name,'mode':'frontier','file':dst.name,'bytes':dst.stat().st_size,**info})
    (out/'manifest.json').write_text(json.dumps({'artifacts':rows,'referenceExpressions':expressions,'sourceSHA256':sha(Path(__file__))},indent=2),encoding='utf-8')
    (out/'compile.py').write_bytes(Path(__file__).read_bytes());print([(r['file'],r.get('terms'),r['bytes']) for r in rows])
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','transform']);ap.add_argument('source',type=Path);ap.add_argument('output',type=Path,nargs='?');a=ap.parse_args()
    if a.command=='build':build(a.source)
    else:print(json.dumps(transform(a.source,a.output),indent=2))
