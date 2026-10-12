"""K1 candidate rejection test. Benign mathematical model, not a Wasm tool."""
import itertools, json, os, platform, random, sys, time
from pathlib import Path
sys.path.insert(0, os.environ.get('WASM_SYNTH_DEPENDENCIES', r'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\encoding-synthesis-python'))
import z3
ROOT = Path(__file__).resolve().parent
MASK = (1 << 32) - 1
SEED = 0x4b31494e

def rot(x):
    return ((x << 5) | (x >> 27)) & MASK

def mine(samples):
    # Decoder receives anonymous columns only, not c,d or generation logs.
    return [(k2,k1,k0) for k2,k1,k0 in itertools.product(range(-8,9), range(-8,9), range(-16,17))
            if all((b + k2*a*a + k1*a + k0) & MASK == 0 for a,b in samples)]

def prove(label, formula):
    s = z3.SolverFor('QF_BV'); s.set(timeout=3000, random_seed=SEED)
    s.add(formula)
    start=time.perf_counter(); verdict=s.check()
    row={'label':label, 'result':str(verdict), 'seconds':time.perf_counter()-start}
    if verdict == z3.unknown: row['reason']=s.reason_unknown()
    return row

def main():
    rng=random.Random(SEED); rows=[]
    for c,d in [(1,0),(3,7),(5,11)]:
        training=[]
        for _ in range(16):
            a=rng.getrandbits(32); training.append([a,(a*a+c*a+d)&MASK])
        hypotheses=mine(training)
        assert len(hypotheses)==1, hypotheses
        k2,k1,k0=hypotheses[0]
        a,b,u=z3.BitVecs('a b u',32)
        recovered_b=-(k2*a*a+k1*a+k0)
        original=(a^u)+a*u
        invariant=b-a*a-c*a-d
        transformed=original+((a^u)|1)*invariant
        # Exact substitution of a recovered state relation, then ring normalization.
        difference=z3.simplify(z3.substitute(transformed-original,(b,recovered_b)),som=True)
        proofs=[prove('recovered-relation-eliminates-inserted-term',difference!=0),
                prove('entry-establishes-recovered-relation',z3.simplify(a*a+c*a+d+k2*a*a+k1*a+k0,som=True)!=0)]
        nxt=z3.RotateLeft(a,5)^u
        proofs.append(prove('update-preserves-recovered-relation',z3.simplify(nxt*nxt+c*nxt+d+k2*nxt*nxt+k1*nxt+k0,som=True)!=0))
        failures=0; records=[]
        for _ in range(128):
            av=rng.getrandbits(32)
            for step in range(32):
                uv=rng.getrandbits(32); bv=(av*av+c*av+d)&MASK
                expected=((av^uv)+av*uv)&MASK
                observed=(expected+((av^uv)|1)*(bv-av*av-c*av-d))&MASK
                ok=observed==expected and (bv+k2*av*av+k1*av+k0)&MASK==0
                failures+=not ok
                records.append([av,bv,uv,expected,observed])
                av=rot(av)^uv
        # Explicit off-invariant witness: odd multiplier, relation differs by one.
        invalid_a=0; invalid_u=0; invalid_b=(d+1)&MASK
        local_expected=0; local_observed=(invalid_b-d)&MASK
        rows.append({'c':c,'d':d,'training':training,'mined_relations':hypotheses,
                     'proofs':proofs,'heldout_checks':len(records),'failures':failures,
                     'heldout_states':records,
                     'off_invariant_counterexample':{'a':invalid_a,'b':invalid_b,'u':invalid_u,'original':local_expected,'transformed':local_observed}})
    report={'seed':SEED,'python':platform.python_version(),'z3':z3.get_version_string(),'width':32,
            'model':'pure i32 arithmetic; instrumented state columns; no binary lifting', 'cases':rows}
    (ROOT/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'cases':len(rows),'heldout_checks':sum(r['heldout_checks'] for r in rows),
                      'failures':sum(r['failures'] for r in rows),'proof_results':[p['result'] for r in rows for p in r['proofs']]}))
    assert all(r['failures']==0 and all(p['result']=='unsat' for p in r['proofs']) for r in rows)

if __name__=='__main__': main()
