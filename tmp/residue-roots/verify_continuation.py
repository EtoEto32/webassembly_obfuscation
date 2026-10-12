import pathlib,json,collections,random
ROOT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/residue-occupancy')
MASK=(1<<32)-1
def step(values,u):
    selector=(sum(values)>>2)&1
    return [(2*x*x+(1+2*selector)*x+u+2*(x%2))&MASK for x in values]
def coefficients(values):
    out=[1,0,0,0]
    for v in values:
        for j in [3,2,1]:out[j]=(out[j]+v*out[j-1])&MASK
    return out[1:]
inputs=json.loads((SRC/'wasm-inputs.json').read_text())
recovered=json.loads((ROOT/'joint-recovery.json').read_text())
by_case=collections.defaultdict(list)
for row in recovered:by_case[(row['file'],row['input_index'])].append(row)
summary=[];rng=random.Random(1729)
for (file,index),rows in by_case.items():
    case=inputs[index];values=[((v<<2)|(i//3))&MASK for i,v in enumerate(case['values'])]
    for _ in range(case['rounds']&31):values=step(values,case['u'])
    matches=[]
    for row in rows:
        if row['values'] is not None:matches.append(sorted(row['values'])==sorted(v for v in values if v%4==row['residue']))
    record={'file':file,'input_index':index,'recovered_groups':len(matches),'historical_multiset_matches':sum(matches)}
    if len(matches)==4:
        alternate=[v for row in rows for v in row['values']];future=[]
        for _ in range(7):
            u=rng.getrandbits(32);values=step(values,u);alternate=step(alternate,u)
            expected=coefficients(values);actual=coefficients(alternate)
            groups_equal=all(coefficients([v for v in values if v%4==r])==coefficients([v for v in alternate if v%4==r]) for r in range(4))
            future.append({'u':u,'expected':expected,'actual':actual,'all_group_coefficients_equal':groups_equal})
            assert expected==actual and groups_equal
        record['continuation']=future
    summary.append(record)
(ROOT/'continuation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'recovered_groups':sum(r['recovered_groups'] for r in summary),'historical_multiset_matches':sum(r['historical_multiset_matches'] for r in summary),'complete_instances':sum('continuation' in r for r in summary),'future_steps':sum(len(r.get('continuation',[])) for r in summary)}))
