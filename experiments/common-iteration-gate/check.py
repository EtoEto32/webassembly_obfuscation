"""Exact finite feasibility checks for common-step instruction execution."""
import hashlib,itertools,json,platform
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results.json'
if OUT.exists():raise SystemExit('Refuse overwrite results')
def compose(f,g):return tuple(f[x] for x in g)
def steps(u,x,count):
    for _ in range(count):x=u[x]
    return x
maps=list(itertools.product(range(4),repeat=4));identity=tuple(range(4))
common={};power_lengths=Counter()
for u in maps:
    powers=[];p=identity
    while p not in powers:
        powers.append(p);p=compose(u,p)
    power_lengths[len(powers)]+=1
    for i,f in enumerate(powers):
        for j,g in enumerate(powers):
            common.setdefault((f,g),{'U':u,'counts':[i,j]})
commuting=0;commuting_without=None
for f,g in itertools.product(maps,repeat=2):
    c=compose(f,g)==compose(g,f);commuting+=c
    if (f,g) in common:
        assert c
        witness=common[f,g]
        for x in range(4):
            assert steps(witness['U'],x,witness['counts'][0])==f[x]
            assert steps(witness['U'],x,witness['counts'][1])==g[x]
    elif c and commuting_without is None:commuting_without={'f':f,'g':g}
add=tuple((x+1)%4 for x in range(4));xor=tuple(x^1 for x in range(4));add2=tuple((x+2)%4 for x in range(4))
assert (add,xor) not in common and (add,add2) in common
noncommute={'x':0,'add_after_xor':add[xor[0]],'xor_after_add':xor[add[0]]}
assert noncommute['add_after_xor']!=noncommute['xor_after_add']

# All cycles are written starting with label 0: exactly (N-1)! cycles.
cycle_rows=[];variable_transition_checks=0;general_map_checks=0
for n in [2,4,8]:
    rows=[]
    for tail in itertools.permutations(range(1,n)):
        order=(0,)+tail;position={x:i for i,x in enumerate(order)}
        u=[0]*n
        for i,x in enumerate(order):u[x]=order[(i+1)%n]
        timings=[]
        for target in [lambda x:(x+1)%n,lambda x:x^1]:
            counts=[(position[target(x)]-position[x])%n for x in range(n)]
            for x,c in enumerate(counts):
                assert steps(u,x,c)==target(x);variable_transition_checks+=1
            timings.append(counts)
        assert sum(timings[1])==n*n//2
        rows.append({'cycle':order,'add_counts':timings[0],'xor_counts':timings[1],'worst':max(timings[0]+timings[1])})
        if n==4:
            for f in maps:
                counts=[(position[f[x]]-position[x])%n for x in range(n)]
                for x,c in enumerate(counts):
                    assert steps(u,x,c)==f[x];general_map_checks+=1
    (ROOT/f'cycles-{n}.json').write_text(json.dumps(rows,indent=2))
    best=min(rows,key=lambda r:r['worst'])
    cycle_rows.append({'states':n,'cycles':len(rows),'xor_mean_steps':n/2,'minimum_joint_worst_steps':best['worst'],'best_example':best,'worst_histogram':dict(sorted(Counter(r['worst'] for r in rows).items()))})

# Independently test the graph claim at four points: if x+1 is reachable from
# every x by iterating U, then U is a full cycle. Reachability uses a visited walk.
reachability_maps=[]
for u in maps:
    ok=True
    for x in range(4):
        seen=set();v=x
        while v not in seen:seen.add(v);v=u[v]
        if (x+1)%4 not in seen:ok=False;break
    if ok:
        assert len({steps(u,0,k) for k in range(4)})==4 and steps(u,0,4)==0
        reachability_maps.append(u)
assert len(reachability_maps)==6

# A concrete Before/After, generated from the minimizing eight-state cycle.
best8=cycle_rows[-1]['best_example'];order=best8['cycle'];u=[0]*8
for i,x in enumerate(order):u[x]=order[(i+1)%8]
sample={'before':{'add_one':[(x+1)%8 for x in range(8)],'xor_one':[x^1 for x in range(8)]},'after':{'U':u,'add_counts':best8['add_counts'],'xor_counts':best8['xor_counts']},'pseudocode':'z=x; repeat counts[operation][x] times: z=U[z]; return z','scope':'Generated finite lookup representation, not a Wasm transform; the count tables carry operation-specific semantics'}
(ROOT/'sample.json').write_text(json.dumps(sample,indent=2))
result={'python':platform.python_version(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'fixed_counts':{'maps':256,'ordered_pairs':65536,'commuting_pairs':commuting,'common_power_pairs':len(common),'power_length_histogram':dict(power_lengths),'commuting_without_common_generator':commuting_without,'noncommuting_target_witness':noncommute,'positive':common[add,add2]},'variable_counts':cycle_rows,'variable_transition_checks':variable_transition_checks,'all_four_state_map_transition_checks':general_map_checks,'add_reachable_maps':reachability_maps,'i32_average_xor_steps_from_theorem':1<<31,'decision':'Reject fixed-count candidate for expressiveness; reject same-word autonomous variable-count candidate for exponential microstep cost'}
OUT.write_text(json.dumps(result,indent=2))
print(json.dumps({'common_power_pairs':len(common),'commuting_pairs':commuting,'cycles':sum(r['cycles'] for r in cycle_rows),'variable_transition_checks':variable_transition_checks,'all_map_checks':general_map_checks,'minimum_joint_worst_steps_n8':cycle_rows[-1]['minimum_joint_worst_steps']}))
