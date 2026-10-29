import argparse,itertools,json,random
from pathlib import Path
import prototype as p

def nu(v,w):
    v&=(1<<w)-1
    return w if not v else (v&-v).bit_length()-1
def score(v,r,w):return min(len(v)*nu(x-y,w)+i for i,(x,y) in enumerate(zip(v,r)))
def one_step():
    rows=[]
    for w in (1,2):
        q=1<<w;checks=0
        matrices=list(itertools.product(range(1,q,2),range(0,q,2),range(q),range(1,q,2)))
        for r in itertools.product(range(q),repeat=2):
            for v in itertools.product(range(q),repeat=2):
                for f1 in range(q):
                    if (f1-r[1])% (1<<nu(v[0]-r[0],w)):continue
                    e=(v[0]-r[0],v[1]-f1)
                    for a,b,c,d in matrices:
                        h=((v[0]-a*e[0]-b*e[1])%(q),(v[1]-c*e[0]-d*e[1])%q)
                        assert h==r if v==r else score(h,r,w)>score(v,r,w)
                        checks+=1
        rows.append(dict(width=w,cases=checks,matrices_per_point=len(matrices)))
    return rows

def run(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);rows=one_step();cases=[]
    # A true discontinuity in the usual 2-adic metric, with convergence intact.
    for w in (4,8,16,32):
        mask=(1<<w)-1
        def h(v):
            rot=((v<<2)|(v>>(w-2)))&mask
            return (v-(rot|1)*v)&mask
        a,b=1,1+(1<<(w-1));ua,ub=h(a),h(b)
        assert nu(a-b,w)==w-1 and nu(ua-ub,w)==1
        initial=range(1<<w) if w<=8 else [random.Random(w+k).getrandbits(w) for k in range(512)]
        count=0;max_steps=0
        for v in initial:
            steps=0
            while v:
                before=nu(v,w);v=h(v);steps+=1;assert nu(v,w)>before and steps<=w
            count+=1;max_steps=max(max_steps,steps)
        cases.append(dict(width=w,pair=[a,b],images=[ua,ub],input_valuation=w-1,output_valuation=1,initial_states=count,max_steps=max_steps))
    p.save(out/'model.json',dict(pointwise_descent=rows,pointwise_cases=sum(x['cases'] for x in rows),noncongruent=cases,convergence_cases=sum(x['initial_states'] for x in cases),scope='Exhaustive admissible local transitions for n=2,w=1,2; exhaustive scalar starts at w=4,8; sampled starts at w=16,32. Not enumeration of every function M.'))
    p.save(out/'pins.json',{f.name:p.digest(f) for f in out.iterdir() if f.is_file()});print(json.dumps(dict(pointwise_cases=sum(x['cases'] for x in rows),convergence_cases=sum(x['initial_states'] for x in cases))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
