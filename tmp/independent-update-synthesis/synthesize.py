import sys, json, time, itertools, pathlib, random, os
sys.path.insert(0, os.environ.get('WASM_SYNTH_DEPENDENCIES', str(pathlib.Path(__file__).resolve().parents[2] / '.tools' / 'encoding-synthesis-python')))
import z3

ROOT = pathlib.Path(__file__).resolve().parent
def basis(a,b,u):
    return [1,a,b,a*a,a*b,b*b,a*b*b,b**3,b**4,u]

def check(model, width, states):
    mask=(1<<width)-1
    k,l=model['k'],model['l']
    failures=[]
    tested=0
    for a,b,u in states:
        tested+=1
        coeff=model['updates'][u&1]
        ap=sum(c*v for c,v in zip(coeff,basis(a,b,u)))&mask
        bp=(b+1)&mask
        x=(a+k*b*b+l*b)&mask
        expected=(x*x+(3 if u&1 else 5)*x+u)&mask
        actual=(ap+k*bp*bp+l*bp)&mask
        if actual!=expected and len(failures)<16:
            failures.append({'state':[a,b,u],'expected':expected,'actual':actual})
    return {'tested':tested,'counterexamples':failures}

def run(mode):
    s=z3.Solver(); s.set(timeout=10000,random_seed=1729)
    k,l=z3.BitVecs('k l',4)
    cs=[[z3.BitVec(f'c{branch}_{i}',4) for i in range(10)] for branch in range(2)]
    s.add(k&1==1)
    if mode=='fixed': s.add(k==1,l==0)
    def add(state):
        a,b,u=state
        x=a+k*b*b+l*b
        ap=sum(c*(v&15) for c,v in zip(cs[u&1],basis(a,b,u)))
        bp=(b+1)&15
        s.add(ap+k*bp*bp+l*bp==x*x+(3 if u&1 else 5)*x+u)
    for state in [(0,0,0),(1,0,1),(0,1,0),(15,15,15)]: add(state)
    record={'mode':mode,'z3':z3.get_version_string(),'rounds':[],'status':'running'}
    dest=ROOT/(mode+'.json')
    for iteration in range(60):
        start=time.perf_counter(); result=s.check(); elapsed=time.perf_counter()-start
        entry={'iteration':iteration,'solver_status':str(result),'solver_seconds':elapsed}
        if result!=z3.sat:
            record['status']=str(result)
            if result==z3.unknown: entry['reason']=s.reason_unknown()
            record['rounds'].append(entry); dest.write_text(json.dumps(record,indent=2)); break
        m=s.model()
        model={'k':m.eval(k,model_completion=True).as_long(),'l':m.eval(l,model_completion=True).as_long(),'updates':[[m.eval(c,model_completion=True).as_long() for c in row] for row in cs]}
        verification=check(model,4,itertools.product(range(16),repeat=3))
        entry.update(model=model,verification=verification)
        record['rounds'].append(entry)
        if not verification['counterexamples']:
            record['status']='verified_4bit'
            # Deliberately literal zero-extension, not an inferred polynomial lift.
            rng=random.Random(1729)
            boundaries=[0,1,2,15,16,0x7fffffff,0x80000000,0xffffffff]
            states=list(itertools.product(boundaries,repeat=3))+[tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(1024)]
            record['literal_unsigned_i32_lift']=check(model,32,states)
            dest.write_text(json.dumps(record,indent=2)); break
        dest.write_text(json.dumps(record,indent=2))
        for item in verification['counterexamples']: add(item['state'])
    else:
        record['status']='round_limit'; dest.write_text(json.dumps(record,indent=2))
    print(json.dumps({'mode':mode,'status':record['status'],'rounds':len(record['rounds']),'model':record['rounds'][-1].get('model'),'lift':record.get('literal_unsigned_i32_lift')}),flush=True)

if __name__=='__main__':
    for mode in ['fixed','joint']: run(mode)
