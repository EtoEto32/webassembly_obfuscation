"""Finite SSA-expression bank and two-output join. Not a new obfuscator."""
import itertools, json, time, random, platform
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OPS=('add','sub','xor','and','or','mul')
COMM={'add','xor','and','or','mul'}

def op(name,a,b,mask):
    if name=='add': return (a+b)&mask
    if name=='sub': return (a-b)&mask
    if name=='xor': return a^b
    if name=='and': return a&b
    if name=='or': return a|b
    if name=='mul': return (a*b)&mask
    raise ValueError(name)

def evaluate(tree,a,b,u,mask,trace=None):
    if isinstance(tree,str): return {'a':a,'b':b,'u':u,'zero':0,'one':1}[tree]
    name,l,r=tree
    v=op(name,evaluate(l,a,b,u,mask,trace),evaluate(r,a,b,u,mask,trace),mask)
    if trace is not None: trace.append(v)
    return v

def build_bank(width,max_cost,states=None):
    mask=(1<<width)-1
    if states is None: states=list(itertools.product(range(mask+1),repeat=3))
    # Retain cheapest expression for each semantics, and separately whether its
    # chosen implementation contains an intermediate equal to the old x=a^b.
    target_x=tuple(a^b for a,b,u in states)
    bank={}; levels=[]; attempted=0
    leaf=[]
    for name in ['a','b','u','zero','one']:
        sig=tuple(evaluate(name,*s,mask) for s in states)
        item={'tree':name,'sig':sig,'cost':0,'exposes_x':False}
        bank[(sig,False)]=item; leaf.append(item)
    levels.append(leaf)
    for cost in range(1,max_cost+1):
        level=[]
        for lc in range(cost):
            rc=cost-1-lc
            for left in levels[lc]:
                for right in levels[rc]:
                    for name in OPS:
                        if name in COMM and (lc>rc or (lc==rc and left['sig']>right['sig'])): continue
                        attempted+=1
                        sig=tuple(op(name,a,b,mask) for a,b in zip(left['sig'],right['sig']))
                        exposed=left['exposes_x'] or right['exposes_x'] or sig==target_x
                        key=(sig,exposed)
                        if key in bank: continue
                        item={'tree':[name,left['tree'],right['tree']],'sig':sig,'cost':cost,'exposes_x':exposed}
                        bank[key]=item; level.append(item)
        levels.append(level)
        print(json.dumps({'cost':cost,'new_entries':len(level),'attempted':attempted}),flush=True)
    return bank,states,attempted,[len(x) for x in levels]

def verify(pair,width,states):
    mask=(1<<width)-1; errors=[]; checked=0
    for a,b,u in states:
        ap=evaluate(pair[0],a,b,u,mask); bp=evaluate(pair[1],a,b,u,mask)
        expected=((a^b)+u)&mask; actual=ap^bp
        checked+=1
        if actual!=expected and len(errors)<8: errors.append({'input':[a,b,u],'expected':expected,'actual':actual})
    return {'checked':checked,'counterexamples':errors}

def main():
    if (ROOT/'results.json').exists(): raise SystemExit('Refuse to overwrite saved results')
    start=time.perf_counter(); bank,states,attempted,levels=build_bank(2,3)
    target=tuple(((a^b)+u)&3 for a,b,u in states)
    matches=[]
    for right in bank.values():
        wanted=tuple(t^r for t,r in zip(target,right['sig']))
        for exposed in [False,True]:
            left=bank.get((wanted,exposed))
            if left is None: continue
            matches.append({'trees':[left['tree'],right['tree']], 'cost':left['cost']+right['cost'],
                            'exposes_x':left['exposes_x'] or right['exposes_x']})
    matches.sort(key=lambda x:(x['cost'],json.dumps(x['trees'])))
    chosen={}
    for mode,accept in [('correctness_only',lambda m:True),('no_direct_x_intermediate',lambda m:not m['exposes_x'])]:
        selected=next((m.copy() for m in matches if accept(m)),None)
        if selected is None: chosen[mode]=None; continue
        selected['checks']={str(w):verify(selected['trees'],w,itertools.product(range(1<<w),repeat=3)) for w in [2,3,4]}
        rng=random.Random(0x535341)
        bounds=[0,1,2,3,4,7,8,15,16,0x7fffffff,0x80000000,0xffffffff]
        tests=list(itertools.product(bounds,repeat=3))+[tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(1024)]
        selected['checks']['32_samples']=verify(selected['trees'],32,tests)
        # Actual observations include incoming a,b. A one-operation decoder is
        # available regardless of the intermediate-exposure flag.
        selected['checkpoint_decoder']={'expression':['xor','a','b'],'valid_by_encoding_definition':True}
        chosen[mode]=selected
    result={'python':platform.python_version(),'width':2,'max_expression_cost':3,
            'states':len(states),'operations':OPS,'levels':levels,'attempted_expressions':attempted,
            'bank_entries':len(bank),'pair_matches':len(matches),'chosen':chosen,
            'seconds':time.perf_counter()-start,'seed_i32':0x535341,
            'claim':'Finite update synthesis controls only; no new obfuscation algorithm, no Wasm execution.'}
    (ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)

if __name__=='__main__': main()
