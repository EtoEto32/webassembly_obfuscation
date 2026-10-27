"""Universal arbitrary-switching certificate for a finite family of correctors."""
import itertools
import json
from pathlib import Path
import sys
import screen


def verify(n,correctors,records=False):
    bound=0;cert=[]
    for tables,f in screen.triangular(n):
        target=next(s for s in range(1<<n) if f[s]==s)
        edges=[sorted({f[s]^N[s^f[s]] for N in correctors}) for s in range(1<<n)]
        if edges[target]!=[target]:return {'valid':False,'reason':'root not absorbing'}
        memo={target:0};active=[]
        def visit(s):
            if s in memo:return memo[s]
            if s in active:raise ValueError(active[active.index(s):]+[s])
            active.append(s);value=1+max(visit(v) for v in edges[s]);active.pop();memo[s]=value;return value
        try:local=max(visit(s) for s in range(1<<n))
        except ValueError as e:return {'valid':False,'source_tables':tables,'source_map':f,'target':target,'edges':edges,'cycle':e.args[0]}
        bound=max(bound,local)
        if records:cert.append({'source_tables':tables,'target':target,'ranks':[memo[s] for s in range(1<<n)],'edges':edges})
    return {'valid':True,'bound':bound,'certificates':cert}


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    a2=[0,0,1,2];a3=[0,2,3,0,0,2,0,0];b3=[0,4,3,0,0,0,0,0]
    options=[]
    for tail in itertools.product(range(4),repeat=3):
        b2=[0,*tail]
        if b2!=a2:
            r=verify(2,[a2,b2])
            if r['valid']:options.append({'N':b2,'bound':r['bound']})
    chosen=options[0]['N'];results={'dimension2':{'family':[a2,chosen],**verify(2,[a2,chosen],True),'other_options':options},
                                 'dimension3':{'family':[a3,b3],**verify(3,[a3,b3],True)},
                                 'unsafe_switching':{'family':[a3,[0]*8],**verify(3,[a3,[0]*8],True)}}
    assert results['dimension2']['valid'] and results['dimension3']['valid'] and not results['unsafe_switching']['valid']
    (out/'certificates.json').write_text(json.dumps(results,indent=2));print(json.dumps({'N2_B':chosen,'bound2':results['dimension2']['bound'],'bound3':results['dimension3']['bound'],'unsafe_cycle':results['unsafe_switching']['cycle']}))

if __name__=='__main__':main(sys.argv[1])
