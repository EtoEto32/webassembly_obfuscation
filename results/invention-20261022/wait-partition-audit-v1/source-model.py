"""Finite sanity checks, not a proof for all 32-bit programs."""
import itertools,json

def check():
    cases=0;counts={}
    # All permutations of two 1-bit fields, checking factorization of each projection.
    states=list(itertools.product(range(2),repeat=2))
    for family in ([],[{0}],[{1}],[{0},{1}],[{0,1}]):
        valid=0
        for permutation in itertools.permutations(states):
            ok=True
            for s in family:
                projection={}
                for x,y in zip(states,permutation):
                    a=tuple(x[i] for i in sorted(s));b=tuple(y[i] for i in sorted(s))
                    if a in projection and projection[a]!=b:ok=False
                    projection[a]=b;cases+=1
                if len(set(projection.values()))!=len(projection):ok=False
            valid+=ok
        counts[str([sorted(s) for s in family])]=valid
    assert list(counts.values())==[24,8,8,4,24]
    # Wait placement: before update => first notify must wake it, afterwards => mismatch.
    possible=[dict(wait='before',first_notify=1,second_notify=0,result=0),
              dict(wait='after',first_notify=0,second_notify=0,result=1)]
    bad=dict(first_notify=0,second_notify=1,result=0)
    assert not any(all(x[k]==v for k,v in bad.items()) for x in possible)
    return dict(projection_checks=cases,admissible_permutations=counts,original_histories=possible,bad_history=bad)

if __name__=='__main__':print(json.dumps(check(),indent=2))
