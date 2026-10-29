import hashlib
import itertools
import json
import platform
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ASSIGN=list(itertools.product((0,1),repeat=5))
ALL=(1<<32)-1


def basis(values):
    pivots={}
    for v in values:
        while v:
            p=v.bit_length()-1
            if p not in pivots:
                pivots[p]=v
                break
            v ^= pivots[p]
    return pivots


def contains(pivots,v):
    while v:
        p=v.bit_length()-1
        if p not in pivots: return False
        v ^= pivots[p]
    return True


def features(observations):
    values=[ALL]+list(observations.values())
    return values+[a&b for i,a in enumerate(values) for b in values[i:]]


def run_block(bits,excluded):
    observed={c:bits[i] for i,c in enumerate('abcde')}
    out=0
    ops=0
    for a,b in itertools.combinations('abcde',2):
        if a+b==excluded: continue
        value=observed[a]&observed[b]
        observed[a+b]=value
        out ^= value; observed[f'xor{ops}']=out
        out ^= value; observed[f'xor{ops+1}']=out
        ops+=3
    observed['out']=out
    return observed,ops


def run_context(obs,monomial):
    obs=dict(obs)
    value=obs[monomial[0]]
    for i,c in enumerate(monomial[1:],1):
        value &= obs[c]
        obs['context'+str(i)]=value
    obs['result']=obs['out']^value
    return obs


def signatures(traces):
    return {key:sum(row[key]<<i for i,row in enumerate(traces)) for key in traces[0]}


def main():
    path=ROOT/'results.json'
    if path.exists(): raise FileExistsError(path)
    traces={}
    costs={}
    for name,excluded in [('P','ac'),('Q','ab')]:
        runs=[run_block(bits,excluded) for bits in ASSIGN]
        traces[name]=[row for row,cost in runs]
        costs[name]=runs[0][1]
        assert all(row['out']==0 and cost==costs[name] for row,cost in runs)
    assert costs['P']==costs['Q']
    raw={name:signatures(rows) for name,rows in traces.items()}
    spaces={name:basis(features(obs)) for name,obs in raw.items()}
    assert all(contains(spaces['Q'],v) for v in spaces['P'].values())
    assert all(contains(spaces['P'],v) for v in spaces['Q'].values())
    target=sum(int(all(bits))<<i for i,bits in enumerate(ASSIGN))
    assert not contains(spaces['P'],target) and not contains(spaces['Q'],target)
    contexts=[]
    example=None
    for degree in (1,2,3):
        for letters in itertools.combinations('abcde',degree):
            monomial=''.join(letters)
            new={name:[run_context(row,monomial) for row in rows] for name,rows in traces.items()}
            sig={name:signatures(rows) for name,rows in new.items()}
            bs={name:basis(features(obs)) for name,obs in sig.items()}
            record=dict(context=monomial,ranks={name:len(b) for name,b in bs.items()},
                        recovered={name:contains(b,target) for name,b in bs.items()})
            contexts.append(record)
            if monomial=='cde':
                assert record['recovered']=={'P':True,'Q':False}
                assert sig['P']['ab'] & sig['P']['context2'] == target
                # Top-degree ANF coefficient is parity of the full Boolean table.
                # Every Q feature has zero coefficient; target has coefficient one.
                assert all(v.bit_count()%2==0 for v in features(sig['Q']))
                assert target.bit_count()%2==1
                assert all((p['ab']&p['context2'])==int(all(bits)) for bits,p in zip(ASSIGN,new['P']))
                example=dict(context=monomial,decoder='P.ab AND P.context2',
                             assignments=ASSIGN,traces=new,
                             Q_feature_count=len(features(sig['Q'])),
                             Q_nonzero_top_ANF_coefficients=0)
    assert len(contexts)==25 and example is not None
    result=dict(python=platform.python_version(),costs=costs,isolated_ranks={n:len(s) for n,s in spaces.items()},
                contexts=contexts,example=example,
                hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['check.py','protocol.json']})
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(costs=costs,isolated_ranks=result['isolated_ranks'],
                         separating=[c for c in contexts if c['recovered']['P']!=c['recovered']['Q']],
                         Q_feature_count=example['Q_feature_count']),indent=2))


if __name__=='__main__': main()
