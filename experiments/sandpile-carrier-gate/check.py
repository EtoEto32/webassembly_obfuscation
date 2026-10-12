import hashlib
import json
import platform
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def stabilize(z, a, b, c, order=(0,1)):
    z=list(z)
    trace=[z[:]]
    # Bulk topplings are repeated legal single topplings at one vertex.
    while max(z)>=a:
        for vertex in order:
            count=z[vertex]//a
            if count:
                z[vertex]-=count*a
                z[1-vertex]+=count*(b if vertex==0 else c)
                trace.append(z[:])
                if len(trace)>129:
                    raise RuntimeError('toppling budget exceeded')
    return z,trace


def observer(topplings, modulus, one):
    # Derive a modular left invariant from the public change vectors.
    a=-topplings[0][0]
    b=topplings[0][1]
    v=[b,a]
    assert all(sum(x*y for x,y in zip(v,t))%modulus==0 for t in topplings)
    calibration=sum(x*y for x,y in zip(v,one))%modulus
    scale=pow(calibration,-1,modulus)
    return [(scale*x)%modulus for x in v]


def value(v,z,modulus):
    return sum(x*y for x,y in zip(v,z))%modulus


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'protocol.json').read_text())
    rng=random.Random(protocol['seed'])
    records=[]
    for w in protocol['widths']:
        m=1<<w
        a=(1<<(w//2))+1
        b=3
        assert (2*a-1)%b==0
        c=(2*a-1)//b
        assert a*a-b*c==m and a>b and a>c
        topplings=[[-a,b],[c,-a]]
        scales=[1,rng.randrange(m)|1,rng.randrange(m)|1]
        if w==4:
            pairs=[(x,y) for x in range(m) for y in range(m)]
        else:
            boundaries=sorted({0,1,2,m//2-1,m//2,m-2,m-1})
            pairs=[(x,y) for x in boundaries for y in boundaries]
            pairs += [(rng.randrange(m),rng.randrange(m)) for _ in range(1024)]
        for r in scales:
            def encode(x):
                return stabilize([(r*x)%m,0],a,b,c)[0]
            one=encode(1)
            v=observer(topplings,m,one)
            # This identity checks all x without enumerating 2^32 inputs.
            assert (v[0]*r)%m==1
            assert all(sum(x*y for x,y in zip(v,t))%m==0 for t in topplings)
            rows=[];negative=None;trace_checks=0;max_topplings=0
            for x,y in pairs:
                ex,ey=encode(x),encode(y)
                initial=[ex[i]+ey[i] for i in range(2)]
                result,trace=stabilize(initial,a,b,c)
                reverse,_=stabilize(initial,a,b,c,(1,0))
                assert result==reverse
                expected=(x+y)%m
                got=value(v,result,m)
                assert got==expected and value(v,ex,m)==x and value(v,ey,m)==y
                assert all(value(v,z,m)==expected for z in trace)
                trace_checks+=len(trace)
                max_topplings=max(max_topplings,len(trace)-1)
                wrong=value([(v[0]+1)%m,v[1]],ex,m)
                if negative is None and wrong!=x:
                    negative={'input':x,'encoded':ex,'wrong':wrong,'expected':x}
                rows.append({'x':x,'y':y,'encoded_x':ex,'encoded_y':ey,'sum':result,'recovered':got,'trace':trace})
            assert negative is not None
            records.append({'width':w,'scale':r,'topplings':topplings,'known_one':one,'recovered_coefficients':v,
                            'pairs':len(pairs),'trace_checks':trace_checks,'max_addition_bulk_topplings':max_topplings,
                            'negative':negative,'rows':rows})
    (out/'observations.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    summary={'python':platform.python_version(),'encodings':len(records),'pairs':sum(r['pairs'] for r in records),
             'operand_recoveries':2*sum(r['pairs'] for r in records),'sum_recoveries':sum(r['pairs'] for r in records),
             'trace_checks':sum(r['trace_checks'] for r in records),'mismatches':0,
             'cases':[{k:v for k,v in r.items() if k not in ['rows','negative']} for r in records],
             'hashes':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'protocol.json',HERE/'check.py',out/'observations.json']}}
    (out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['hashes','cases']},indent=2))


if __name__=='__main__':
    main()
