"""Finite check of observation-set dominance for pure expression synthesis."""
from dataclasses import dataclass
from pathlib import Path
import itertools,json,time
ROOT=Path(__file__).resolve().parent
OPS=('add','sub','xor','mul')

def apply(name,x,y,mask):
    return {'add':lambda:(x+y)&mask,'sub':lambda:(x-y)&mask,
            'xor':lambda:x^y,'mul':lambda:(x*y)&mask}[name]()

@dataclass
class Term:
    sig: tuple
    seen: frozenset
    cost: int
    tree: object

def dominates(p,q):
    return p.sig==q.sig and p.cost<=q.cost and p.seen<=q.seen

def generate(mode,maxcost=3):
    states=list(itertools.product(range(4),repeat=2)); levels=[]; groups={}; attempts=0
    leaves=[]
    for name,fn in [('a',lambda a,b:a),('b',lambda a,b:b),('zero',lambda a,b:0),('one',lambda a,b:1)]:
        sig=tuple(fn(*s) for s in states)
        t=Term(sig,frozenset(),0,name); leaves.append(t); groups[sig]=[t]
    base={t.sig for t in leaves}; levels.append(leaves)
    for cost in range(1,maxcost+1):
        added=[]
        for lc in range(cost):
            rc=cost-1-lc
            for p in levels[lc]:
                for q in levels[rc]:
                    for op in OPS:
                        attempts+=1
                        sig=tuple(apply(op,x,y,3) for x,y in zip(p.sig,q.sig))
                        seen=p.seen|q.seen|({sig} if sig not in base else set())
                        t=Term(sig,frozenset(seen),cost,[op,p.tree,q.tree]); existing=groups.setdefault(sig,[])
                        if mode=='output_only':
                            if existing: continue
                        elif mode=='frontier':
                            if any(dominates(old,t) for old in existing): continue
                            existing[:]=[old for old in existing if not dominates(t,old)]
                        elif mode=='all_profiles':
                            if any(old.cost<=cost and old.seen==t.seen for old in existing): continue
                        else: raise ValueError(mode)
                        existing.append(t); added.append(t)
        # A same-cost term can have been removed by a later dominator.
        retained=[t for t in added if any(t is x for x in groups[t.sig])]
        levels.append(retained)
    return groups,{'attempts':attempts,'levels':[len(x) for x in levels],'profiles':sum(map(len,groups.values()))}

def evaltree(t,a,b,c,mask,seen):
    if isinstance(t,str): return {'a':a,'b':b,'c':c}[t]
    name,l,r=t; value=apply(name,evaltree(l,a,b,c,mask,seen),evaltree(r,a,b,c,mask,seen),mask)
    seen.append(value); return value

def profile_counterexample():
    states=list(itertools.product(range(8),repeat=3))
    p=['add',['add','a','b'],'c']; q=['add','a',['add','b','c']]
    common=['mul','c','c']
    target=tuple(((a+b)*c*c)&7 for a,b,c in states)
    base=[tuple(s[i] for s in states) for i in range(3)]
    def signatures(t):
        rows=[]
        for s in states:
            trace=[]; evaltree(t,*s,7,trace); rows.append(trace)
        return [tuple(row[i] for row in rows) for i in range(len(rows[0]))]
    def can_recover(atoms):
        if target in atoms: return True
        return any(tuple(apply(op,x,y,7) for x,y in zip(l,r))==target for op in OPS for l in atoms for r in atoms)
    return {'P':p,'Q':q,'context':['add','HOLE',common],'target':'(a+b)*c*c mod 8','domain_size':len(states),
            'before':{'P':can_recover(base+signatures(p)),'Q':can_recover(base+signatures(q))},
            'after':{'P':can_recover(base+signatures(['add',p,common])),'Q':can_recover(base+signatures(['add',q,common]))}}

def main():
    if (ROOT/'results.json').exists(): raise SystemExit('Refuse overwrite')
    banks={}; stats={}
    for mode in ['all_profiles','frontier','output_only']:
        start=time.perf_counter(); banks[mode],stats[mode]=generate(mode)
        stats[mode]['seconds']=time.perf_counter()-start
        print(json.dumps({mode:stats[mode]}),flush=True)
    coverage=0; failures=[]; discarded_by_output=[]
    for sig,terms in banks['all_profiles'].items():
        for t in terms:
            coverage+=1
            if not any(dominates(p,t) for p in banks['frontier'].get(sig,[])): failures.append(t.tree)
            if not any(dominates(p,t) for p in banks['output_only'].get(sig,[])):
                if len(discarded_by_output)<8: discarded_by_output.append({'lost':t.tree,'cost':t.cost,'retained':banks['output_only'][sig][0].tree})
    example=profile_counterexample()
    result={'width':2,'inputs':['a','b'],'max_tree_operations':3,'operations':OPS,'stats':stats,
            'coverage_checks':coverage,'frontier_coverage_failures':failures,'output_only_lost_examples':discarded_by_output,
            'target_profile_not_context_closed':example}
    (ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'coverage':coverage,'failures':len(failures),'counterexample':example}),flush=True)
    assert not failures
    assert example['before']=={'P':False,'Q':False} and example['after']=={'P':True,'Q':False}

if __name__=='__main__': main()
