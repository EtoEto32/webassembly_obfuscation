"""i32 search with exact solver validation; sample-bank exhaustion is NOT UNSAT."""
import json,itertools,random,os,sys,time
from pathlib import Path
from search import build_bank
sys.path.insert(0,os.environ.get('WASM_SYNTH_DEPENDENCIES',r'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\encoding-synthesis-python'))
import z3
ROOT=Path(__file__).resolve().parent

def symbolic(tree,env):
    if isinstance(tree,str): return env[tree]
    name,l,r=tree; x=symbolic(l,env); y=symbolic(r,env)
    return {'add':lambda:x+y,'sub':lambda:x-y,'xor':lambda:x^y,
            'and':lambda:x&y,'or':lambda:x|y,'mul':lambda:x*y}[name]()

def check(trees,width):
    a,b,u=z3.BitVecs('a b u',width)
    env={'a':a,'b':b,'u':u,'zero':z3.BitVecVal(0,width),'one':z3.BitVecVal(1,width)}
    lhs=symbolic(trees[0],env)^symbolic(trees[1],env)
    rhs=(a^b)+u
    solver=z3.SolverFor('QF_BV'); solver.set(timeout=3000,random_seed=5460801)
    solver.add(lhs!=rhs); start=time.perf_counter(); verdict=solver.check()
    result={'width':width,'result':str(verdict),'seconds':time.perf_counter()-start}
    if verdict==z3.sat:
        m=solver.model(); result['counterexample']=[m.eval(v,model_completion=True).as_long() for v in [a,b,u]]
    if verdict==z3.unknown: result['reason']=solver.reason_unknown()
    return result

def main():
    dest=ROOT/'i32-results.json'
    if dest.exists(): raise SystemExit('Refuse overwrite')
    small=json.loads((ROOT/'results.json').read_text())
    imported={k:[check(v['trees'],w) for w in [2,3,32]] for k,v in small['chosen'].items() if v}
    rng=random.Random(5460801)
    samples=list(itertools.product(range(4),repeat=3))+[tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(12)]
    rounds=[]
    for iteration in range(4):
        start=time.perf_counter(); bank,_,attempts,levels=build_bank(32,3,samples)
        target=tuple(((a^b)+u)&0xffffffff for a,b,u in samples)
        matches=[]
        for right in bank.values():
            wanted=tuple(t^r for t,r in zip(target,right['sig']))
            for exposed in [False,True]:
                left=bank.get((wanted,exposed))
                if left is not None:
                    matches.append({'trees':[left['tree'],right['tree']], 'cost':left['cost']+right['cost'],
                                    'sample_exposes_x':left['exposes_x'] or right['exposes_x']})
        matches.sort(key=lambda m:(m['cost'],json.dumps(m['trees'])))
        selected={}; new=[]
        for name,allowed in [('correctness_only',lambda m:True),('no_direct_x_intermediate',lambda m:not m['sample_exposes_x'])]:
            chosen=next((m.copy() for m in matches if allowed(m)),None)
            if chosen:
                chosen['proof']=check(chosen['trees'],32)
                if chosen['proof']['result']=='sat': new.append(chosen['proof']['counterexample'])
            selected[name]=chosen
        rounds.append({'iteration':iteration,'samples':samples.copy(),'attempts':attempts,'levels':levels,
                       'bank_entries':len(bank),'matches':len(matches),'selected':selected,'seconds':time.perf_counter()-start})
        if not new: break
        for sample in new:
            if tuple(sample) not in samples: samples.append(tuple(sample))
    result={'z3':z3.get_version_string(),'imported_small_width_checks':imported,'rounds':rounds,
            'limitations':['Fixed XOR encoding is a control, not a synthesized new encoding.',
                           'All candidates are recovered by XOR of incoming a,b.',
                           'No match in the sampled semantic bank is not a grammar-wide impossibility proof.',
                           'No direct intermediate is only a heuristic, not decoder resistance.',
                           'No Wasm binaries or runtime-performance comparison.']}
    dest.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'imported':imported,'rounds':[{'iteration':r['iteration'],'selected':r['selected'],'matches':r['matches']} for r in rounds]}),flush=True)

if __name__=='__main__': main()
