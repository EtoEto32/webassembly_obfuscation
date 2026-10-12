import hashlib
import importlib.util
import itertools
import json
import platform
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
HELPER=HERE.parent/'quadratic-context-gate/check.py'
spec=importlib.util.spec_from_file_location('gf2',HELPER)
gf2=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gf2)
PAIRS=list(itertools.combinations(range(4),2))


def table(n,indices):
    return sum(int(all((x>>i)&1 for i in indices))<<x for x in range(1<<n))


def observations(mask,fresh):
    n=4+fresh
    values=[table(n,()),0]+[table(n,[i]) for i in range(n)]
    # acc starts zero, each pair is XORed twice: its only values are pair, zero.
    for j,pair in enumerate(PAIRS):
        if mask>>j&1:
            v=table(n,pair)
            values.extend([v,v,0])
    return sorted(set(values))


def products(values,d,n):
    # Squarefree products suffice because Boolean values are idempotent.
    yield (1<<(1<<n))-1
    for degree in range(1,d+1):
        for terms in itertools.combinations(values,degree):
            result=(1<<(1<<n))-1
            for v in terms:
                result &= v
            yield result


def coefficient(v,fresh):
    # Coefficient of r0*...*r(k-1), as a truth table on four old inputs.
    out=0
    for x in range(16):
        bit=0
        for r in range(1<<fresh):
            bit ^= (v>>(x|(r<<4)))&1
        out |= bit<<x
    return out


def subset(left,right):
    return all(gf2.contains(right,v) for v in left.values())


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((HERE/'protocol.json').read_text())
    linear=[gf2.basis(observations(mask,0)) for mask in range(64)]
    reports=[];total_certificates=0
    for d in plan['degrees']:
        fresh=d-1;n=4+fresh
        old_spaces=[gf2.basis(products(observations(mask,0),d,4)) for mask in range(64)]
        spaces=[];certificate_counts=[]
        for mask in range(64):
            features=list(products(observations(mask,fresh),d,n))
            spaces.append(gf2.basis(features))
            # A second route to non-membership: every feature's extracted
            # coefficient lies in the old linear space (not merely B_d).
            for v in features:
                assert gf2.contains(linear[mask],coefficient(v,fresh))
            certificate_counts.append(len(features))
        positive=negative=old_positive=eligible_negative=0
        witnesses=[]
        for p in range(64):
            for q in range(64):
                included=subset(linear[p],linear[q])
                assert included == ((p&~q)==0)
                actual=subset(spaces[p],spaces[q])
                assert actual==included
                if subset(old_spaces[p],old_spaces[q]):
                    old_positive+=1
                if included:
                    positive+=1
                else:
                    negative+=1
                    j=((p&~q)&-(p&~q)).bit_length()-1
                    f=table(4,PAIRS[j])
                    target=table(n,list(PAIRS[j])+list(range(4,n)))
                    assert gf2.contains(spaces[p],target)
                    assert not gf2.contains(spaces[q],target)
                    assert coefficient(target,fresh)==f
                    assert not gf2.contains(linear[q],f)
                    cost_eligible=p.bit_count()<=q.bit_count()
                    eligible_negative+=int(cost_eligible)
                    witnesses.append({'p':p,'q':q,'observed_pair':PAIRS[j],'f':f,'target':target,
                                      'fresh_inputs':fresh,'cost_eligible':cost_eligible})
        assert positive+negative==4096
        payload={'degree':d,'old_domain_rows':16,'extended_domain_rows':1<<n,
                 'old_inclusions':old_positive,'extended_inclusions':positive,'separations':negative,
                 'cost_eligible_separations':eligible_negative,
                 'feature_coefficient_checks':sum(certificate_counts),
                 'old_ranks':[len(x) for x in old_spaces],'extended_ranks':[len(x) for x in spaces],
                 'witnesses':witnesses}
        (out/f'degree-{d}.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
        total_certificates+=sum(certificate_counts)
        reports.append({k:v for k,v in payload.items() if k not in ['witnesses','old_ranks','extended_ranks']})
    files=[HERE/'protocol.json',HERE/'check.py',HELPER]+sorted(out.glob('degree-*.json'))
    report={'python':platform.python_version(),'profiles':64,'ordered_comparisons':64*64*len(plan['degrees']),
            'feature_coefficient_checks':total_certificates,'results':reports,
            'hashes':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='hashes'},indent=2))


if __name__=='__main__':
    main()
