"""Post-hoc mechanism diagnostic on exactly the frozen candidate pool."""
import argparse, hashlib, json, time
from pathlib import Path
import core

def run(d):
    dest=d/'ablation.json'
    if dest.exists():raise ValueError('Refuse overwrite')
    plan=json.loads((d/'plan.json').read_text());rows=[]
    for name,source in plan['programs'].items():
        wanted=plan['targets'][name]
        if wanted is None:rows.append({'program':name,'status':'no_target'});continue
        pool,stats=core.generate(source);start=time.perf_counter();keep=core.frontier(pool);filtertime=time.perf_counter()-start
        profiles={core.key(t):core.profile(t) for t in pool}
        assert all(any(core.dominates(profiles[core.key(k)],profiles[core.key(t)]) for k in keep) for t in pool)
        start=time.perf_counter();scores={}
        for t in pool:
            r=core.recover_two(t,wanted)
            scores[core.key(t)]=r
        scoringtime=time.perf_counter()-start
        def rank(t):
            r=scores[core.key(t)];score=r['cost'] if r['cost'] is not None else (3 if r['status'].startswith('not_found') else -1)
            return (-score,core.cost(t),core.key(t))
        choices={'observation_frontier':min(keep,key=rank),'no_frontier':min(pool,key=rank),
          'cost_only':min(pool,key=lambda t:(core.cost(t),core.key(t))),
          'max_size_diagnostic':min(pool,key=lambda t:(-core.cost(t),core.key(t)))}
        choices={label:{'tree':t,'cost':core.cost(t),'recovery':scores[core.key(t)]} for label,t in choices.items()}
        measured=json.loads((d/name/'frontier.wasm.json').read_text())['regions'][0]['chosen']
        assert choices['observation_frontier']['tree']==measured
        rows.append({'program':name,'pool':stats,'retained':len(keep),'dominance_coverage':True,
          'filter_seconds':filtertime,'all_scoring_seconds':scoringtime,'choices':choices,
          'recovery_distribution':{str(k):sum(r['cost']==k for r in scores.values()) for k in (0,1,2,None)}})
    dest.write_text(json.dumps({'rows':rows,'planSHA256':hashlib.sha256((d/'plan.json').read_bytes()).hexdigest(),
       'scope':'Post-hoc exact algebraic diagnostic, not an added pre-registered Wasm performance condition. Max-size is not SaMBA implementation.',
       'interpretation':'Removing frontier and retaining target-based scoring isolates the filtering mechanism. Same outcome means no demonstrated security benefit from filtering.'},indent=2))
    print(json.dumps([{k:r[k] for k in ('program','retained','recovery_distribution') if k in r} for r in rows]))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);run(ap.parse_args().directory)
