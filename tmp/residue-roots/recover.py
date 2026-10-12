import pathlib,json,time,collections
ROOT=pathlib.Path(__file__).resolve().parent;MASK=(1<<32)-1
class Budget(Exception):pass
def recover(s,p,q,residue):
    count=0
    def evaluate(poly,x,mask):
        nonlocal count
        count+=1
        if count>20000:raise Budget()
        value=0
        for c in poly:value=(value*x+c)&mask
        return value
    def roots(poly,value,bits):
        if bits==32:
            yield value;return
        next_mask=(1<<(bits+1))-1
        for x in [value,value+(1<<bits)]:
            if evaluate(poly,x,next_mask)==0:yield from roots(poly,x,bits+1)
    def factor(poly):
        if len(poly)==2:
            root=(-poly[1])&MASK
            return [root] if root%4==residue else None
        if evaluate(poly,residue,3):return None
        for root in roots(poly,residue,2):
            quotient=[1]
            for c in poly[1:-1]:quotient.append((c+root*quotient[-1])&MASK)
            tail=factor(quotient)
            if tail is not None:return [root]+tail
        return None
    start=time.perf_counter()
    try:
        result=factor([1,(-s)&MASK,p,(-q)&MASK]);status='compatible_multiset' if result is not None else 'no_factorization'
    except Budget:result=None;status='budget_exhausted'
    if result is not None:
        x,y,z=result
        assert [(x+y+z)&MASK,(x*y+x*z+y*z)&MASK,(x*y*z)&MASK]==[s,p,q]
        assert all(x%4==residue for x in result)
    return {'status':status,'values':result,'polynomial_evaluations':min(count,20000),'seconds':time.perf_counter()-start}

rows=json.loads((ROOT/'coefficient-observations.json').read_text());out=[]
for index,row in enumerate(rows):
    result=recover(*row['coefficients'],row['residue']);out.append({**row,**result})
    (ROOT/'recovery.json').write_text(json.dumps(out))
summary={'groups':len(out),'status_counts':dict(collections.Counter(r['status'] for r in out)),'maximum_seconds':max(r['seconds'] for r in out),'total_evaluations':sum(r['polynomial_evaluations'] for r in out)}
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
