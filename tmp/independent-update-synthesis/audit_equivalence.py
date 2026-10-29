import pathlib,json,itertools
root=pathlib.Path(__file__).resolve().parent
results=[]
for name in ['fixed','joint']:
    saved=json.loads((root/(name+'.json')).read_text())
    m=saved['rounds'][-1]['model']; k,l=m['k'],m['l']
    branches=[]
    for branch,c in enumerate([5,3]):
        # Independently expanded T(a+k*b^2+l*b,u)-k*(b+1)^2-l*(b+1).
        canonical=[-k-l,c,-2*k+(c-1)*l,1,2*l,l*l+(c-1)*k,2*k,2*k*l,k*k,1]
        canonical=[v%16 for v in canonical]
        delta=[(v-w)%16 for v,w in zip(m['updates'][branch],canonical)]
        failures=[]
        for a,b,u in itertools.product(range(16),repeat=3):
            terms=[1,a,b,a*a,a*b,b*b,a*b*b,b**3,b**4,u]
            difference=sum(v*t for v,t in zip(delta,terms))%16
            if difference: failures.append([a,b,u,difference])
        branches.append({'branch':branch,'canonical':canonical,'synthesized':m['updates'][branch],'delta':delta,'all_states':4096,'delta_nonzero_cases':len(failures),'first_counterexamples':failures[:16]})
    results.append({'mode':name,'encoding':{'k':k,'l':l},'branches':branches})
(root/'equivalence.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
