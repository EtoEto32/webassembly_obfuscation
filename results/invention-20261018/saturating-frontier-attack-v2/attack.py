"""Extract public SIMD coefficient sets; attempt exact two-term Minkowski factors.
Does not read the original module, benchmark name, or construction manifest.
"""
import importlib.util,itertools,json,struct,sys,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('sf',Path(__file__).with_name('compile.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def normal(rows):
    rows=set(tuple(x) for x in rows)
    # 65535 is tropical zero: padding/initial accumulator is never an extra term.
    finite={a for a in rows if a[-1]<65535}
    if finite:rows=finite
    elif rows:return frozenset([(0,)*(len(next(iter(rows)))-1)+(65535,)])
    return frozenset(a for a in rows if not any(a!=b and all(v<=u for u,v in zip(a,b)) for b in rows))
def plus(a,b):
    return normal([tuple(x+y for x,y in zip(u[:-1],v[:-1]))+(min(65535,u[-1]+v[-1]),) for u in a for v in b])
def lift(src):
    m=c.wasm.parse(c.wasm.tool('wasm2wat',[src,'--fold-exprs']));f=c.items(m,'func')[0];n=len(c.items(f,'param')[0])-1
    zero=(0,)*(n+1);locals={}
    def exp(x):
        op=x[0]
        if op=='local.get':return locals[int(x[1])]
        if op=='v128.const':
            form=x[1];values=[int(t,0) for t in x[2:]]
            if form=='i32x4':b=b''.join(struct.pack('<I',v&0xffffffff) for v in values);vals=struct.unpack('<8H',b)
            elif form=='i16x8':vals=[v&65535 for v in values]
            else:raise ValueError('const shape')
            return [frozenset([zero[:-1]+(v,)]) for v in vals]
        if op=='i16x8.splat':
            leaf=x[1]
            row=tuple(int(i==int(leaf[1])) for i in range(n))+(0,) if leaf[0]=='local.get' else zero[:-1]+(int(leaf[1])&65535,)
            return [frozenset([row])]*8
        if op in ('i16x8.min_u','i16x8.add_sat_u'):
            a,b=exp(x[1]),exp(x[2]);return [normal(u|v) if op=='i16x8.min_u' else plus(u,v) for u,v in zip(a,b)]
        if op=='v128.and':
            a,b=exp(x[1]),exp(x[2]);out=[]
            for u,v in zip(a,b):
                assert len(v)==1;mask=next(iter(v));assert not any(mask[:-1]) and mask[-1] in (0,65535)
                out.append(u if mask[-1] else frozenset([zero]))
            return out
        if op=='i8x16.shuffle':
            ids=list(map(int,x[1:17]));a=exp(x[17])+exp(x[18]);out=[]
            for i in range(0,16,2):
                assert ids[i]%2==0 and ids[i+1]==ids[i]+1
                out.append(a[ids[i]//2])
            return out
        raise ValueError(op)
    result=None
    for x in f[1:]:
        if not isinstance(x,list):continue
        if x[0]=='local.set':locals[int(x[1])]=exp(x[2])
        if x[0]=='i16x8.extract_lane_u':result=exp(x[2])[int(x[1])]
    if result is None:raise ValueError('missing result')
    return n,result
def factor(terms,stats):
    # Candidate two-point factors derive only from differences of public rows.
    if len(terms)==1:return {'term':list(next(iter(terms)))}
    tried=set()
    for p,q in itertools.combinations(sorted(terms),2):
        base=tuple(min(u,v) for u,v in zip(p,q));a=tuple(u-v for u,v in zip(p,base));b=tuple(u-v for u,v in zip(q,base))
        pair=frozenset([a,b])
        if pair in tried or len(pair)<2:continue
        tried.add(pair);stats['factorCandidates']+=1;quotient=set()
        for t in terms:
            if all(u>=v for u,v in zip(t,a)):
                r=tuple(u-v for u,v in zip(t,a));s=tuple(u+v for u,v in zip(r,b))
                if s in terms:quotient.add(r)
        if not quotient:continue
        quotient=normal(quotient)
        if len(quotient)>=len(terms) or plus(pair,quotient)!=terms:continue
        return {'add':[{'min':[{'term':list(a)},{'term':list(b)}]},factor(quotient,stats)]}
    return {'min':[{'term':list(t)} for t in sorted(terms)]}
def expand(e):
    if 'term' in e:return frozenset([tuple(e['term'])])
    if 'add' in e:return plus(*(expand(x) for x in e['add']))
    return normal(set().union(*(expand(x) for x in e['min'])))
def ops(e):
    if 'term' in e:
        t=e['term'];return max(0,sum(t[:-1])+int(t[-1]!=0)-1)
    k='add' if 'add' in e else 'min';return len(e[k])-1+sum(ops(x) for x in e[k])
def main(src,out):
    out.mkdir();rows=[]
    for p in sorted(src.glob('*-frontier.wasm')):
        start=time.perf_counter();n,terms=lift(p);extract=time.perf_counter()-start;stats={'factorCandidates':0};begin=time.perf_counter();expr=factor(terms,stats)
        assert expand(expr)==terms
        # Formal antichain equality is sufficient; not necessary for functional equality.
        rows.append({'file':p.name,'sha256':c.sha(p),'inputs':n,'terms':sorted(terms),'extractionSeconds':extract,'factorSeconds':time.perf_counter()-begin,
          'status':'exact_reconstruction','expression':expr,'reconstructedOperations':ops(expr),'flatOperations':ops({'min':[{'term':list(t)} for t in terms]}),**stats})
    (out/'attack.json').write_text(json.dumps({'rows':rows,'scope':'Known SIMD emitter profile. Two-term factors only; exact antichain equality verified. Optimality not proved.'},indent=2),encoding='utf-8')
    (out/'attack.py').write_bytes(Path(__file__).read_bytes());print([{k:r[k] for k in ('file','reconstructedOperations','flatOperations','factorCandidates','factorSeconds')} for r in rows])
if __name__=='__main__':main(*map(Path,sys.argv[1:3]))
