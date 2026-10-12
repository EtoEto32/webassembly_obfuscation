import importlib.util,pathlib,json,hashlib,random,itertools
ROOT=pathlib.Path(__file__).resolve().parent
dependency=pathlib.Path('C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/residue-state/experiment.py')
spec=importlib.util.spec_from_file_location('coefficient_kernel',dependency)
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
MASK=(1<<32)-1

def prepare(inputs):return [((v<<2)|(i//3))&MASK for i,v in enumerate(inputs)]
def coefficients_of_class(xs):
    # Independent reference enumeration, not the transformed push/merge.
    return [len(xs)]+[sum(__import__('math').prod(group) for group in itertools.combinations(xs,k))&MASK for k in range(1,4)]
def encode_reference(xs):return [coefficients_of_class([v for v in xs if v%4==r]) for r in range(4)]
def reference(xs,u):
    selector=(sum(xs)>>2)&1
    return [(2*v*v+(1+2*selector)*v+u+(2 if v%2 else 0))%(1<<32) for v in xs]
def step(groups,u):
    selector=((sum(row[1] for row in groups)&MASK)>>2)&1
    out=[[0,0,0,0] for _ in range(4)]
    for r,g in enumerate(groups):
        destination=(2*r*r+(1+2*selector)*r+u+2*(r&1))&3
        out[destination]=core.merge(out[destination],core.push(g,2,1+2*selector,u+2*(r&1),MASK),MASK)
    return out

def main():
    certificate=[]
    for selector,u in itertools.product(range(2),range(4)):
        destinations=[(2*r*r+(1+2*selector)*r+u+2*(r&1))%4 for r in range(4)]
        assert sorted(destinations)==list(range(4))
        certificate.append({'selector':selector,'u_mod4':u,'destinations':destinations})
    # The source preparation, not an input filter, establishes three lanes/class.
    rng=random.Random(1729)
    boundary=[0,1,2,3,0x3fffffff,0x40000000,0x7fffffff,0x80000000,0xffffffff]
    inputs=[{'values':[v]*12,'u':u,'rounds':n} for v,u,n in itertools.product(boundary,[0,1,2,3,0xffffffff],[0,1,2,3,15,31])]
    inputs += [{'values':[rng.getrandbits(32) for _ in range(12)],'u':rng.getrandbits(32),'rounds':rng.randrange(32)} for _ in range(1024)]
    errors=[];transitions=0;occupancy_errors=0;selectors=set();samples=[];digest=hashlib.sha256()
    for index,case in enumerate(inputs):
        xs=prepare(case['values']);groups=core.encode(xs,MASK)
        assert [g[0] for g in groups]==[3]*4
        for iteration in range(case['rounds']):
            selectors.add(((sum(g[1] for g in groups)&MASK)>>2)&1)
            groups=step(groups,case['u']);xs=reference(xs,case['u'])
            expected=encode_reference(xs)
            if groups!=expected: errors.append({'case':index,'iteration':iteration,'expected':expected,'actual':groups})
            if [g[0] for g in groups]!=[3]*4:occupancy_errors+=1
            digest.update(json.dumps(groups,separators=(',',':')).encode())
            if index in [1,91,269,270,271]:samples.append({'case':index,'iteration':iteration,'groups':groups,'source_values':xs[:]})
            transitions+=1
    result={'cases':len(inputs),'transitions':transitions,'failure_count':len(errors),'failures':errors[:16],'occupancy_errors':occupancy_errors,'selectors_observed':sorted(selectors),'trace_sha256':digest.hexdigest(),'dependency_sha256':hashlib.sha256(dependency.read_bytes()).hexdigest(),'seed':1729,'routing_certificate':certificate}
    (ROOT/'inputs.json').write_text(json.dumps(inputs))
    (ROOT/'samples.json').write_text(json.dumps(samples,indent=2))
    (ROOT/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result));assert not errors and not occupancy_errors
if __name__=='__main__':main()
