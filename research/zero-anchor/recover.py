"""Method-aware finite-coordinate recovery without seeds or generation metadata.

The reader handles the emitted pure byte profile (including Binaryen O3).
It is deliberately not presented as a general decompiler.
"""
import json, sys, time
from pathlib import Path
import prototype as p
q=p.q

class Fact:
    def __init__(self,expr,domain,values=None):
        self.expr=expr;self.domain=tuple(sorted(set(domain)))
        self.values=dict(values) if values is not None else {i:i for i in self.domain}
        self.bit_expr=None;self.true_bit=None
    def plain(self):return all(self.values[i]==i for i in self.domain)

def recover(src,dst=None):
    t0=time.perf_counter();m=q.read(src);t1=time.perf_counter()
    allowed=set('module type func export param result local local.get local.set local.tee i32.const i32x4.splat i32x4.extract_lane v128.const v128.and v128.xor v128.bitselect i8x16.swizzle i8x16.relaxed_swizzle i8x16.eq i8x16.add i8x16.sub i8x16.shr_u'.split())
    if any(e[0] not in allowed for e in q.walk(m)):raise q.Unsupported('recovery instruction profile')
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=1 or any(e[0] not in ('type','func','export') for e in m[1:]):raise q.Unsupported('pure single function')
    f=fs[0]
    if [e for e in f[1:] if isinstance(e,list) and e[0]=='param']!=[['param','i32','i32','i32']]:raise q.Unsupported('three i32 inputs')
    if [e for e in f[1:] if isinstance(e,list) and e[0]=='result']!=[['result','i32']]:raise q.Unsupported('one i32 result')
    localtypes=[t for e in f[1:] if isinstance(e,list) and e[0]=='local' for t in e[1:]]
    if any(t!='v128' for t in localtypes):raise q.Unsupported('vector locals only')
    env={i+3:Fact(q.vc([0]*16),[0]) for i in range(len(localtypes))};stats=dict(swizzles=0,table_steps=0,table_pairs_checked=0,overflow_canonicalizations=0,visited=0)
    def visit(e):
        stats['visited']+=1;op=e[0]
        if op=='local.get':
            i=int(e[1]);
            if i<3:raise q.Unsupported('scalar input must be splatted')
            return env[i]
        if op in ('local.set','local.tee'):
            i=int(e[1]);
            if i<3:raise q.Unsupported('scalar mutation')
            v=visit(e[2]);env[i]=v;return v if op=='local.tee' else None
        if op=='i32x4.splat':
            if e[1][0]!='local.get' or int(e[1][1])>=3:raise q.Unsupported('input splat')
            return Fact(e,range(256))
        if op=='i32x4.extract_lane':
            if e[1]!='0':raise q.Unsupported('extract lane zero')
            v=visit(e[2]);
            if not v.plain():raise q.Unsupported('nontrivial final encoding')
            return v
        if op=='v128.const':
            a=q.vconst(e)
            if len(set(a))!=1:raise q.Unsupported('nonuniform vector outside lookup')
            return Fact(q.vc(a),[a[0]])
        if op in ('i8x16.swizzle','i8x16.relaxed_swizzle'):
            table=q.vconst(e[1]);v=visit(e[2]);mapping={}
            for x in v.domain:
                i=v.values[x];zero=table[i] if i<16 else 0
                low=table[i%16] if i<128 else 0
                if op=='i8x16.relaxed_swizzle' and zero!=low:raise q.Unsupported('host-dependent lookup result')
                mapping[x]=zero
            stats['swizzles']+=1
            # A value may be 16 or 255 before the anchored lookup. Quotient by
            # mod16 only after verifying equality for every value in the range.
            reduced={};compatible=True
            for x,y in mapping.items():
                if x%16 in reduced and reduced[x%16]!=y:compatible=False
                reduced[x%16]=y
            if any(x>=16 for x in v.domain) and compatible:
                stats['overflow_canonicalizations']+=1
                return Fact(q.masked(v.expr),reduced.keys(),reduced)
            return Fact(v.expr,v.domain,mapping)
        if op=='i8x16.shr_u':
            v=visit(e[1])
            if not v.plain() or e[2][0]!='i32.const':raise q.Unsupported('plain constant shift')
            shift=int(e[2][1],0)&7
            return Fact([op,v.expr,['i32.const',str(shift)]],{x>>shift for x in v.domain})
        if op=='v128.bitselect':
            a,b,c=[visit(x) for x in e[1:]]
            if a.expr!=b.expr or a.domain!=tuple(range(16)) or b.domain!=tuple(range(16)) or c.bit_expr is None:raise q.Unsupported('two-row encoded step')
            rows=[b.values,a.values] if c.true_bit==1 else [a.values,b.values]
            encoding=rows[0]
            if sorted(encoding.values())!=list(range(16)):raise q.Unsupported('row zero not bijective')
            for candidate in ('add','sub','xor'):
                if all(rows[j][x]==encoding[q.op_eval(candidate,x,j)] for x in range(16) for j in range(2)):
                    expr=[p.OPS[candidate],a.expr,c.bit_expr]
                    if candidate!='xor':expr=q.masked(expr)
                    stats['table_steps']+=1;stats['table_pairs_checked']+=32
                    return Fact(expr,range(16),encoding)
            raise q.Unsupported('unsupported row operation')
        if op in ('v128.and','v128.xor','i8x16.add','i8x16.sub','i8x16.eq'):
            a,b=[visit(x) for x in e[1:]]
            if op=='v128.and' and a.expr[0]=='v128.const':a,b=b,a
            if not a.plain() or not b.plain():raise q.Unsupported('arithmetic before coordinate decode')
            # Preserve the compact form of already-proven masks.
            if op=='v128.and' and len(b.domain)==1 and all((x&b.domain[0])==x for x in a.domain):return a
            evaluate={'v128.and':lambda x,y:x&y,'v128.xor':lambda x,y:x^y,'i8x16.add':lambda x,y:(x+y)&255,'i8x16.sub':lambda x,y:(x-y)&255,'i8x16.eq':lambda x,y:255 if x==y else 0}[op]
            result=Fact([op,a.expr,b.expr],{evaluate(x,y) for x in a.domain for y in b.domain})
            if op=='i8x16.eq':
                if a.domain in ((0,1),(0,),(1,)) and b.domain in ((0,),(1,)):
                    result.bit_expr=a.expr;result.true_bit=b.domain[0]
                elif b.domain in ((0,1),(0,),(1,)) and a.domain in ((0,),(1,)):
                    result.bit_expr=b.expr;result.true_bit=a.domain[0]
            return result
        raise q.Unsupported('unsupported expression '+op)
    result=None
    for e in f[1:]:
        if isinstance(e,list) and e[0] in ('type','param','result','local'):continue
        v=visit(e)
        if v is not None:
            if result is not None:raise q.Unsupported('multiple results')
            result=v
    if result is None or not result.plain():raise q.Unsupported('missing decoded result')
    text=p.module(result.expr);t2=time.perf_counter()
    if dst is not None:q.compile(text,dst)
    return text,dict(stats,read_ms=(t1-t0)*1000,body_ms=(t2-t1)*1000,ms=(time.perf_counter()-t0)*1000)

def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    expected={};rows=[];manifest=json.loads((src/'manifest.json').read_text())
    for r in manifest:
        if r['kernel'] not in expected:expected[r['kernel']]=recover(src/r['source'])[0]
        try:
            text,info=recover(src/r['file'],out/r['file'])
            if text!=expected[r['kernel']]:raise AssertionError('canonical expression mismatch '+r['file'])
        except q.Unsupported as e:
            rows.append(dict(r,status='unsupported',reason=str(e)));q.save(out/'analysis.json',rows);continue
        rows.append(dict(r,status='recovered',analysis=info,sha256=q.digest(out/r['file'])))
        q.save(out/'analysis.json',rows)
    ok=[r for r in rows if r['status']=='recovered'];q.save(out/'manifest.json',ok);q.save(out/'models.json',json.loads((src/'models.json').read_text()))
    import subprocess
    subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
    print(json.dumps(dict(targets=len(rows),recovered=len(ok),unsupported=len(rows)-len(ok))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
